"""Actual SQL and HTTP report reads with explicit synthetic institutional facts."""

import time
from uuid import uuid4

import psycopg
import pytest
from business_app.contracts import validate_response
from business_app.errors import BusinessError
from business_app.permissions.object_facts import digest
from business_app.permissions.rule_types import ConditionFacts
from business_app.types import Scope
from sqlalchemy import event

from tests.business.scoped_history_fixtures import history_read_evidence
from tests.business.t014_positive_fixtures import candidate
from tests.business.test_controls import AUTH
from tests.business.test_controls import control_context as control_context
from tests.business.test_t014_permissions import permission_context as permission_context
from tests.business.test_t015_scope_sql import two_cases


@pytest.fixture
def report_context(request):
    ctx = request.getfixturevalue("control_context")
    permissions = request.getfixturevalue("permission_context")
    configured, objects, authority, facts = candidate(ctx, permissions, ["report.read"])
    identifier = uuid4()
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            "INSERT INTO mt.report(report_id,org_id,case_id,task_id,run_version,result_version,version,template_version,"
            "state,snapshot_sha256,created_by) VALUES(%s,%s,%s,%s,1,1,1,'synthetic-template/1','DRAFT',%s,%s)",
            (identifier, ctx["actor"].org_id, ctx["case_id"], ctx["task_id"], "a" * 64, ctx["actor"].user_id),
        )
        admin.execute(
            "INSERT INTO mt.report_evidence(link_id,org_id,case_id,report_id,evidence_id) VALUES(%s,%s,%s,%s,%s)",
            (uuid4(), ctx["actor"].org_id, ctx["case_id"], identifier, ctx["evidence_id"]),
        )
    return dict(
        ctx, report_id=identifier, configured=configured, object_facts=objects, conditions=authority, facts=facts
    )


def read(ctx, **kwargs):
    return ctx["control_http"].get(f"/api/v1/reports/{ctx['report_id']}", headers=AUTH, **kwargs)


def test_report_reads_actual_persisted_metadata_and_evidence(report_context):
    ctx = report_context
    response = read(ctx)
    assert response.status_code == 200, response.json()
    value = response.json()
    validate_response("Report", value)
    assert value["report_id"] == str(ctx["report_id"])
    assert value["evidence_ids"] == [str(ctx["evidence_id"])]
    assert value["task_id"] == str(ctx["task_id"])
    assert value["run_version"] == value["result_version"] == value["version"] == 1
    assert value["state"] == "DRAFT" and value["object_ref"] is None and value["approval_id"] is None
    assert response.headers["ETag"] and response.headers["Cache-Control"] == "no-store"


def test_report_reads_exact_registered_object_metadata(report_context):
    ctx = report_context
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            "UPDATE mt.report SET object_id=%s,state='READY',row_version=row_version+1 WHERE report_id=%s",
            (ctx["input_ref"]["object_id"], ctx["report_id"]),
        )
    response = read(ctx)
    assert response.status_code == 200, response.json()
    assert response.json()["object_ref"] == ctx["input_ref"]
    assert not {"bucket_alias", "object_key", "path", "download_url"} & response.json().keys()


def test_missing_report_is_not_found(report_context):
    ctx = dict(report_context, report_id=uuid4())
    response = read(ctx)
    assert response.status_code == 404 and "evidence_ids" not in response.json()


def test_report_rejects_missing_identity_and_unconfigured_formal_facts(report_context):
    ctx = report_context
    assert ctx["control_http"].get(f"/api/v1/reports/{ctx['report_id']}").status_code == 401
    ctx["object_facts"].supplemental = None
    response = read(ctx)
    assert response.status_code == 503 and "report_id" not in response.json()


def test_report_classification_denial_is_not_exposed(report_context):
    ctx = report_context
    ctx["facts"].blocked.add(ctx["report_id"])
    response = read(ctx)
    assert response.status_code == 403 and "report_id" not in response.json()


@pytest.mark.parametrize("defect", ["case_id", "history[run_version]", "unknown", "duplicate"])
def test_report_rejects_uncontracted_scope_and_history(report_context, defect):
    query = [("case_id", str(report_context["case_id"]))] if defect != "duplicate" else [("x", "1"), ("x", "2")]
    if defect not in {"case_id", "duplicate"}:
        query = [(defect, "1")]
    response = read(report_context, params=query)
    assert response.status_code == 422 and "report_id" not in response.json()


def test_revoked_primary_source_prevents_report_disclosure(report_context):
    ctx = report_context
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            "UPDATE mt.source_registry SET authorization_status='revoked',row_version=row_version+1 WHERE source_id=%s",
            (ctx["source_id"],),
        )
    response = read(ctx)
    assert response.status_code == 403 and "report_id" not in response.json()


def test_report_permission_change_after_projection_is_refused(report_context):
    ctx = report_context
    engine = ctx["control_app"].state.business_database.engine

    def deny(connection, cursor, statement, parameters, context, executemany):
        if "registry_report_projection" in statement:
            ctx["facts"].blocked.add(ctx["report_id"])

    event.listen(engine, "after_cursor_execute", deny)
    try:
        response = read(ctx)
    finally:
        event.remove(engine, "after_cursor_execute", deny)
    # The established fence propagates an explicit current classification denial
    # as PERMISSION_REQUIRED/403; unavailable facts are separately 503. Both are
    # checked before a response can disclose the report or its evidence.
    assert response.status_code == 403
    assert response.json()["code"] == "PERMISSION_REQUIRED"
    assert not {"report_id", "evidence_ids", "object_ref"} & response.json().keys()
    assert response.headers["Cache-Control"] == "no-store"


