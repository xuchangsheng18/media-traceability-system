"""Real SQL/HTTP with explicitly synthetic policies; no formal consumer is mounted."""

import hashlib
import importlib
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from copy import copy
from dataclasses import replace
from datetime import datetime
from threading import Barrier, Event
from typing import Any
from uuid import UUID, uuid4

import psycopg
import pytest
from business_app.controls.providers import ApprovalRule, OperationTokenKey, OperationTokenRule
from business_app.db import Database
from business_app.errors import BusinessError
from business_app.main import create_app
from business_app.permissions.context import request_authorization
from business_app.permissions.rule_types import RuleTarget
from business_app.types import Scope
from fastapi import Request
from fastapi.testclient import TestClient
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from sqlalchemy import event, text

from tests.business.t014_positive_fixtures import candidate
from tests.business.test_controls import AUTH, approve, request_approval
from tests.business.test_controls import control_context as control_context
from tests.business.test_recovery import pg_tool
from tests.business.test_t014_permissions import permission_context as permission_context
from tests.business.test_t015_collections import synthetic_target
from tests.business.test_t015_scope_recovery import empty_scope_database


@pytest.fixture
def token_context(control_context):
    ctx = control_context
    module = importlib.import_module("business_app.controls.operation_tokens")
    assert hasattr(module, "OperationTokens"), "T016_CASE_ISSUANCE_AND_CONSUMPTION_REQUIRED"
    app = ctx["control_app"]
    old_rules = app.state.approvals.rules

    class Rules:
        def approval(self, scope, purpose, version):
            if purpose == "seal" and version == "policy-dev-1":
                return ApprovalRule(version, 1800, 2)
            return old_rules.approval(scope, purpose, version)

    class TokenRules:
        version = "self-owned-token-rule-1"
        ttl = 60

        def resolve(self, scope, approval):
            assert scope.case_id == ctx["case_id"]
            assert approval["object_type"] == "task" and approval["purpose"] == "seal"
            return OperationTokenRule("sealEvidence", self.version, self.ttl)

    class Keys:
        key = OperationTokenKey("self-owned-key-1", b"synthetic-t016-only-key-material!!")

        def current(self):
            return self.key

        def get(self, key_id):
            if key_id != self.key.key_id:
                raise BusinessError("OPERATION_TOKEN_UNAVAILABLE", 503)
            return self.key

    app.state.approvals.rules = Rules()
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute("UPDATE mt.analysis_task SET run_version=1,result_version=1 WHERE task_id=%s", (ctx["task_id"],))
    service = app.state.operation_tokens
    service.rules, service.keys = TokenRules(), Keys()
    identifier = request_approval(ctx, purpose="seal")
    approve(ctx, identifier)
    body = dict(approval_id=identifier, object_id=str(ctx["task_id"]), object_version=1, purpose="seal")
    return dict(ctx, token_service=service, token_body=body)


def issue(ctx, *, key="self-owned-token-request", body=None):
    return ctx["control_http"].post(
        "/api/v1/operation-tokens",
        json=ctx["token_body"] if body is None else body,
        headers=dict(AUTH, **{"Idempotency-Key": key}),
    )


def consume(ctx, credential, connection, **overrides):
    values = dict(
        approval_id=UUID(ctx["token_body"]["approval_id"]),
        action="sealEvidence",
        object_id=ctx["task_id"],
        object_version=1,
        request=Request({"type": "http", "headers": []}),
    )
    values.update(overrides)
    return ctx["token_service"].consume(connection, Scope(ctx["actor"], ctx["case_id"]), credential, **values)


def action_target(ctx):
    return RuleTarget(ctx["actor"].org_id, "task", ctx["task_id"], 1, ctx["case_id"], "seal", None)


@contextmanager
def action_root(ctx, operation, target, *, generation="explicit-synthetic-fixture"):
    from tests.business.http_fixtures import FixtureFence

    with synthetic_target(ctx, operation, target) as proof:
        with request_authorization(
            replace(proof, recovery_generation=generation), FixtureFence(frozenset({ctx["actor"]})), mutation=True
        ):
            yield proof


