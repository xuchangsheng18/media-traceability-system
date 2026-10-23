"""Source synchronization against real SQL, six-role conditions and transaction fence.

Only the external authority and institutional SOURCE_WRITE input are synthetic.
Expected RED: authority reads outside the write transaction, missing final authority
recheck, stale receipt replay, unhandled provider failures and lossy expiry parsing.
"""

import copy
import time
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import psycopg
import pytest
from business_app.contracts import validate_response
from business_app.errors import BusinessError
from business_app.permissions.fence import AuthorizationFence
from business_app.permissions.object_facts import digest
from business_app.permissions.rule_types import ConditionFacts
from business_app.scope_context import current_scope_transaction
from fastapi.testclient import TestClient
from sqlalchemy import event

from tests.business.t014_positive_fixtures import candidate
from tests.business.test_controls import AUTH
from tests.business.test_controls import control_context as control_context
from tests.business.test_t014_permissions import permission_context as permission_context


@pytest.fixture
def source_sync_context(request):
    ctx = request.getfixturevalue("control_context")
    permissions = request.getfixturevalue("permission_context")
    configured, objects, _, facts = candidate(
        ctx, permissions, ["source.manage", "source.read"], role_code="data_admin"
    )

    class SyntheticSourceConditions:
        allowed: bool | None = True

        def read(self, principal, operation_id, target, *, connection):
            previous = facts.read(principal, operation_id, target, connection=connection)
            checks = dict(previous.checks, authoritative_source_sync=self.allowed)
            return ConditionFacts(principal, target, checks, digest([target, checks]), time.time() + 60)

    class SyntheticSourceAuthority:
        value: Any = dict(
            source_id=str(ctx["source_id"]),
            case_id=str(ctx["case_id"]),
            authorization_ref="self-owned-sync-authority/2",
            authorization_version="self-owned-sync/2",
            purpose=["upload", "analysis"],
            authorization_status="verified",
            expires_at=None,
        )
        failure: Exception | None = None
        shared = False

        def __init__(self):
            self.transactions = []

        def current(self, scope, source_id):
            assert scope.actor == ctx["actor"] and scope.case_id == ctx["case_id"]
            assert source_id == ctx["source_id"]
            root = current_scope_transaction()
            self.transactions.append(
                None if root is None else (root.connection.get_transaction(), root.scope.operation_id)
            )
            if self.failure is not None:
                raise self.failure
            return self.value if self.shared else copy.deepcopy(self.value)

    conditions, provider = SyntheticSourceConditions(), SyntheticSourceAuthority()
    objects.supplemental = conditions
    app = ctx["control_app"]
    app.state.source_synchronization = provider
    assert isinstance(app.state.authorization_fence, AuthorizationFence)
    http = TestClient(app, raise_server_exceptions=False)
    try:
        yield dict(ctx, configured=configured, provider=provider, conditions=conditions, sync_http=http)
    finally:
        http.close()


def detail(ctx):
    response = ctx["sync_http"].get(f"/api/v1/sources/{ctx['source_id']}", headers=AUTH)
    assert response.status_code == 200, response.text
    return response


def synchronize(ctx, *, key=None, body=None, etag=None, source=None, headers=None):
    values = dict(AUTH if headers is None else headers)
    values["Idempotency-Key"] = key or uuid4().hex
    if etag is not None:
        values["If-Match"] = etag
    return ctx["sync_http"].post(
        f"/api/v1/sources/{source or ctx['source_id']}/authorization/sync",
        json=dict(expected_version=1) if body is None else body,
        headers=values,
    )