def test_report_refuses_ready_record_without_artifact(report_context):
    ctx = report_context
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            "UPDATE mt.report SET state='READY',row_version=row_version+1 WHERE report_id=%s", (ctx["report_id"],)
        )
    response = read(ctx)
    assert response.status_code == 503 and "report_id" not in response.json()


def test_report_checks_every_evidence_source_not_only_primary_asset(report_context):
    ctx = report_context
    secondary, _ = two_cases(ctx)
    evidence = uuid4()
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            "INSERT INTO mt.evidence_item(evidence_id,org_id,case_id,task_id,run_version,result_version,asset_id,"
            "type,sha256,captured_at,mapping_version,authorization_version,immutable_state) "
            "VALUES(%s,%s,%s,%s,1,1,%s,'synthetic-secondary-source',%s,now(),'fixture-v1','fixture-v1','RECORDED')",
            (evidence, ctx["actor"].org_id, ctx["case_id"], ctx["task_id"], secondary["asset"], "b" * 64),
        )
        admin.execute(
            "INSERT INTO mt.report_evidence(link_id,org_id,case_id,report_id,evidence_id) VALUES(%s,%s,%s,%s,%s)",
            (uuid4(), ctx["actor"].org_id, ctx["case_id"], ctx["report_id"], evidence),
        )
    valid = read(ctx)
    assert valid.status_code == 200, valid.json()
    assert set(valid.json()["evidence_ids"]) == {str(ctx["evidence_id"]), str(evidence)}
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            "UPDATE mt.source_registry SET authorization_status='revoked',row_version=row_version+1 WHERE source_id=%s",
            (secondary["source"],),
        )
    response = read(ctx)
    assert response.status_code == 403 and "evidence_ids" not in response.json()


def test_report_metadata_cannot_be_read_across_another_valid_case_membership(report_context):
    ctx = report_context
    _, foreign = two_cases(ctx)
    identifier = uuid4()
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        # Self-owned metadata fixtures only. No inference is run or reported successful.
        admin.execute(
            "INSERT INTO mt.task_run(task_run_id,org_id,case_id,task_id,run_version,input_sha256,dag_version,policy_version) "
            "VALUES(%s,%s,%s,%s,1,%s,'synthetic/1','fixture-v1')",
            (uuid4(), ctx["actor"].org_id, foreign["case"], foreign["task"], "a" * 64),
        )
        admin.execute(
            "INSERT INTO mt.task_result(result_id,org_id,case_id,task_id,run_version,result_version,sha256,policy_version) "
            "VALUES(%s,%s,%s,%s,1,1,%s,'fixture-v1')",
            (uuid4(), ctx["actor"].org_id, foreign["case"], foreign["task"], "a" * 64),
        )
        admin.execute(
            "INSERT INTO mt.report(report_id,org_id,case_id,task_id,run_version,result_version,version,template_version,"
            "state,snapshot_sha256,created_by) VALUES(%s,%s,%s,%s,1,1,1,'synthetic/1','DRAFT',%s,%s)",
            (identifier, ctx["actor"].org_id, foreign["case"], foreign["task"], "a" * 64, ctx["actor"].user_id),
        )
    original = ctx["object_facts"].supplemental

    class BothCasesInstitutionalFacts:
        def read(self, principal, operation_id, target, *, connection):
            if target.case_id == ctx["case_id"]:
                return original.read(principal, operation_id, target, connection=connection)
            checks = dict(classification=True, read_purpose=True)
            return ConditionFacts(principal, target, checks, digest([target, checks]), time.time() + 60)

    ctx["object_facts"].supplemental = BothCasesInstitutionalFacts()
    response = read(dict(ctx, report_id=identifier))
    assert response.status_code == 404 and "report_id" not in response.json()


def test_report_evidence_limit_is_explicit_development_refusal(report_context):
    ctx = report_context
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        with admin.cursor() as cursor:
            cursor.executemany(
                "INSERT INTO mt.report_evidence(link_id,org_id,case_id,report_id,evidence_id) VALUES(%s,%s,%s,%s,%s)",
                [
                    (uuid4(), ctx["actor"].org_id, ctx["case_id"], ctx["report_id"], ctx["evidence_id"])
                    for _ in range(1000)
                ],
            )
    response = read(ctx)
    assert response.status_code == 503 and "report_id" not in response.json()
    assert "REPORT_READ_DEVELOPMENT_LIMIT_EXCEEDED" in response.text


def test_report_without_any_evidence_is_not_fabricated_as_success(report_context):
    ctx = report_context
    identifier = uuid4()
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            "INSERT INTO mt.report(report_id,org_id,case_id,task_id,run_version,result_version,version,template_version,"
            "state,snapshot_sha256,created_by) VALUES(%s,%s,%s,%s,1,1,2,'synthetic/1','DRAFT',%s,%s)",
            (identifier, ctx["actor"].org_id, ctx["case_id"], ctx["task_id"], "a" * 64, ctx["actor"].user_id),
        )
    response = read(dict(ctx, report_id=identifier))
    assert response.status_code == 503 and "report_id" not in response.json()
    assert "REPORT_METADATA_BINDING_INVALID" in response.text


def test_report_repository_rejects_a_task_root_without_exact_report_authority(report_context):
    ctx = report_context
    scope = Scope(ctx["actor"], ctx["case_id"])
    database = ctx["control_app"].state.business_database
    with history_read_evidence(scope, "getTask", "task", ctx["task_id"]):
        with database.transaction(scope) as connection:
            with pytest.raises(BusinessError) as error:
                ctx["control_app"].state.registry_reads.report(connection, scope, ctx["report_id"])
    assert error.value.code == "AUTHORITY_SCOPE_INVALID"