def test_issue_replay_is_same_credential_and_never_persists_plaintext(token_context):
    ctx = token_context
    first = issue(ctx)
    assert first.status_code == 200, first.json()
    second = issue(ctx)
    assert second.status_code == 200 and second.json() == first.json()
    credential = first.json()["operation_token"]
    assert first.json()["object_version"] == 1
    assert datetime.fromisoformat(first.json()["expires_at"]).timestamp() > time.time()
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        rows = admin.execute("SELECT token_sha256,to_jsonb(t)::text FROM mt.operation_token t").fetchall()
        assert len(rows) == 1 and rows[0][0] == hashlib.sha256(credential.encode()).hexdigest()
        assert credential not in rows[0][1]
        assert credential not in str(admin.execute("SELECT response_ref FROM mt.idempotency_record").fetchall())
        assert credential not in str(admin.execute("SELECT to_jsonb(t)::text FROM mt.audit_event t").fetchall())


def test_uuid_spelling_is_canonical_before_binding_and_idempotency(token_context):
    ctx = token_context
    body = dict(
        ctx["token_body"], approval_id=ctx["token_body"]["approval_id"].upper(), object_id=str(ctx["task_id"]).upper()
    )
    first = issue(ctx, body=body)
    assert first.status_code == 200, first.json()
    second = issue(ctx)
    assert second.status_code == 200 and second.json() == first.json()


def test_http_issuance_uses_real_six_role_facts_and_current_source(token_context, permission_context):
    ctx = token_context
    candidate(ctx, permission_context, ["operation.confirm"])
    ctx["token_service"].confirmation_authority = ctx["control_app"].state.permission_authority
    response = issue(ctx)
    assert response.status_code == 200, response.json()
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            "UPDATE mt.source_registry SET authorization_status='revoked',authorization_version='self-owned-revoked' WHERE source_id=%s",
            (ctx["source_id"],),
        )
    replay = issue(ctx)
    assert replay.status_code in {403, 409}, replay.json()


@pytest.mark.parametrize("missing", ["rules", "keys", "confirmation_authority"])
def test_missing_provider_never_creates_token(token_context, missing):
    ctx = token_context
    setattr(ctx["token_service"], missing, None)
    response = issue(ctx)
    assert response.status_code == 503, response.json()
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        assert admin.execute("SELECT count(*) FROM mt.operation_token").fetchone() == (0,)


@pytest.mark.parametrize("state", ["REQUESTED", "REVOKED", "RETURNED", "REJECTED", "INVALIDATED"])
def test_unapproved_or_revoked_chain_cannot_issue(token_context, state):
    ctx = token_context
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            "UPDATE mt.approval_request SET state=%s,row_version=row_version+1 WHERE approval_id=%s",
            (state, ctx["token_body"]["approval_id"]),
        )
    response = issue(ctx)
    assert response.status_code == 409, response.json()


def test_wrong_database_service_is_denied_before_writes_even_when_caught(token_context):
    ctx = token_context
    response = issue(ctx)
    assert response.status_code == 200, response.json()
    service, db = ctx["token_service"], ctx["control_app"].state.business_database
    original = service.database
    with (
        action_root(ctx, "sealEvidence", action_target(ctx)),
        db.transaction(Scope(ctx["actor"], ctx["case_id"])) as connection,
    ):
        service.database = ctx["database"]  # Separate Database instance, same isolated database.
        try:
            with pytest.raises(BusinessError):
                consume(ctx, response.json()["operation_token"], connection)
        finally:
            service.database = original
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        assert admin.execute("SELECT consumed_at,row_version FROM mt.operation_token").fetchone() == (None, 1)
        assert admin.execute(
            "SELECT count(*) FROM mt.audit_event WHERE action='operation_token.consume'"
        ).fetchone() == (0,)


def extend_synthetic_freshness(ctx):
    original = ctx["control_app"].state.conditional_permissions

    class ExtendedSyntheticFixture:
        def authorize_http(self, *args, **kwargs):
            return replace(original.authorize_http(*args, **kwargs), valid_until=time.time() + 60)

    ctx["control_app"].state.conditional_permissions = ExtendedSyntheticFixture()