def state(ctx):
    """Observe all three persisted effects without entering the business transaction."""
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        source = admin.execute(
            "SELECT authorization_ref,purpose,authorization_status,authorization_version,expires_at,row_version,"
            "updated_at FROM mt.source_registry WHERE source_id=%s",
            (ctx["source_id"],),
        ).fetchone()
        receipts = admin.execute(
            "SELECT count(*) FROM mt.idempotency_record WHERE operation='syncSourceAuthorization'"
        ).fetchone()
        audits = admin.execute(
            "SELECT count(*) FROM mt.audit_event WHERE action='source.authorization.sync'"
        ).fetchone()
        assert source is not None and receipts is not None and audits is not None
        return source, receipts[0], audits[0]


def assert_problem(response, status, code):
    assert response.status_code == status, response.text
    assert response.json()["code"] == code
    assert response.headers["content-type"].startswith("application/problem+json")
    assert "source_id" not in response.json()


def test_strict_sync_persists_authority_receipt_and_audit(source_sync_context):
    ctx = source_sync_context
    before = detail(ctx)
    response = synchronize(ctx, etag=before.headers["ETag"])
    assert response.status_code == 200, response.text
    validate_response("Source", response.json())
    assert response.json() == dict(
        before.json(),
        authorization_ref="self-owned-sync-authority/2",
        purpose=["upload", "analysis"],
        authorization_status="verified",
        expires_at=None,
        version=2,
    )
    assert response.headers["Cache-Control"] == "no-store" and response.headers["ETag"] != before.headers["ETag"]
    source, receipts, audits = state(ctx)
    assert source[:6] == (
        "self-owned-sync-authority/2",
        ["upload", "analysis"],
        "verified",
        "self-owned-sync/2",
        None,
        2,
    )
    assert (receipts, audits) == (1, 1)
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        assert admin.execute(
            "SELECT actor_id,object_type,object_id,object_version,outcome FROM mt.audit_event "
            "WHERE action='source.authorization.sync'"
        ).fetchone() == (ctx["actor"].user_id, "source", ctx["source_id"], 2, "allowed")


def test_authority_snapshot_and_recheck_share_the_write_transaction(source_sync_context):
    ctx = source_sync_context
    response = synchronize(ctx, etag=detail(ctx).headers["ETag"])
    assert response.status_code == 200, response.text
    reads = ctx["provider"].transactions
    assert len(reads) >= 2 and all(value is not None for value in reads)
    assert all(value == reads[0] and value[1] == "syncSourceAuthorization" for value in reads)


def test_identical_sync_replay_preserves_original_result_without_duplicate_effects(source_sync_context):
    ctx, key = source_sync_context, uuid4().hex
    original_etag = detail(ctx).headers["ETag"]
    first = synchronize(ctx, key=key, etag=original_etag)
    assert first.status_code == 200, first.text
    saved = state(ctx)
    replay = synchronize(ctx, key=key, etag=original_etag)
    assert replay.status_code == 200 and replay.json() == first.json()
    assert replay.headers["ETag"] == first.headers["ETag"] and state(ctx) == saved


def test_sync_replay_still_requires_original_if_match_header(source_sync_context):
    ctx, key = source_sync_context, uuid4().hex
    original_etag = detail(ctx).headers["ETag"]
    first = synchronize(ctx, key=key, etag=original_etag)
    assert first.status_code == 200, first.text
    before = state(ctx)
    replay = synchronize(ctx, key=key)
    assert_problem(replay, 428, "PRECONDITION_REQUIRED")
    assert state(ctx) == before


def test_sync_replay_cannot_replace_original_if_match_with_updated_strong_etag(source_sync_context):
    ctx, key = source_sync_context, uuid4().hex
    original_etag = detail(ctx).headers["ETag"]
    first = synchronize(ctx, key=key, etag=original_etag)
    assert first.status_code == 200, first.text
    updated_etag = first.headers["ETag"]
    assert updated_etag != original_etag and updated_etag.startswith('"')
    before = state(ctx)
    replay = synchronize(ctx, key=key, etag=updated_etag)
    assert_problem(replay, 412, "PRECONDITION_FAILED")
    assert state(ctx) == before


