"""Real SQL catalog reads; institutional inputs here are isolated synthetic fixtures."""

from dataclasses import replace
from uuid import UUID, uuid4

import psycopg
import pytest
from business_app.contracts import validate_response
from business_app.permissions.object_facts import digest
from business_app.permissions.rule_types import ConditionFacts
from business_app.types import Actor, Scope
from sqlalchemy import event

from tests.business.t014_positive_fixtures import candidate
from tests.business.test_controls import AUTH
from tests.business.test_controls import control_context as control_context
from tests.business.test_t014_permissions import permission_context as permission_context
from tests.business.test_t015_scope_sql import two_cases


@pytest.fixture
def catalog_context(control_context, permission_context):
    ctx = control_context
    configured, objects, authority, facts = candidate(ctx, permission_context, ["asset.read", "task.read"])
    return dict(ctx, configured=configured, object_facts=objects, conditions=authority, facts=facts)


def request(ctx, path, **query):
    return ctx["control_http"].get(path, params=query, headers=AUTH)


def test_asset_detail_is_actual_metadata_and_fixed_object_version(catalog_context):
    ctx = catalog_context
    response = request(ctx, f"/api/v1/assets/{ctx['asset_id']}")
    assert response.status_code == 200, response.json()
    value = response.json()
    validate_response("Asset", value)
    assert value["object_ref"] == ctx["input_ref"]
    assert value["asset_id"] == ctx["asset_id"] and value["case_id"] == str(ctx["case_id"])
    assert value["state"] == "VALID" and value["width"] == value["height"] == 8
    assert response.headers["ETag"] and response.headers["Cache-Control"] == "no-store"
    assert not {"object_key", "bucket_alias", "path", "download_url"} & value.keys()


def test_asset_list_reads_current_authorized_database_rows(catalog_context):
    ctx = catalog_context
    response = request(ctx, "/api/v1/assets", case_id=str(ctx["case_id"]))
    assert response.status_code == 200, response.json()
    validate_response("AssetPage", response.json())
    assert [row["asset_id"] for row in response.json()["items"]] == [ctx["asset_id"]]


def test_task_list_includes_current_task_without_result(catalog_context):
    ctx = catalog_context
    task = uuid4()
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            "INSERT INTO mt.analysis_task(task_id,org_id,case_id,asset_id,scene,priority,state,policy_version,modules,report_eligibility,created_by) VALUES(%s,%s,%s,%s,'synthetic-only','normal','QUEUED','policy-dev-1',ARRAY[]::text[],'draft_only',%s)",
            (task, ctx["actor"].org_id, ctx["case_id"], ctx["asset_id"], ctx["actor"].user_id),
        )
        assert admin.execute("SELECT count(*) FROM mt.task_result WHERE task_id=%s", (task,)).fetchone() == (0,)
    response = request(ctx, "/api/v1/analysis/tasks", case_id=str(ctx["case_id"]))
    assert response.status_code == 200, response.json()
    validate_response("TaskPage", response.json())
    actual = next(row for row in response.json()["items"] if row["task_id"] == str(task))
    assert actual["state"] == "QUEUED" and actual["progress"] == 0
    assert actual["nodes"] == [] and actual["report_eligibility"] == "draft_only"


def clone_asset(ctx, identifier, digest=None):
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            "INSERT INTO mt.media_asset(asset_id,org_id,case_id,content_id,source_id,object_id,sha256,mime,size_bytes,duration_ms,width,height,kind,mapping_version,state,created_by) SELECT %s,org_id,case_id,content_id,source_id,object_id,coalesce(%s,sha256),mime,size_bytes,duration_ms,width,height,kind,mapping_version,state,created_by FROM mt.media_asset WHERE asset_id=%s",
            (identifier, digest, ctx["asset_id"]),
        )


