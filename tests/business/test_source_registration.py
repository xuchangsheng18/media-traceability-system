"""Real PostgreSQL registration tests, with self-owned synthetic authority proofs only."""

import copy
import time
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import psycopg
import pytest
from business_app.contracts import validate_response
from business_app.errors import BusinessError
from business_app.permissions.object_facts import digest
from business_app.permissions.rule_types import ConditionFacts
from business_app.types import Scope
from fastapi import Request
from sqlalchemy import event

from tests.business.scoped_history_fixtures import history_read_evidence
from tests.business.t014_positive_fixtures import candidate
from tests.business.test_controls import AUTH
from tests.business.test_controls import control_context as control_context
from tests.business.test_t014_permissions import permission_context as permission_context


@pytest.fixture
def registration_context(request):
    from business_app.source_registration import SourceRegistrationProof

    ctx = request.getfixturevalue("control_context")
    permissions = request.getfixturevalue("permission_context")
    configured, objects, authority, facts = candidate(ctx, permissions, ["source.manage"], role_code="data_admin")
    body: dict[str, Any] = dict(
        case_id=str(ctx["case_id"]),
        name="self-owned synthetic registration",
        source_type="synthetic",
        authorization_ref="synthetic-reference/" + uuid4().hex,
        purpose=["upload", "analysis"],
        expires_at=None,
    )

    class SyntheticRegistrationAuthority:
        proof = SourceRegistrationProof(
            org_id=ctx["actor"].org_id,
            case_id=ctx["case_id"],
            source_type="synthetic",
            authorization_ref=body["authorization_ref"],
            purpose=("upload", "analysis"),
            expires_at=None,
            authorization_status="verified",
            authorization_version="self-owned-registration-authority/1",
            valid_until=datetime.now(timezone.utc) + timedelta(minutes=5),
        )

        def resolve(self, scope, body, *, connection):
            return self.proof

    class SyntheticRegistrationConditions:
        source_write_allowed = True

        def read(self, principal, operation_id, target, *, connection):
            previous = facts.read(principal, operation_id, target, connection=connection)
            checks = dict(previous.checks, authoritative_source_sync=self.source_write_allowed)
            return ConditionFacts(principal, target, checks, digest([target, checks]), time.time() + 60)

    conditions = SyntheticRegistrationConditions()
    objects.supplemental = conditions
    provider = SyntheticRegistrationAuthority()
    ctx["control_app"].state.source_registration.authority = provider
    return dict(ctx, body=body, provider=provider, source_conditions=conditions, configured=configured)


def register(ctx, *, body=None, key=None, headers=None, params=None):
    return ctx["control_http"].post(
        "/api/v1/sources",
        json=ctx["body"] if body is None else body,
        headers=dict(AUTH if headers is None else headers, **{"Idempotency-Key": key or uuid4().hex}),
        params=params,
    )


def counts(ctx):
    with psycopg.connect(ctx["admin_dsn"]) as connection:
        sources = connection.execute(
            "SELECT count(*) FROM mt.source_registry WHERE authorization_ref=%s", (ctx["body"]["authorization_ref"],)
        ).fetchone()
        assert sources is not None
        receipts = connection.execute(
            "SELECT count(*) FROM mt.idempotency_record WHERE operation='createSource'"
        ).fetchone()
        assert receipts is not None
        audits = connection.execute("SELECT count(*) FROM mt.audit_event WHERE action='source.registered'").fetchone()
        assert audits is not None
    return sources[0], receipts[0], audits[0]


