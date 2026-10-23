"""Real SQL scope tests with explicit synthetic evidence, never formal identity proof."""

import importlib
import importlib.util
import time
from contextlib import contextmanager
from uuid import uuid4

import psycopg
import pytest
from business_app.errors import BusinessError
from business_app.permissions.context import request_authorization
from business_app.permissions.object_facts import ObjectFactsReader
from business_app.permissions.rule_types import AuthorizationEvidence, ExecutionSubject, RuleTarget
from business_app.permissions.types import Principal
from business_app.types import Scope
from psycopg import sql
from sqlalchemy import event, text
from sqlalchemy.exc import DBAPIError

from tests.business.http_fixtures import FixtureFence


def two_cases(context):
    """The same real directory user has BOTH cases; a missing WHERE must still fail closed."""
    actor = context["actor"]
    second = uuid4()
    records = []
    with psycopg.connect(context["admin_dsn"]) as admin:
        admin.execute(
            "INSERT INTO mt.cases(case_id,org_id,display_code,status) VALUES(%s,%s,%s,'ACTIVE')",
            (second, actor.org_id, str(second)),
        )
        admin.execute(
            "INSERT INTO mt.case_membership(membership_id,case_id,org_id,user_id) VALUES(%s,%s,%s,%s)",
            (uuid4(), second, actor.org_id, actor.user_id),
        )
        for case in (context["case_id"], second):
            source, content, obj, asset, task = [uuid4() for _ in range(5)]
            admin.execute(
                "INSERT INTO mt.source_registry(source_id,org_id,case_id,name,source_type,authorization_ref,purpose,authorization_status,authorization_version) VALUES(%s,%s,%s,'synthetic','synthetic','self-owned-test',ARRAY['analysis'],'verified','fixture-v1')",
                (source, actor.org_id, case),
            )
            admin.execute(
                "INSERT INTO mt.content_item(content_id,org_id,case_id,source_id,discovered_at,status) VALUES(%s,%s,%s,%s,now(),'synthetic')",
                (content, actor.org_id, case, source),
            )
            admin.execute(
                "INSERT INTO mt.object_version(object_id,org_id,case_id,bucket_alias,object_key,version_id,sha256,size_bytes) VALUES(%s,%s,%s,'synthetic',%s,'fixture-v1',%s,1)",
                (obj, actor.org_id, case, str(obj), "a" * 64),
            )
            admin.execute(
                "INSERT INTO mt.media_asset(asset_id,org_id,case_id,content_id,source_id,object_id,sha256,mime,size_bytes,kind,mapping_version,state) VALUES(%s,%s,%s,%s,%s,%s,%s,'image/png',1,'original','fixture-v1','VALID')",
                (asset, actor.org_id, case, content, source, obj, "a" * 64),
            )
            admin.execute(
                "INSERT INTO mt.analysis_task(task_id,org_id,case_id,asset_id,scene,priority,state,policy_version,modules,report_eligibility,created_by) VALUES(%s,%s,%s,%s,'synthetic','normal','CREATED','fixture-v1',ARRAY[]::text[],'draft_only',%s)",
                (task, actor.org_id, case, asset, actor.user_id),
            )
            records.append(dict(case=case, source=source, asset=asset, task=task))
    return records


def principal(context):
    return Principal(context["actor"], "https://identity.example.test", "synthetic-scope-user", int(time.time()) + 300)


@contextmanager
def case_evidence(context, case):
    actor = context["actor"]
    proof = AuthorizationEvidence(
        principal(context),
        "listSources",
        RuleTarget(actor.org_id, "case", case, None, case, None, None),
        "a" * 64,
        "b" * 64,
        "explicit-synthetic-fixture",
        "synthetic-scope-only",
        time.time() + 300,
    )
    with request_authorization(proof, FixtureFence(frozenset({actor})), mutation=True):
        yield proof


def test_case_query_without_case_filter_does_not_return_another_valid_membership(business_context):
    first, _ = two_cases(business_context)
    with case_evidence(business_context, first["case"]):
        with business_context["database"].transaction(Scope(business_context["actor"], first["case"])) as connection:
            actual = connection.execute(text("SELECT task_id FROM mt.analysis_task")).scalars().all()
    assert actual == [first["task"]]