@pytest.mark.parametrize("path", ["/api/v1/assets", "/api/v1/analysis/tasks"])
@pytest.mark.parametrize("defect", ["missing", "duplicate", "duplicate_foreign", "unknown", "invalid", "foreign_case"])
def test_lists_reject_ambiguous_or_untrusted_case_scope(catalog_context, path, defect):
    ctx = catalog_context
    query = [("case_id", str(ctx["case_id"]))]
    if defect == "missing":
        query = []
    elif defect == "duplicate":
        query += query
    elif defect == "duplicate_foreign":
        query += [("case_id", str(ctx["other_case_id"]))]
    elif defect == "unknown":
        query += [("extra", "untrusted")]
    elif defect == "invalid":
        query = [("case_id", "not-a-uuid")]
    else:
        query = [("case_id", str(ctx["other_case_id"]))]
    response = ctx["control_http"].get(path, params=query, headers=AUTH)
    assert response.status_code == (404 if defect == "foreign_case" else 422), response.json()
    assert not {"items", "next_cursor", "total"} & response.json().keys()


def test_asset_visibility_precedes_pagination_and_denied_ids_do_not_bind_cursor(catalog_context):
    ctx = catalog_context
    identifiers = [UUID(int=1), UUID(int=2), UUID(int=3)]
    for identifier in identifiers:
        clone_asset(ctx, identifier)
    ctx["facts"].blocked = {identifiers[0], UUID(ctx["asset_id"])}
    query = dict(case_id=str(ctx["case_id"]), limit=1)
    first = request(ctx, "/api/v1/assets", **query)
    assert first.status_code == 200, first.json()
    assert [v["asset_id"] for v in first.json()["items"]] == [str(identifiers[1])]
    cursor = first.json()["next_cursor"]
    assert cursor is not None
    # A denied row changing is not a visible result or cursor/count change.
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute("UPDATE mt.media_asset SET row_version=row_version+1 WHERE asset_id=%s", (identifiers[0],))
    second = request(ctx, "/api/v1/assets", **dict(query, cursor=cursor))
    assert second.status_code == 200, second.json()
    assert [v["asset_id"] for v in second.json()["items"]] == [str(identifiers[2])]
    assert second.json()["next_cursor"] is None


@pytest.mark.parametrize("defect", ["encoding", "signature", "operation", "limit"])
def test_catalog_cursor_rejects_noncanonical_or_cross_binding_replay(catalog_context, defect):
    ctx = catalog_context
    clone_asset(ctx, UUID(int=1))
    query = dict(case_id=str(ctx["case_id"]), limit=1)
    first = request(ctx, "/api/v1/assets", **query)
    assert first.status_code == 200, first.json()
    cursor = first.json()["next_cursor"]
    assert cursor is not None
    path = "/api/v1/assets"
    if defect == "encoding":
        cursor += "="
    elif defect == "signature":
        cursor = ("A" if cursor[0] != "A" else "B") + cursor[1:]
    elif defect == "operation":
        path = "/api/v1/analysis/tasks"
    else:
        query["limit"] = 2
    response = request(ctx, path, **dict(query, cursor=cursor))
    assert response.status_code == 422, response.json()
    assert "items" not in response.json()


@pytest.mark.parametrize("path", ["/api/v1/assets", "/api/v1/analysis/tasks"])
def test_all_denied_rows_produce_authorized_empty_page(catalog_context, path):
    ctx = catalog_context
    ctx["facts"].blocked = {UUID(ctx["asset_id"]), ctx["task_id"]}
    response = request(ctx, path, case_id=str(ctx["case_id"]))
    assert response.status_code == 200, response.json()
    assert response.json() == {"items": [], "next_cursor": None}


@pytest.mark.parametrize("target", ["asset", "assets", "tasks"])
def test_missing_identity_is_401_and_missing_formal_conditions_are_503(catalog_context, target):
    ctx = catalog_context
    path = {
        "asset": f"/api/v1/assets/{ctx['asset_id']}",
        "assets": "/api/v1/assets",
        "tasks": "/api/v1/analysis/tasks",
    }[target]
    query = {} if target == "asset" else dict(case_id=str(ctx["case_id"]))
    assert ctx["control_http"].get(path, params=query).status_code == 401
    ctx["object_facts"].supplemental = None
    assert request(ctx, path, **query).status_code == 503