def test_sync_replay_refuses_receipt_without_original_if_match_proof(source_sync_context):
    ctx, key = source_sync_context, uuid4().hex
    original_etag = detail(ctx).headers["ETag"]
    assert synchronize(ctx, key=key, etag=original_etag).status_code == 200
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            "UPDATE mt.idempotency_record SET response_ref=response_ref-'original_if_match' "
            "WHERE operation='syncSourceAuthorization' AND idempotency_key=%s",
            (key,),
        )
    before = state(ctx)
    replay = synchronize(ctx, key=key, etag=original_etag)
    assert_problem(replay, 409, "SOURCE_VERSION_CONFLICT")
    assert state(ctx) == before


def test_sync_with_same_authority_version_cannot_change_its_content(source_sync_context):
    ctx = source_sync_context
    first = synchronize(ctx, etag=detail(ctx).headers["ETag"])
    assert first.status_code == 200, first.text
    ctx["provider"].value["purpose"] = ["analysis"]
    before = state(ctx)
    response = synchronize(ctx, etag=first.headers["ETag"], body=dict(expected_version=2))
    assert_problem(response, 503, "SOURCE_AUTHORITY_VERSION_CONFLICT")
    assert state(ctx) == before


def test_unchanged_authority_snapshot_does_not_increment_source_version(source_sync_context):
    ctx = source_sync_context
    first = synchronize(ctx, etag=detail(ctx).headers["ETag"])
    assert first.status_code == 200, first.text
    before = state(ctx)
    second = synchronize(ctx, etag=first.headers["ETag"], body=dict(expected_version=2))
    assert second.status_code == 200 and second.json() == first.json()
    source, receipts, audits = state(ctx)
    assert source == before[0] and (receipts, audits) == (2, 2)


def test_replay_after_newer_revocation_never_returns_old_verified_success(source_sync_context):
    ctx, key = source_sync_context, uuid4().hex
    etag = detail(ctx).headers["ETag"]
    first = synchronize(ctx, key=key, etag=etag)
    assert first.status_code == 200, first.text
    ctx["provider"].value.update(authorization_version="self-owned-sync/3", authorization_status="revoked")
    revoked = synchronize(ctx, etag=first.headers["ETag"], body=dict(expected_version=2))
    assert revoked.status_code == 200 and revoked.json()["authorization_status"] == "revoked", revoked.text
    before = state(ctx)
    assert before[0][2:4] == ("revoked", "self-owned-sync/3")
    replay = synchronize(ctx, key=key, etag=etag)
    assert_problem(replay, 409, "SOURCE_VERSION_CONFLICT")
    assert state(ctx) == before


def test_receipt_binds_internal_authority_version_even_when_public_source_is_identical(source_sync_context):
    ctx, key = source_sync_context, uuid4().hex
    etag = detail(ctx).headers["ETag"]
    assert synchronize(ctx, key=key, etag=etag).status_code == 200
    # Real external reconciliation changes only the internal version; Source has
    # no authorization_version field, so comparing the public response is insufficient.
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            "UPDATE mt.source_registry SET authorization_version='self-owned-sync/3' WHERE source_id=%s",
            (ctx["source_id"],),
        )
    ctx["provider"].value["authorization_version"] = "self-owned-sync/3"
    before = state(ctx)
    replay = synchronize(ctx, key=key, etag=etag)
    assert_problem(replay, 409, "SOURCE_VERSION_CONFLICT")
    assert state(ctx) == before


@pytest.mark.parametrize(
    "mode,status,code",
    [
        ("missing_etag", 428, "PRECONDITION_REQUIRED"),
        ("stale_etag", 412, "PRECONDITION_FAILED"),
        ("wrong_version", 409, "SOURCE_VERSION_CONFLICT"),
    ],
)
def test_sync_requires_current_etag_and_expected_version(source_sync_context, mode, status, code):
    ctx = source_sync_context
    etag = detail(ctx).headers["ETag"]
    before = state(ctx)
    response = synchronize(
        ctx,
        etag=None if mode == "missing_etag" else '"stale"' if mode == "stale_etag" else etag,
        body=dict(expected_version=2 if mode == "wrong_version" else 1),
    )
    assert_problem(response, status, code)
    assert state(ctx) == before