def test_related_join_is_limited_to_the_fixed_case_even_without_where(business_context):
    first, _ = two_cases(business_context)
    with case_evidence(business_context, first["case"]):
        with business_context["database"].transaction(Scope(business_context["actor"], first["case"])) as connection:
            values = (
                connection.execute(
                    text("SELECT t.task_id FROM mt.analysis_task t JOIN mt.media_asset a ON a.asset_id=t.asset_id")
                )
                .scalars()
                .all()
            )
    assert values == [first["task"]]


def test_cross_case_update_is_not_allowed_by_other_valid_membership(business_context):
    first, second = two_cases(business_context)
    with case_evidence(business_context, first["case"]):
        with business_context["database"].transaction(Scope(business_context["actor"], first["case"])) as connection:
            changed = connection.execute(
                text("UPDATE mt.analysis_task SET priority='high' WHERE task_id=:id"), {"id": second["task"]}
            )
            assert changed.rowcount == 0


def test_cross_case_insert_is_rejected_before_it_can_commit(business_context):
    first, second = two_cases(business_context)
    actor = business_context["actor"]
    with case_evidence(business_context, first["case"]):
        with business_context["database"].transaction(Scope(actor, first["case"])) as connection:
            with pytest.raises(DBAPIError):
                with connection.begin_nested():
                    connection.execute(
                        text(
                            "INSERT INTO mt.analysis_task(task_id,org_id,case_id,asset_id,scene,priority,state,policy_version,modules,report_eligibility) VALUES(:id,:org,:case,:asset,'synthetic','normal','CREATED','fixture-v1',ARRAY[]::text[],'draft_only')"
                        ),
                        dict(id=uuid4(), org=actor.org_id, case=second["case"], asset=second["asset"]),
                    )


def test_scope_argument_cannot_switch_the_authorized_case(business_context):
    first, second = two_cases(business_context)
    with case_evidence(business_context, first["case"]):
        with pytest.raises(BusinessError) as caught:
            with business_context["database"].transaction(Scope(business_context["actor"], second["case"])):
                pytest.fail("CASE_BOUND_EVIDENCE_WAS_REPLACED")
    assert (caught.value.code, caught.value.http_status) == ("AUTHORITY_SCOPE_INVALID", 503)


def test_forged_scope_without_evidence_cannot_open_business_transaction(business_context):
    with pytest.raises(BusinessError) as caught:
        with business_context["database"].transaction(Scope(business_context["actor"], business_context["case_id"])):
            pytest.fail("DATA_SCOPE_IS_NOT_AUTHENTICATION")
    assert caught.value.http_status == 503


def test_organization_mode_cannot_read_case_payload(business_context):
    two_cases(business_context)
    proof = AuthorizationEvidence(
        principal(business_context),
        "getPolicy",
        RuleTarget(business_context["actor"].org_id, "policy", uuid4(), 1, None, None, "retention"),
        "a" * 64,
        "b" * 64,
        "explicit-synthetic-fixture",
        "synthetic-scope-only",
        time.time() + 300,
    )
    with request_authorization(proof, business_context["authorization_fence"], mutation=False):
        with business_context["database"].identity_transaction(business_context["actor"]) as connection:
            assert connection.execute(text("SELECT task_id FROM mt.analysis_task")).scalars().all() == []


def test_lookup_is_readonly_exact_target_and_has_no_payload(business_context):
    first, _ = two_cases(business_context)
    name = "business_app.scope_lookup"
    assert importlib.util.find_spec(name) is not None, "READONLY_EXACT_METADATA_PORT_REQUIRED"
    from business_app.data_scope import LookupKey

    reads = []

    def inspect(connection, cursor, statement, parameters, context, executemany):
        if "mt.lookup_scope_metadata(" in statement:
            reads.append(connection.exec_driver_sql("SHOW transaction_read_only").scalar_one())
            assert connection.execute(text("SELECT task_id FROM mt.analysis_task")).scalars().all() == []

    engine = business_context["database"].engine
    event.listen(engine, "before_cursor_execute", inspect)
    try:
        result = (
            importlib.import_module(name)
            .SqlScopeLookup(business_context["database"])
            .read(principal(business_context), "getTask", LookupKey("task", first["task"]))
        )
    finally:
        event.remove(engine, "before_cursor_execute", inspect)
    assert reads and set(reads) == {"on"}
    assert result.target.case_id == first["case"] and result.target.object_id == first["task"]
    assert not {"content", "details", "snapshot", "claim_text", "artifact_ref"} & set(result.projection)