@pytest.mark.parametrize("status", ["pending", "verified"])
def test_registration_inserts_authoritative_row_receipt_and_audit(registration_context, status):
    ctx = registration_context
    ctx["provider"].proof = replace(ctx["provider"].proof, authorization_status=status)
    response = register(ctx)
    assert response.status_code == 201, response.json()
    value = response.json()
    validate_response("Source", value)
    assert value == dict(ctx["body"], source_id=value["source_id"], authorization_status=status, version=1)
    assert response.headers["ETag"] and response.headers["Cache-Control"] == "no-store"
    with psycopg.connect(ctx["admin_dsn"]) as connection:
        row = connection.execute(
            "SELECT org_id,case_id,created_by,authorization_version,authorization_status,row_version "
            "FROM mt.source_registry WHERE source_id=%s",
            (value["source_id"],),
        ).fetchone()
        assert row == (
            ctx["actor"].org_id,
            ctx["case_id"],
            ctx["actor"].user_id,
            "self-owned-registration-authority/1",
            status,
            1,
        )
        audit = connection.execute(
            "SELECT actor_id,object_type,object_id,object_version,outcome FROM mt.audit_event "
            "WHERE action='source.registered'"
        ).fetchone()
        assert audit is not None
        assert tuple(map(str, audit)) == (str(ctx["actor"].user_id), "source", value["source_id"], "1", "allowed")
    assert counts(ctx) == (1, 1, 1)


def test_registration_replay_does_not_insert_or_audit_twice(registration_context):
    ctx, key = registration_context, uuid4().hex
    initial = register(ctx, key=key)
    assert initial.status_code == 201, initial.json()
    replay = register(ctx, key=key)
    assert replay.status_code == 201 and replay.json() == initial.json()
    assert counts(ctx) == (1, 1, 1)


def test_registration_idempotency_reuse_with_different_body_is_conflict(registration_context):
    ctx, key = registration_context, uuid4().hex
    assert register(ctx, key=key).status_code == 201
    changed = dict(ctx["body"], name="another source name")
    response = register(ctx, body=changed, key=key)
    assert response.status_code == 409 and response.json()["code"] == "IDEMPOTENCY_CONFLICT"
    assert counts(ctx) == (1, 1, 1)


def test_registration_expired_idempotency_key_cannot_be_reused(registration_context):
    ctx, key = registration_context, uuid4().hex
    assert register(ctx, key=key).status_code == 201
    with psycopg.connect(ctx["admin_dsn"]) as connection:
        connection.execute(
            "UPDATE mt.idempotency_record SET expires_at=now()-interval '1 second' WHERE operation='createSource'"
        )
    response = register(ctx, key=key)
    assert response.status_code == 409 and counts(ctx) == (1, 1, 1)


@pytest.mark.parametrize("field", ["authorization_version", "authorization_status", "row_version"])
def test_registration_replay_rejects_changed_persisted_authority(registration_context, field):
    ctx, key = registration_context, uuid4().hex
    response = register(ctx, key=key)
    assert response.status_code == 201
    expressions = {
        "authorization_version": "authorization_version='synthetic-new-version'",
        "authorization_status": "authorization_status='revoked'",
        "row_version": "row_version=row_version+1",
    }
    with psycopg.connect(ctx["admin_dsn"]) as connection:
        connection.execute(
            "UPDATE mt.source_registry SET " + expressions[field] + " WHERE source_id=%s",
            (response.json()["source_id"],),
        )
    replay = register(ctx, key=key)
    assert replay.status_code == 409 and "source_id" not in replay.json()
    assert counts(ctx) == (1, 1, 1)


def test_registration_replay_rechecks_revoked_external_authority(registration_context):
    ctx, key = registration_context, uuid4().hex
    assert register(ctx, key=key).status_code == 201
    ctx["provider"].proof = replace(ctx["provider"].proof, authorization_status="revoked")
    assert register(ctx, key=key).status_code == 403
    assert counts(ctx) == (1, 1, 1)


@pytest.mark.parametrize(
    "field,value", [("authorization_status", "verified"), ("org_id", str(uuid4())), ("actor_id", str(uuid4()))]
)
def test_registration_rejects_uncontracted_client_authority_fields(registration_context, field, value):
    ctx = registration_context
    response = register(ctx, body=dict(ctx["body"], **{field: value}))
    assert response.status_code == 422 and counts(ctx) == (0, 0, 0)