@pytest.mark.parametrize("mode", ["different_body", "expired_key"])
def test_sync_idempotency_conflicts_do_not_write(source_sync_context, mode):
    ctx, key = source_sync_context, uuid4().hex
    etag = detail(ctx).headers["ETag"]
    assert synchronize(ctx, key=key, etag=etag).status_code == 200
    if mode == "expired_key":
        with psycopg.connect(ctx["admin_dsn"]) as admin:
            admin.execute(
                "UPDATE mt.idempotency_record SET expires_at=now()-interval '1 second' "
                "WHERE operation='syncSourceAuthorization'"
            )
    before = state(ctx)
    response = synchronize(ctx, key=key, etag=etag, body=dict(expected_version=2 if mode == "different_body" else 1))
    assert_problem(response, 409, "IDEMPOTENCY_CONFLICT")
    assert state(ctx) == before


@pytest.mark.parametrize(
    "field,expression",
    [
        ("authorization_version", "authorization_version='self-owned-sync/3'"),
        ("authorization_status", "authorization_status='revoked'"),
        ("authorization_ref", "authorization_ref='self-owned-changed-reference'"),
        ("purpose", "purpose=ARRAY['analysis']"),
        ("expires_at", "expires_at='2036-10-21T10:00:00Z'"),
        ("row_version", "row_version=row_version+1"),
    ],
)
def test_sync_replay_rejects_changed_current_row(source_sync_context, field, expression):
    ctx, key = source_sync_context, uuid4().hex
    etag = detail(ctx).headers["ETag"]
    assert synchronize(ctx, key=key, etag=etag).status_code == 200
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute("UPDATE mt.source_registry SET " + expression + " WHERE source_id=%s", (ctx["source_id"],))
    before = state(ctx)
    response = synchronize(ctx, key=key, etag=etag)
    assert_problem(response, 409, "SOURCE_VERSION_CONFLICT")
    assert state(ctx) == before, field


@pytest.mark.parametrize(
    "field,value",
    [
        ("authorization_version", "self-owned-sync/3"),
        ("authorization_status", "revoked"),
        ("authorization_ref", "self-owned-other-reference"),
        ("purpose", ["analysis"]),
        ("expires_at", "2036-10-21T10:00:00Z"),
    ],
)
def test_sync_replay_rejects_changed_external_authority(source_sync_context, field, value):
    ctx, key = source_sync_context, uuid4().hex
    etag = detail(ctx).headers["ETag"]
    assert synchronize(ctx, key=key, etag=etag).status_code == 200
    ctx["provider"].value[field] = value
    before = state(ctx)
    response = synchronize(ctx, key=key, etag=etag)
    assert_problem(response, 409, "SOURCE_VERSION_CONFLICT")
    assert state(ctx) == before


@pytest.mark.parametrize("shared", [False, True])
@pytest.mark.parametrize(
    "field,value",
    [("authorization_version", "self-owned-sync/3"), ("authorization_status", "revoked"), ("purpose", ["analysis"])],
)
def test_authority_change_after_all_writes_rolls_back_source_receipt_and_audit(
    source_sync_context, shared, field, value
):
    ctx = source_sync_context
    ctx["provider"].shared = shared
    etag, before = detail(ctx).headers["ETag"], state(ctx)
    engine = ctx["control_app"].state.business_database.engine

    def changed(connection, cursor, statement, parameters, context, executemany):
        if "INSERT INTO mt.audit_event" in statement:
            ctx["provider"].value[field] = value

    event.listen(engine, "after_cursor_execute", changed)
    try:
        response = synchronize(ctx, etag=etag)
    finally:
        event.remove(engine, "after_cursor_execute", changed)
    assert_problem(response, 503, "AUTHORIZATION_CHANGED")
    assert state(ctx) == before