@pytest.mark.parametrize("target", ["asset", "assets", "tasks"])
def test_revoked_source_is_not_exposed(catalog_context, target):
    ctx = catalog_context
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            "UPDATE mt.source_registry SET authorization_status='revoked',row_version=row_version+1 WHERE source_id=%s",
            (ctx["source_id"],),
        )
    path = {
        "asset": f"/api/v1/assets/{ctx['asset_id']}",
        "assets": "/api/v1/assets",
        "tasks": "/api/v1/analysis/tasks",
    }[target]
    response = request(ctx, path, **({} if target == "asset" else dict(case_id=str(ctx["case_id"]))))
    if target == "asset":
        assert response.status_code == 403, response.json()
    else:
        assert response.status_code == 200 and response.json() == {"items": [], "next_cursor": None}


def test_asset_detail_rejects_mismatched_registered_object_digest(catalog_context):
    ctx = catalog_context
    mismatched = uuid4()
    clone_asset(ctx, mismatched, "0" * 64)
    response = request(ctx, f"/api/v1/assets/{mismatched}")
    assert response.status_code == 503, response.json()
    assert "object_ref" not in response.json()


def test_asset_permission_change_after_data_read_is_refused_before_commit(catalog_context):
    ctx = catalog_context
    engine = ctx["control_app"].state.business_database.engine

    def revoke(connection, cursor, statement, parameters, context, executemany):
        if "catalog_asset_projection" in statement:
            ctx["facts"].blocked.add(UUID(ctx["asset_id"]))

    event.listen(engine, "after_cursor_execute", revoke)
    try:
        response = request(ctx, "/api/v1/assets", case_id=str(ctx["case_id"]))
    finally:
        event.remove(engine, "after_cursor_execute", revoke)
    assert response.status_code == 503, response.json()
    assert "items" not in response.json()


@pytest.mark.parametrize("path", ["/api/v1/assets", "/api/v1/analysis/tasks"])
def test_unknown_per_item_classification_fails_the_entire_list(catalog_context, path):
    ctx = catalog_context
    original = ctx["facts"]

    class UnknownClassification:
        def read(self, principal, operation_id, target, *, connection):
            facts = original.read(principal, operation_id, target, connection=connection)
            return replace(facts, checks=dict(facts.checks, classification=None)) if target.kind != "case" else facts

    ctx["object_facts"].supplemental = UnknownClassification()
    response = request(ctx, path, case_id=str(ctx["case_id"]))
    assert response.status_code == 503 and "items" not in response.json()


def test_asset_in_another_organization_is_not_found(catalog_context):
    ctx = catalog_context
    foreign, _ = two_cases(dict(ctx, actor=ctx["other_actor"], case_id=ctx["other_case_id"]))
    response = request(ctx, f"/api/v1/assets/{foreign['asset']}")
    assert response.status_code == 404 and "object_ref" not in response.json()


@pytest.mark.parametrize("path", ["/api/v1/assets", "/api/v1/analysis/tasks"])
def test_role_revocation_prevents_catalog_reads(catalog_context, path):
    ctx = catalog_context
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            "UPDATE mt.user_roles SET revoked_at=now(),row_version=row_version+1 WHERE user_id=%s AND revoked_at IS NULL",
            (ctx["actor"].user_id,),
        )
    response = request(ctx, path, case_id=str(ctx["case_id"]))
    assert response.status_code == 403 and "items" not in response.json()


def test_task_nodes_use_current_run_and_latest_attempt(catalog_context):
    ctx = catalog_context
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            "INSERT INTO mt.task_run(task_run_id,org_id,case_id,task_id,run_version,input_sha256,dag_version,policy_version) VALUES(%s,%s,%s,%s,2,%s,'synthetic-only','policy-dev-1')",
            (uuid4(), ctx["actor"].org_id, ctx["case_id"], ctx["task_id"], "a" * 64),
        )
        for run, attempt, state in [(1, 1, "FAILED"), (1, 2, "READY"), (2, 1, "SUCCEEDED")]:
            admin.execute(
                "INSERT INTO mt.task_node_run(run_id,org_id,case_id,task_id,run_version,node_code,attempt,input_hash,state,required,fencing_epoch) VALUES(%s,%s,%s,%s,%s,'synthetic-node',%s,%s,%s,true,1)",
                (uuid4(), ctx["actor"].org_id, ctx["case_id"], ctx["task_id"], run, attempt, "a" * 64, state),
            )
    response = request(ctx, "/api/v1/analysis/tasks", case_id=str(ctx["case_id"]))
    assert response.status_code == 200, response.json()
    task = next(row for row in response.json()["items"] if row["task_id"] == str(ctx["task_id"]))
    assert task["run_version"] == 1
    assert task["nodes"] == [dict(node_code="synthetic-node", state="READY", attempt=2, reason=None, required=True)]