def test_two_connections_compete_for_exactly_one_consumption(token_context):
    ctx = token_context
    extend_synthetic_freshness(ctx)
    response = issue(ctx)
    assert response.status_code == 200, response.json()
    barrier = Barrier(2)

    def attempt(index):
        db = Database(ctx["control_settings"].database_dsn)
        service = copy(ctx["token_service"])
        service.database = db
        current = dict(ctx, token_service=service)
        try:
            with action_root(current, "sealEvidence", action_target(current)):
                barrier.wait(timeout=5)
                try:
                    with db.transaction(Scope(ctx["actor"], ctx["case_id"])) as connection:
                        consume(current, response.json()["operation_token"], connection)
                    return "committed"
                except BusinessError as error:
                    assert error.http_status == 409
                    return "conflict"
        finally:
            db.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(attempt, [1, 2])) == ["committed", "conflict"]
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        assert admin.execute("SELECT count(*) FROM mt.operation_token WHERE consumed_at IS NOT NULL").fetchone() == (1,)
        assert admin.execute(
            "SELECT count(*) FROM mt.audit_event WHERE action='operation_token.consume'"
        ).fetchone() == (1,)


def test_real_fence_concurrent_issuance_does_not_upgrade_shared_task_locks(token_context, permission_context):
    ctx = token_context
    candidate(ctx, permission_context, ["operation.confirm"])
    ctx["token_service"].confirmation_authority = ctx["control_app"].state.permission_authority
    app = ctx["control_app"]
    second_app = create_app(
        ctx["control_settings"],
        app.state.business_authority,
        rules=app.state.approvals.rules,
        permission_authority=app.state.permission_authority,
        conditional_permissions=app.state.conditional_permissions,
        authorization_fence=app.state.authorization_fence,
        independent_duties=app.state.approvals.duties,
        operation_token_rules=ctx["token_service"].rules,
        operation_token_keys=ctx["token_service"].keys,
    )
    second_http = TestClient(second_app)
    clients = [ctx, dict(ctx, control_http=second_http)]
    barrier = Barrier(2)
    seen: set[object] = set()
    engines = [app.state.business_database.engine, second_app.state.business_database.engine]

    def synchronize(connection, cursor, statement, parameters, context, executemany):
        if (
            "SELECT mt.lookup_scope_metadata" in statement
            and isinstance(parameters, dict)
            and parameters.get("kind") == "task"
            and connection not in seen
        ):
            seen.add(connection)
            barrier.wait(timeout=8)

    for engine in engines:
        event.listen(engine, "after_cursor_execute", synchronize)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            responses = list(
                pool.map(lambda index: issue(clients[index], key="self-owned-parallel-" + str(index)), [0, 1])
            )
        assert [response.status_code for response in responses] == [200, 200], [
            response.json().get("code") for response in responses
        ]
    finally:
        for engine in engines:
            event.remove(engine, "after_cursor_execute", synchronize)
        second_http.close()
        second_app.state.business_database.close()


def test_idempotent_retry_and_consumer_use_consistent_database_lock_order(token_context):
    ctx = token_context
    extend_synthetic_freshness(ctx)
    response = issue(ctx)
    assert response.status_code == 200, response.json()
    issuer = ctx["control_app"].state.business_database
    consumer = Database(ctx["control_settings"].database_dsn)
    service = copy(ctx["token_service"])
    service.database = consumer
    current = dict(ctx, token_service=service)
    task_locked, token_read = Event(), Event()

    def pause_issuer(connection, cursor, statement, parameters, context, executemany):
        if "FROM mt.analysis_task WHERE" in statement and " FOR " in statement and not task_locked.is_set():
            task_locked.set()
            assert token_read.wait(timeout=8)

    def observe_consumer(connection, cursor, statement, parameters, context, executemany):
        if "SELECT * FROM mt.operation_token WHERE token_id" in statement:
            token_read.set()

    def consume_after_task_lock():
        assert task_locked.wait(timeout=8)
        with (
            action_root(current, "sealEvidence", action_target(current)),
            consumer.transaction(Scope(ctx["actor"], ctx["case_id"])) as connection,
        ):
            consume(current, response.json()["operation_token"], connection)
        return "consumed"

    event.listen(issuer.engine, "after_cursor_execute", pause_issuer)
    event.listen(consumer.engine, "after_cursor_execute", observe_consumer)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            used = pool.submit(consume_after_task_lock)
            replay = pool.submit(issue, ctx)
            retried = replay.result(timeout=15)
            if retried.status_code == 200:
                assert retried.json() == response.json()
            else:
                # Either request may obtain the token lock first. Both legal
                # serial orders must remain bounded, with exactly one consume.
                assert retried.status_code == 409
                assert retried.json()["code"] == "OPERATION_TOKEN_STATE_CONFLICT"
            assert used.result(timeout=15) == "consumed"
        with psycopg.connect(ctx["admin_dsn"]) as admin:
            assert admin.execute("SELECT consumed_at IS NOT NULL,row_version FROM mt.operation_token").fetchone() == (
                True,
                2,
            )
            assert admin.execute(
                "SELECT count(*) FROM mt.audit_event WHERE action='operation_token.consume'"
            ).fetchone() == (1,)
    finally:
        event.remove(issuer.engine, "after_cursor_execute", pause_issuer)
        event.remove(consumer.engine, "after_cursor_execute", observe_consumer)
        consumer.close()