@pytest.mark.parametrize("late", [False, True])
@pytest.mark.parametrize("error", [TimeoutError, ValueError, OSError])
def test_authority_failure_is_sanitized_and_rolls_back(source_sync_context, late, error):
    ctx = source_sync_context
    etag, before = detail(ctx).headers["ETag"], state(ctx)
    failure = error("private-authority-address-and-credentials")
    engine = ctx["control_app"].state.business_database.engine

    def failed(connection, cursor, statement, parameters, context, executemany):
        if "INSERT INTO mt.audit_event" in statement:
            ctx["provider"].failure = failure

    if late:
        event.listen(engine, "after_cursor_execute", failed)
    else:
        ctx["provider"].failure = failure
    try:
        response = synchronize(ctx, etag=etag)
    finally:
        if late:
            event.remove(engine, "after_cursor_execute", failed)
    assert_problem(response, 503, "SOURCE_SYNCHRONIZATION_UNAVAILABLE")
    assert "private-authority" not in response.text and state(ctx) == before


@pytest.mark.parametrize("mode", ["missing", "malformed", "wrong_source", "wrong_case"])
def test_invalid_authority_cannot_update_the_source(source_sync_context, mode):
    ctx = source_sync_context
    etag, before = detail(ctx).headers["ETag"], state(ctx)
    code = "SOURCE_SYNCHRONIZATION_UNAVAILABLE" if mode == "missing" else "RESPONSE_CONTRACT_UNAVAILABLE"
    if mode == "missing":
        ctx["control_app"].state.source_synchronization = None
    elif mode == "malformed":
        ctx["provider"].value = {"authorization_status": "verified"}
    else:
        ctx["provider"].value["source_id" if mode == "wrong_source" else "case_id"] = str(uuid4())
        code = "SOURCE_AUTHORITY_BINDING_INVALID"
    response = synchronize(ctx, etag=etag)
    assert_problem(response, 503, code)
    assert state(ctx) == before


def test_audit_failure_rolls_back_source_and_receipt(source_sync_context):
    ctx = source_sync_context
    etag, before = detail(ctx).headers["ETag"], state(ctx)
    engine = ctx["control_app"].state.business_database.engine

    def failed(connection, cursor, statement, parameters, context, executemany):
        if "INSERT INTO mt.audit_event" in statement:
            raise BusinessError("SOURCE_SYNCHRONIZATION_UNAVAILABLE", 503)

    event.listen(engine, "before_cursor_execute", failed)
    try:
        response = synchronize(ctx, etag=etag)
    finally:
        event.remove(engine, "before_cursor_execute", failed)
    assert_problem(response, 503, "SOURCE_SYNCHRONIZATION_UNAVAILABLE")
    assert state(ctx) == before


@pytest.mark.parametrize(
    "allowed,status,code", [(False, 403, "PERMISSION_REQUIRED"), (None, 503, "CONDITIONAL_FACTS_UNAVAILABLE")]
)
def test_source_manage_permission_requires_actual_source_write_condition(source_sync_context, allowed, status, code):
    ctx = source_sync_context
    etag, before = detail(ctx).headers["ETag"], state(ctx)
    ctx["conditions"].allowed = allowed
    response = synchronize(ctx, etag=etag)
    assert_problem(response, status, code)
    assert state(ctx) == before and not ctx["provider"].transactions


def test_sync_refuses_missing_identity_and_idempotency_header(source_sync_context):
    ctx = source_sync_context
    etag, before = detail(ctx).headers["ETag"], state(ctx)
    assert_problem(synchronize(ctx, headers={}, etag=etag), 401, "AUTHENTICATION_REQUIRED")
    response = ctx["sync_http"].post(
        f"/api/v1/sources/{ctx['source_id']}/authorization/sync",
        json=dict(expected_version=1),
        headers=dict(AUTH, **{"If-Match": etag}),
    )
    assert_problem(response, 422, "INPUT_INVALID")
    assert state(ctx) == before