@pytest.mark.parametrize(
    "defect",
    [
        "missing",
        "malformed",
        "unavailable",
        "expired_proof",
        "wrong_case",
        "wrong_purpose",
        "revoked",
        "expired_source",
    ],
)
def test_registration_rejects_invalid_authority_without_persisting(registration_context, defect):
    ctx = registration_context
    provider = ctx["provider"]
    status = 503
    if defect == "missing":
        ctx["control_app"].state.source_registration.authority = None
    elif defect == "malformed":
        provider.proof = {"authorization_status": "verified"}
    elif defect == "unavailable":

        def unavailable(scope, body, *, connection):
            raise OSError("private-authority-address")

        provider.resolve = unavailable
    elif defect == "expired_proof":
        provider.proof = replace(provider.proof, valid_until=datetime.now(timezone.utc) - timedelta(seconds=1))
    else:
        status = 403
        if defect == "wrong_case":
            provider.proof = replace(provider.proof, case_id=uuid4())
        elif defect == "wrong_purpose":
            provider.proof = replace(provider.proof, purpose=("training",))
        elif defect == "revoked":
            provider.proof = replace(provider.proof, authorization_status="revoked")
        else:
            expired = datetime.now(timezone.utc) - timedelta(seconds=1)
            ctx["body"]["expires_at"] = expired.isoformat()
            provider.proof = replace(provider.proof, expires_at=expired)
    response = register(ctx)
    assert response.status_code == status, response.json()
    assert "private-authority-address" not in response.text
    assert counts(ctx) == (0, 0, 0)


def test_registration_refuses_missing_identity_and_unproven_source_management(registration_context):
    ctx = registration_context
    assert register(ctx, headers={}).status_code == 401
    ctx["source_conditions"].source_write_allowed = False
    assert register(ctx).status_code == 403
    assert counts(ctx) == (0, 0, 0)


def test_registration_cannot_choose_another_case(registration_context):
    ctx = registration_context
    response = register(ctx, body=dict(ctx["body"], case_id=str(ctx["other_case_id"])))
    assert response.status_code == 404 and counts(ctx) == (0, 0, 0)


def test_registration_authority_change_before_commit_rolls_back_all_writes(registration_context):
    ctx = registration_context
    engine = ctx["control_app"].state.business_database.engine

    def changed(connection, cursor, statement, parameters, context, executemany):
        if "INSERT INTO mt.source_registry" in statement:
            ctx["provider"].proof = replace(ctx["provider"].proof, authorization_version="synthetic-changed/2")

    event.listen(engine, "after_cursor_execute", changed)
    try:
        response = register(ctx)
    finally:
        event.remove(engine, "after_cursor_execute", changed)
    assert response.status_code == 503 and response.json()["code"] == "AUTHORIZATION_CHANGED"
    assert counts(ctx) == (0, 0, 0)


def test_registration_audit_failure_rolls_back_source_and_receipt(registration_context):
    ctx = registration_context
    engine = ctx["control_app"].state.business_database.engine

    def failed(connection, cursor, statement, parameters, context, executemany):
        if "INSERT INTO mt.audit_event" in statement:
            raise BusinessError("SOURCE_SYNCHRONIZATION_UNAVAILABLE", 503)

    event.listen(engine, "before_cursor_execute", failed)
    try:
        response = register(ctx)
    finally:
        event.remove(engine, "before_cursor_execute", failed)
    assert response.status_code == 503 and counts(ctx) == (0, 0, 0)


def test_registration_requires_configured_receipt_retention(registration_context):
    ctx = registration_context
    ctx["control_app"].state.control_receipts.control_ttl = None
    response = register(ctx)
    assert response.status_code == 503 and response.json()["code"] == "CONTROL_RECEIPT_TTL_UNCONFIRMED"
    assert counts(ctx) == (0, 0, 0)


@pytest.mark.parametrize("query", [[("case_id", "forged")], [("unknown", "1")], [("x", "1"), ("x", "2")]])
def test_registration_rejects_uncontracted_query_scope(registration_context, query):
    ctx = registration_context
    response = register(ctx, params=query)
    assert response.status_code == 422 and counts(ctx) == (0, 0, 0)