def test_actual_expiry_cannot_be_extended_by_new_request(token_context):
    ctx = token_context
    ctx["token_service"].rules.ttl = 1
    response = issue(ctx)
    assert response.status_code == 200, response.json()
    time.sleep(1.05)
    assert issue(ctx).status_code == 409
    db = ctx["control_app"].state.business_database
    with (
        action_root(ctx, "sealEvidence", action_target(ctx)),
        pytest.raises(BusinessError),
        db.transaction(Scope(ctx["actor"], ctx["case_id"])) as connection,
    ):
        consume(ctx, response.json()["operation_token"], connection)


def test_restored_database_does_not_revive_old_generation_token(token_context, tmp_path):
    ctx = token_context
    extend_synthetic_freshness(ctx)
    response = issue(ctx)
    assert response.status_code == 200, response.json()
    dump = tmp_path / "t016-synthetic.dump"
    pg_tool("pg_dump", ctx["admin_dsn"], "-Fc", "--no-owner", "--file", str(dump))
    with empty_scope_database(ctx["admin_dsn"]) as restored_admin:
        pg_tool("pg_restore", restored_admin, "--no-owner", "--exit-on-error", str(dump))
        db = Database(
            make_conninfo(ctx["control_settings"].database_dsn, dbname=conninfo_to_dict(restored_admin)["dbname"])
        )
        service = copy(ctx["token_service"])
        service.database = db
        current = dict(ctx, token_service=service)
        try:
            with psycopg.connect(restored_admin) as admin:
                row = admin.execute("SELECT expires_at,consumed_at FROM mt.operation_token").fetchone()
                assert row is not None and row[0].timestamp() > time.time() and row[1] is None
            with (
                action_root(
                    current, "sealEvidence", action_target(current), generation="self-owned-restored-generation-2"
                ),
                pytest.raises(BusinessError) as rejected,
                db.transaction(Scope(ctx["actor"], ctx["case_id"])) as connection,
            ):
                consume(current, response.json()["operation_token"], connection)
            assert rejected.value.code == "OPERATION_TOKEN_STATE_CONFLICT"
            with psycopg.connect(restored_admin) as admin:
                assert admin.execute("SELECT consumed_at,row_version FROM mt.operation_token").fetchone() == (None, 1)
        finally:
            db.close()


@pytest.mark.parametrize(
    "field,value",
    [("object_id", str(UUID(int=99))), ("object_version", 2), ("purpose", "report_export")],
    ids=["object", "version", "purpose"],
)
def test_issue_rejects_request_binding_swap(token_context, field, value):
    ctx = token_context
    result = issue(ctx, body=dict(ctx["token_body"], **{field: value}))
    assert result.status_code in {403, 409, 422}, result.json()
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        assert admin.execute("SELECT count(*) FROM mt.operation_token").fetchone() == (0,)


def test_consume_and_synthetic_business_write_commit_once(token_context):
    ctx = token_context
    result = issue(ctx)
    assert result.status_code == 200, result.json()
    credential = result.json()["operation_token"]
    db = ctx["control_app"].state.business_database
    scope = Scope(ctx["actor"], ctx["case_id"])
    with action_root(ctx, "sealEvidence", action_target(ctx)), db.transaction(scope) as connection:
        consume(ctx, credential, connection)
        # Synthetic side effect only. This is not a real evidence seal consumer.
        connection.execute(
            text("UPDATE mt.cases SET display_code='synthetic-token-commit' WHERE case_id=:id"), {"id": scope.case_id}
        )
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        assert admin.execute("SELECT consumed_at IS NOT NULL,row_version FROM mt.operation_token").fetchone() == (
            True,
            2,
        )
        assert admin.execute(
            "SELECT count(*) FROM mt.audit_event WHERE action='operation_token.consume'"
        ).fetchone() == (1,)
    with (
        action_root(ctx, "sealEvidence", action_target(ctx)),
        pytest.raises(BusinessError),
        db.transaction(scope) as connection,
    ):
        consume(ctx, credential, connection)
    assert issue(ctx).status_code == 409