def test_sync_cannot_accept_client_authority_fields(source_sync_context):
    ctx = source_sync_context
    etag, before = detail(ctx).headers["ETag"], state(ctx)
    response = synchronize(ctx, etag=etag, body=dict(expected_version=1, authorization_status="verified"))
    assert_problem(response, 422, "INPUT_INVALID")
    assert state(ctx) == before


@pytest.mark.parametrize("foreign_org", [False, True])
def test_sync_cannot_manage_another_case_or_unit(source_sync_context, foreign_org):
    ctx, source = source_sync_context, uuid4()
    org = ctx["other_actor"].org_id if foreign_org else ctx["actor"].org_id
    case = ctx["other_case_id"] if foreign_org else uuid4()
    creator = ctx["other_actor"].user_id if foreign_org else ctx["reviewers"][0].user_id
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        if not foreign_org:
            admin.execute(
                "INSERT INTO mt.cases(case_id,org_id,display_code,status) VALUES(%s,%s,%s,'ACTIVE')",
                (case, org, "unassigned-sync-case-" + uuid4().hex),
            )
        admin.execute(
            "INSERT INTO mt.source_registry(source_id,org_id,case_id,name,source_type,authorization_ref,purpose,"
            "authorization_status,authorization_version,created_by) "
            "VALUES(%s,%s,%s,'synthetic foreign source','synthetic','self-owned-foreign',ARRAY['analysis'],"
            "'verified','synthetic-foreign/1',%s)",
            (source, org, case, creator),
        )
    before = state(ctx)
    response = synchronize(ctx, source=source, etag='"not-an-access-credential"')
    assert response.status_code == 404, response.text
    assert "source_id" not in response.json() and not ctx["provider"].transactions
    assert state(ctx) == before
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        assert admin.execute(
            "SELECT authorization_version,row_version FROM mt.source_registry WHERE source_id=%s", (source,)
        ).fetchone() == ("synthetic-foreign/1", 1)


def test_sync_keeps_existing_expired_source_write_refusal(source_sync_context):
    ctx = source_sync_context
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            "UPDATE mt.source_registry SET expires_at=now()-interval '1 second' WHERE source_id=%s", (ctx["source_id"],)
        )
    before = state(ctx)
    response = synchronize(ctx, etag=detail(ctx).headers["ETag"])
    assert_problem(response, 503, "CONDITIONAL_FACTS_UNAVAILABLE")
    assert state(ctx) == before and not ctx["provider"].transactions


@pytest.mark.parametrize(
    "expires,expected",
    [
        ("2036-10-21T10:00:00.1Z", "2036-10-21T10:00:00.100000+00:00"),
        ("2036-10-21T10:00:00.123456000Z", "2036-10-21T10:00:00.123456+00:00"),
    ],
)
def test_sync_preserves_representable_authoritative_expiry(source_sync_context, expires, expected):
    ctx = source_sync_context
    ctx["provider"].value["expires_at"] = expires
    response = synchronize(ctx, etag=detail(ctx).headers["ETag"])
    assert response.status_code == 200, response.text
    assert datetime.fromisoformat(response.json()["expires_at"]) == datetime.fromisoformat(expected)
    assert state(ctx)[0][4] == datetime.fromisoformat(expected).astimezone(timezone.utc)


def test_sync_cannot_truncate_nonzero_submicrosecond_authoritative_expiry(source_sync_context):
    ctx = source_sync_context
    ctx["provider"].value["expires_at"] = "2036-10-21T10:00:00.1234567Z"
    etag, before = detail(ctx).headers["ETag"], state(ctx)
    response = synchronize(ctx, etag=etag)
    assert response.status_code == 503, response.text
    assert "source_id" not in response.json() and state(ctx) == before