def test_pre_authorization_metadata_needs_no_prior_evidence_or_share_lock(business_context):
    first, _ = two_cases(business_context)
    locking = []

    def inspect(connection, cursor, statement, parameters, context, executemany):
        if "FOR SHARE" in statement.upper() or "FOR UPDATE" in statement.upper():
            locking.append(statement)

    engine = business_context["database"].engine
    event.listen(engine, "before_cursor_execute", inspect)
    try:
        reader = ObjectFactsReader(business_context["database"])
        target = reader.resolve_http(principal(business_context), "getTask", {"id": first["task"]}, {}, {})
        facts = reader.read(principal(business_context), "getTask", target)
    finally:
        event.remove(engine, "before_cursor_execute", inspect)
    assert facts.checks["case"] is True and facts.checks["source"] is True
    assert locking == [], "AUTHORIZATION_BEFORE_EVIDENCE_MUST_USE_READONLY_METADATA"


def test_lookup_self_identity_never_becomes_an_arbitrary_user_directory(business_context):
    name = "business_app.scope_lookup"
    assert importlib.util.find_spec(name) is not None, "SELF_ONLY_METADATA_LOOKUP_REQUIRED"
    from business_app.data_scope import LookupKey

    other = uuid4()
    actor = business_context["actor"]
    with psycopg.connect(business_context["admin_dsn"]) as admin:
        admin.execute(
            "INSERT INTO mt.users(user_id,org_id,subject,enabled) VALUES(%s,%s,%s,true)",
            (other, actor.org_id, str(other)),
        )
    port = importlib.import_module(name).SqlScopeLookup(business_context["database"])
    own = port.read(principal(business_context), "getCurrentUser", LookupKey("user", actor.user_id))
    assert own.projection["user_id"] == str(actor.user_id)
    assert not {"subject", "password", "credentials"} & set(own.projection)
    with pytest.raises(BusinessError) as caught:
        port.read(principal(business_context), "getCurrentUser", LookupKey("user", other))
    assert caught.value.http_status == 404


def test_metadata_work_subject_requires_a_real_configured_trust_port(business_context):
    name = "business_app.scope_lookup"
    assert importlib.util.find_spec(name) is not None, "WORK_METADATA_TRUST_CHECK_REQUIRED"
    from business_app.data_scope import LookupKey

    upload = uuid4()
    subject = ExecutionSubject(business_context["actor"], uuid4(), "synthetic-map", "upload_validation", upload)
    with pytest.raises(BusinessError) as caught:
        importlib.import_module(name).SqlScopeLookup(business_context["database"]).read(
            subject, "validateUploadWork", LookupKey("upload", upload)
        )
    assert caught.value.http_status == 503


def test_current_actor_case_ids_does_not_open_raw_case_payload_or_other_unit(business_context):
    first, second = two_cases(business_context)
    actor = business_context["actor"]
    proof = AuthorizationEvidence(
        principal(business_context),
        "getCurrentUser",
        RuleTarget(actor.org_id, "user", actor.user_id, None, None, None, None),
        "a" * 64,
        "b" * 64,
        "explicit-synthetic-fixture",
        "synthetic-scope-only",
        time.time() + 300,
    )
    with request_authorization(proof, business_context["authorization_fence"], mutation=False):
        with business_context["database"].identity_transaction(actor) as connection:
            cases = connection.execute(text("SELECT case_id FROM mt.current_actor_case_ids()")).scalars().all()
            assert set(cases) == {first["case"], second["case"]}
            assert connection.execute(text("SELECT case_id FROM mt.cases")).scalars().all() == []
            assert connection.execute(text("SELECT case_id FROM mt.case_membership")).scalars().all() == []


def test_business_connection_cannot_inherit_the_directory_manager(business_context):
    database = business_context["database"]
    with database.engine.connect() as connection:
        login = connection.execute(text("SELECT current_user")).scalar_one()
    with psycopg.connect(business_context["admin_dsn"]) as admin:
        admin.execute(sql.SQL("GRANT mt_directory_manager TO {}").format(sql.Identifier(login)))
    with case_evidence(business_context, business_context["case_id"]):
        with pytest.raises(RuntimeError, match="PRIVILEGED"):
            with database.transaction(Scope(business_context["actor"], business_context["case_id"])):
                pytest.fail("DIRECTORY_MANAGER_MUST_NOT_BE_A_BUSINESS_RUNTIME")