def test_business_failure_rolls_back_consume_and_success_audit(token_context):
    ctx = token_context
    result = issue(ctx)
    assert result.status_code == 200, result.json()
    db = ctx["control_app"].state.business_database
    with (
        action_root(ctx, "sealEvidence", action_target(ctx)),
        pytest.raises(RuntimeError),
        db.transaction(Scope(ctx["actor"], ctx["case_id"])) as connection,
    ):
        consume(ctx, result.json()["operation_token"], connection)
        raise RuntimeError("self-owned-business-write-failure")
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        assert admin.execute("SELECT consumed_at,row_version FROM mt.operation_token").fetchone() == (None, 1)
        assert admin.execute(
            "SELECT count(*) FROM mt.audit_event WHERE action='operation_token.consume'"
        ).fetchone() == (0,)


@pytest.mark.parametrize(
    "change", ["action", "object", "version", "approval", "hash", "generation", "issuance_root", "key", "rule"]
)
def test_consume_rejects_binding_key_rule_or_generation_change(token_context, change):
    ctx = token_context
    result = issue(ctx)
    assert result.status_code == 200, result.json()
    credential, overrides = result.json()["operation_token"], dict[str, Any]()
    service = ctx["token_service"]
    operation = "sealEvidence"
    generation = "explicit-synthetic-fixture"
    target = action_target(ctx)
    if change == "action":
        overrides["action"] = "createReport"
    elif change == "object":
        overrides["object_id"] = uuid4()
    elif change == "version":
        overrides["object_version"] = 2
    elif change == "approval":
        overrides["approval_id"] = uuid4()
    elif change == "hash":
        credential = hashlib.sha256(credential.encode()).hexdigest()
    elif change == "generation":
        generation = "self-owned-restored-generation-2"
    elif change == "issuance_root":
        operation = "issueOperationToken"  # Issuance is not action authority.
        target = RuleTarget(
            ctx["actor"].org_id, "approval", UUID(ctx["token_body"]["approval_id"]), 3, ctx["case_id"], "seal", None
        )
    elif change == "key":
        service.keys.key = OperationTokenKey("self-owned-key-2", b"different-synthetic-t016-key!!!!!!")
    else:
        service.rules.version = "self-owned-token-rule-2"
    db = ctx["control_app"].state.business_database
    with (
        action_root(ctx, operation, target, generation=generation),
        pytest.raises(BusinessError) as denied,
        db.transaction(Scope(ctx["actor"], ctx["case_id"])) as connection,
    ):
        consume(ctx, credential, connection, **overrides)
    assert denied.value.code in {
        "OPERATION_TOKEN_INVALID",
        "OPERATION_TOKEN_STATE_CONFLICT",
        "OPERATION_TOKEN_UNAVAILABLE",
    }


@pytest.mark.parametrize("change", ["key", "rule", "approval"])
def test_commit_time_revalidation_rolls_back_late_change(token_context, change):
    ctx = token_context
    result = issue(ctx)
    assert result.status_code == 200, result.json()
    service = ctx["token_service"]
    db = ctx["control_app"].state.business_database
    with (
        action_root(ctx, "sealEvidence", action_target(ctx)),
        pytest.raises(BusinessError),
        db.transaction(Scope(ctx["actor"], ctx["case_id"])) as connection,
    ):
        consume(ctx, result.json()["operation_token"], connection)
        if change == "key":
            service.keys.key = OperationTokenKey("self-owned-key-2", b"different-synthetic-t016-key!!!!!!")
        elif change == "rule":
            service.rules.version = "self-owned-token-rule-2"
        else:
            connection.execute(
                text("UPDATE mt.approval_request SET state='REVOKED',row_version=row_version+1 WHERE approval_id=:id"),
                {"id": ctx["token_body"]["approval_id"]},
            )
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        assert admin.execute("SELECT consumed_at,row_version FROM mt.operation_token").fetchone() == (None, 1)