def test_registration_contract_rejects_duplicate_purposes(registration_context):
    ctx = registration_context
    body = copy.deepcopy(ctx["body"])
    body["purpose"] = ["upload", "upload"]
    response = register(ctx, body=body)
    assert response.status_code == 422 and counts(ctx) == (0, 0, 0)


def test_registration_requires_a_create_source_root_not_an_existing_task_root(registration_context):
    ctx = registration_context
    scope = Scope(ctx["actor"], ctx["case_id"])
    request = Request(dict(type="http", method="POST", path="/api/v1/sources", query_string=b"", headers=[]))
    with history_read_evidence(scope, "getTask", "task", ctx["task_id"]):
        with pytest.raises(BusinessError) as error:
            ctx["control_app"].state.source_registration.create(scope, ctx["body"], request, uuid4().hex)
    assert error.value.code == "AUTHORITY_SCOPE_INVALID" and counts(ctx) == (0, 0, 0)


def test_registration_requires_the_contract_idempotency_header(registration_context):
    ctx = registration_context
    response = ctx["control_http"].post("/api/v1/sources", json=ctx["body"], headers=AUTH)
    assert response.status_code == 422 and counts(ctx) == (0, 0, 0)


def test_registration_retains_the_actual_authoritative_expiry(registration_context):
    ctx = registration_context
    expires = (datetime.now(timezone.utc) + timedelta(days=1)).replace(microsecond=0)
    ctx["body"]["expires_at"] = expires.isoformat()
    ctx["provider"].proof = replace(ctx["provider"].proof, expires_at=expires)
    response = register(ctx)
    assert response.status_code == 201, response.json()
    assert response.json()["expires_at"] == expires.isoformat()
    with psycopg.connect(ctx["admin_dsn"]) as connection:
        assert connection.execute(
            "SELECT expires_at FROM mt.source_registry WHERE source_id=%s", (response.json()["source_id"],)
        ).fetchone() == (expires,)


@pytest.mark.parametrize(
    "fraction,microsecond",
    [
        ("1", 100000),
        ("12", 120000),
        ("123", 123000),
        ("1234", 123400),
        ("12345", 123450),
        ("123456", 123456),
        ("123456000", 123456),
    ],
)
@pytest.mark.parametrize("time_and_zone", [("00:00:00", "Z"), ("08:00:00", "+08:00")])
def test_registration_persists_fractional_expiry_without_changing_the_instant(
    registration_context, fraction, microsecond, time_and_zone
):
    ctx = registration_context
    expires = (datetime.now(timezone.utc) + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=microsecond
    )
    time, zone = time_and_zone
    ctx["body"]["expires_at"] = f"{expires.date().isoformat()}T{time}.{fraction}{zone}"
    ctx["provider"].proof = replace(ctx["provider"].proof, expires_at=expires)
    key = uuid4().hex
    response = register(ctx, key=key)
    assert response.status_code == 201, response.json()
    assert datetime.fromisoformat(response.json()["expires_at"]) == expires
    replay = register(ctx, key=key)
    assert replay.status_code == 201 and replay.json() == response.json()
    with psycopg.connect(ctx["admin_dsn"]) as connection:
        assert connection.execute(
            "SELECT expires_at FROM mt.source_registry WHERE source_id=%s", (response.json()["source_id"],)
        ).fetchone() == (expires,)
    assert counts(ctx) == (1, 1, 1)


def test_registration_cannot_round_a_valid_submicrosecond_expiry_to_match_authority(registration_context):
    ctx = registration_context
    expires = (datetime.now(timezone.utc) + timedelta(days=1)).replace(microsecond=123456)
    ctx["body"]["expires_at"] = expires.strftime("%Y-%m-%dT%H:%M:%S") + ".1234561Z"
    ctx["provider"].proof = replace(ctx["provider"].proof, expires_at=expires)
    response = register(ctx)
    # This is a valid date-time request; the current authority proof cannot
    # represent its exact expiry. No source, receipt or audit may be persisted.
    assert response.status_code == 403 and response.json()["code"] == "SOURCE_AUTHORIZATION_REQUIRED"
    assert counts(ctx) == (0, 0, 0)