def test_lookup_sql_rejects_kind_not_registered_for_the_operation(business_context):
    actor = business_context["actor"]
    with business_context["database"].engine.begin() as connection:
        connection.exec_driver_sql("SET TRANSACTION READ ONLY")
        for key, value in {
            "app.actor_id": str(actor.user_id),
            "app.org_id": str(actor.org_id),
            "app.scope_mode": "LOOKUP",
            "app.operation_id": "getCurrentUser",
            "app.lookup_kind": "source",
            "app.lookup_id": str(business_context["source_id"]),
        }.items():
            connection.execute(text("SELECT set_config(:key,:value,true)"), dict(key=key, value=value))
        assert (
            connection.execute(
                text("SELECT mt.lookup_scope_metadata('source',:id)"), dict(id=business_context["source_id"])
            ).scalar_one()
            is None
        )


def test_lookup_cannot_open_a_business_transaction_on_its_occupied_pool(business_context):
    from business_app.data_scope import LookupKey
    from business_app.scope_lookup import SqlScopeLookup

    database = business_context["database"]
    with SqlScopeLookup(database).connection(
        principal(business_context), "getSource", LookupKey("source", business_context["source_id"])
    ):
        with pytest.raises(BusinessError) as caught:
            with database.transaction(Scope(business_context["actor"], business_context["case_id"])):
                pytest.fail("LOOKUP_MUST_NOT_UPGRADE_TO_BUSINESS_ACCESS")
        assert (caught.value.code, caught.value.http_status) == ("AUTHORITY_SCOPE_INVALID", 503)


def test_case_status_metadata_does_not_invent_a_membership_revocation(business_context):
    from business_app.data_scope import LookupKey
    from business_app.scope_lookup import SqlScopeLookup

    context = business_context
    with psycopg.connect(context["admin_dsn"]) as admin:
        admin.execute("UPDATE mt.cases SET status='ARCHIVED' WHERE case_id=%s", (context["case_id"],))
    result = SqlScopeLookup(context["database"]).read(
        principal(context), "getSource", LookupKey("source", context["source_id"])
    )
    assert result.target.case_id == context["case_id"]
    actor = context["actor"]
    proof = AuthorizationEvidence(
        principal(context),
        "getCurrentUser",
        RuleTarget(actor.org_id, "user", actor.user_id, None, None, None, None),
        "a" * 64,
        "b" * 64,
        "explicit-synthetic-fixture",
        "synthetic-only",
        time.time() + 60,
    )
    with request_authorization(proof, context["authorization_fence"], mutation=False):
        with context["database"].identity_transaction(actor) as connection:
            assert connection.execute(text("SELECT case_id FROM mt.current_actor_case_ids()")).scalars().all() == [
                context["case_id"]
            ]
            assert connection.execute(text("SELECT case_id FROM mt.cases")).scalars().all() == []


def test_sql_lookup_kind_operation_matrix_matches_the_fixed_python_catalog(business_context):
    from business_app.permissions.object_facts import SUPPORTED_OPERATIONS
    from business_app.permissions.work_subject import WORK_OPERATIONS
    from business_app.scope_catalog import LOOKUP_KINDS, lookup_spec

    kinds = sorted(LOOKUP_KINDS | {"unknown"})
    operations = sorted(SUPPORTED_OPERATIONS | WORK_OPERATIONS.keys() | {"unknown"})
    with business_context["database"].engine.begin() as connection:
        assert connection.execute(
            text("SELECT to_regprocedure('mt.scope_lookup_kind_allowed(text,text)') IS NOT NULL")
        ).scalar_one(), "SQL_SCOPE_CATALOG_AGREEMENT_REQUIRED"
        rows = connection.execute(
            text(
                "SELECT k,o,mt.scope_lookup_kind_allowed(k,o) FROM unnest(CAST(:kinds AS text[])) k CROSS JOIN unnest(CAST(:operations AS text[])) o"
            ),
            dict(kinds=kinds, operations=operations),
        ).all()
    assert len(rows) == len(kinds) * len(operations)
    for kind, operation, allowed in rows:
        assert allowed is (kind in LOOKUP_KINDS and operation in lookup_spec(kind).operation_ids)