def test_task_permission_change_after_projection_is_refused_before_commit(catalog_context):
    ctx = catalog_context
    engine = ctx["control_app"].state.business_database.engine

    def revoke(connection, cursor, statement, parameters, context, executemany):
        if "SELECT node_code,state,attempt,reason,required" in statement:
            ctx["facts"].blocked.add(ctx["task_id"])

    event.listen(engine, "after_cursor_execute", revoke)
    try:
        response = request(ctx, "/api/v1/analysis/tasks", case_id=str(ctx["case_id"]))
    finally:
        event.remove(engine, "after_cursor_execute", revoke)
    assert response.status_code == 503 and "items" not in response.json()


@pytest.mark.parametrize("defect", ["user", "case"])
def test_cursor_cannot_cross_otherwise_authorized_identity_or_case(catalog_context, defect):
    import time

    ctx = catalog_context
    actor = ctx["actor"]
    selected = [ctx["configured"]["principal"]]
    cases = {ctx["case_id"]}
    clone_asset(ctx, UUID(int=1))
    if defect == "case":
        _, second = two_cases(ctx)
        cases.add(second["case"])
    else:
        second_actor = Actor(uuid4(), actor.org_id)
        subject = "synthetic-catalog-" + uuid4().hex
        with psycopg.connect(ctx["admin_dsn"]) as admin:
            admin.execute(
                "INSERT INTO mt.users(user_id,org_id,subject,enabled) VALUES(%s,%s,%s,true)",
                (second_actor.user_id, actor.org_id, subject),
            )
            admin.execute(
                "INSERT INTO mt.user_identities(identity_id,user_id,org_id,issuer,subject,mapping_version,enabled) VALUES(%s,%s,%s,%s,%s,'synthetic-catalog/1',true)",
                (uuid4(), second_actor.user_id, actor.org_id, selected[0].issuer, subject),
            )
            admin.execute(
                "INSERT INTO mt.user_roles(user_role_id,user_id,role_id) SELECT %s,%s,role_id FROM mt.roles WHERE code='case_investigator'",
                (uuid4(), second_actor.user_id),
            )
            admin.execute(
                "INSERT INTO mt.case_membership(membership_id,case_id,org_id,user_id) VALUES(%s,%s,%s,%s)",
                (uuid4(), ctx["case_id"], actor.org_id, second_actor.user_id),
            )

    class Identities:
        def authenticate_principal(self, token):
            assert token == "test-only-valid-token"
            return selected[0]

        def authorize_case(self, current, case_id, action):
            assert current == selected[0].actor and case_id in cases
            return Scope(current, case_id)

    class Facts:
        def read(self, principal, operation_id, target, *, connection):
            assert principal == selected[0] and target.org_id == actor.org_id and target.case_id in cases
            checks = dict(classification=True, read_purpose=True)
            return ConditionFacts(principal, target, checks, digest([operation_id, target, checks]), time.time() + 60)

    ctx["control_app"].state.business_authority = Identities()
    ctx["object_facts"].supplemental = Facts()
    query = dict(case_id=str(ctx["case_id"]), limit=1)
    first = request(ctx, "/api/v1/assets", **query)
    assert first.status_code == 200 and first.json()["next_cursor"] is not None
    if defect == "user":
        selected[0] = replace(selected[0], actor=second_actor, subject=subject)
    else:
        query["case_id"] = str(second["case"])
    # Both scopes are actually authorized. The rejection is cursor binding.
    valid = request(ctx, "/api/v1/assets", **query)
    assert valid.status_code == 200, valid.json()
    denied = request(ctx, "/api/v1/assets", **dict(query, cursor=first.json()["next_cursor"]))
    assert denied.status_code == 422 and "items" not in denied.json()
