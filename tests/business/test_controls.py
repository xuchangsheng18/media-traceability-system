"""Self-owned fixtures only; none of these rules or identities are installed by the application."""

import hashlib
import io
import time
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import psycopg
import pytest
from business_app.controls.providers import ApprovalRule, ExportRule
from business_app.errors import BusinessError
from business_app.main import create_app
from business_app.permissions.catalog import load_catalog
from business_app.permissions.types import Principal
from business_app.types import Actor, Scope
from fastapi.testclient import TestClient

from tests.business.history_fixtures import prepare_history, snapshot
from tests.business.http_fixtures import (
    FixtureConditionals,
    FixtureDuties,
    FixtureFence,
    FixturePermissions,
    FixtureWork,
)
from tests.business.scoped_history_fixtures import append_synthetic_snapshot

AUTH = {"Authorization": "Bearer test-only-valid-token"}


@pytest.fixture
def control_context(business_context):
    context = prepare_history(business_context)
    append_synthetic_snapshot(context, snapshot(context, 1))
    reviewers = [Actor(uuid4(), context["actor"].org_id) for _ in range(2)]
    tokens = {
        "test-only-valid-token": context["actor"],
        "test-only-reviewer-1": reviewers[0],
        "test-only-reviewer-2": reviewers[1],
    }
    with psycopg.connect(context["admin_dsn"]) as connection:
        for actor in reviewers:
            connection.execute(
                "INSERT INTO mt.users(user_id,org_id,subject,enabled) VALUES(%s,%s,%s,true)",
                (actor.user_id, actor.org_id, str(actor.user_id)),
            )
            connection.execute(
                "INSERT INTO mt.case_membership(membership_id,case_id,org_id,user_id) VALUES(%s,%s,%s,%s)",
                (uuid4(), context["case_id"], actor.org_id, actor.user_id),
            )
        evidence = uuid4()
        connection.execute(
            """INSERT INTO mt.evidence_item(evidence_id,org_id,case_id,task_id,run_version,result_version,asset_id,type,object_id,sha256,captured_at,mapping_version,authorization_version,immutable_state)
            VALUES(%s,%s,%s,%s,1,1,%s,'synthetic-persistence-only',%s,%s,now(),'test-persistence/1','test-version-1','RECORDED')""",
            (
                evidence,
                context["actor"].org_id,
                context["case_id"],
                context["task_id"],
                context["asset_id"],
                context["input_ref"]["object_id"],
                context["input_ref"]["sha256"],
            ),
        )

    class TestAuthority:
        def authenticate_principal(self, token):
            actor = self.authenticate(token)
            return Principal(actor, "https://identity.example.test", str(actor.user_id), int(time.time()) + 600)

        def authenticate(self, token):
            if token not in tokens:
                raise BusinessError("AUTHENTICATION_REQUIRED", 401)
            return tokens[token]

        def authorize_case(self, actor, case_id, action):
            if actor not in tokens.values() or case_id != context["case_id"]:
                raise BusinessError("CASE_NOT_FOUND", 404)
            return Scope(actor, case_id)

        def authorize_source(self, scope, source_id, purpose):
            context["authority"].authorize_source(scope, source_id, purpose)

    class TestRules:
        def approval(self, scope, purpose, version):
            if version != "policy-dev-1" or purpose not in {"review", "report_export", "training_feedback"}:
                raise BusinessError("APPROVAL_RULE_UNAVAILABLE", 503)
            return ApprovalRule(version, 1800, 2)

        def review(self, scope, version, decision):
            if version != "policy-dev-1":
                raise BusinessError("APPROVAL_RULE_UNAVAILABLE", 503)

        def audit_export(self, scope, purpose):
            if purpose != "self-owned-test-audit":
                raise BusinessError("EXPORT_WINDOW_UNAUTHORIZED", 403)
            current = datetime.now(timezone.utc)
            return ExportRule(
                "policy-dev-1",
                current + timedelta(hours=1),
                100,
                1000000,
                current - timedelta(days=2),
                current + timedelta(days=2),
            )

        def cancellation(self, scope, approval_id):
            if approval_id is not None:
                raise BusinessError("CANCELLATION_RULE_UNAVAILABLE", 503)

    class TestDirectory:
        def current(self, actor):
            return dict(
                user_id=str(actor.user_id),
                org_id=str(actor.org_id),
                roles=["test-only-role"],
                permissions=["policy.read", "policy.manage", "model.read"],
                case_ids=[str(context["case_id"]), str(context["other_case_id"])],
            )

    settings = replace(context["settings"], control_ttl_seconds=3600, node_lease_seconds=30)
    from pathlib import Path

    permission_authority = FixturePermissions(
        frozenset(tokens.values()),
        frozenset(item.permission for item in load_catalog(Path(__file__).resolve().parents[2]).values()),
    )
    app = create_app(
        settings,
        TestAuthority(),
        rules=TestRules(),
        identity_directory=TestDirectory(),
        permission_authority=permission_authority,
        conditional_permissions=FixtureConditionals(frozenset(tokens.values()), context["database"]),
        independent_duties=FixtureDuties(frozenset(tokens.values()), context["actor"]),
        authorization_fence=FixtureFence(frozenset(tokens.values())),
        work_authorization=FixtureWork(frozenset(tokens.values())),
    )
    http = TestClient(app)
    try:
        yield dict(
            context,
            control_app=app,
            control_http=http,
            reviewers=reviewers,
            evidence_id=evidence,
            control_authority=app.state.business_authority,
            control_permission_authority=permission_authority,
            control_conditional_permissions=app.state.conditional_permissions,
            conditional_permissions=FixtureConditionals(frozenset(tokens.values()), context["database"]),
            rules=TestRules(),
            directory=TestDirectory(),
            control_settings=settings,
        )
    finally:
        http.close()
        app.state.business_database.close()
        context["http"].__exit__(None, None, None)
        context["app"].state.business_database.close()


def request_approval(context, *, purpose="review", kind="task"):
    body = dict(
        case_id=str(context["case_id"]),
        object_type=kind,
        object_id=str(context["task_id"] if kind == "task" else context["case_id"]),
        object_version=1,
        purpose=purpose,
        policy_version="policy-dev-1",
        reason="self-owned control fixture",
        run_version=1 if kind == "task" else None,
        result_version=1 if kind == "task" else None,
    )
    response = context["control_http"].post(
        "/api/v1/approvals", json=body, headers=dict(AUTH, **{"Idempotency-Key": uuid4().hex})
    )
    assert response.status_code == 201, response.json()
    return response.json()["approval_id"]


def decision(context, identifier, token, decision="approve", *, header=True):
    http = context["control_http"]
    current = http.get(f"/api/v1/approvals/{identifier}", headers=AUTH)
    headers = {"Authorization": "Bearer " + token, "Idempotency-Key": uuid4().hex}
    if header:
        headers["If-Match"] = current.headers["ETag"]
    return http.post(
        f"/api/v1/approvals/{identifier}/decisions",
        json=dict(
            expected_version=current.json()["approval"]["version"],
            decision=decision,
            reason="self-owned fixture decision",
            evidence_ids=[],
        ),
        headers=headers,
    )


def approve(context, identifier):
    first = decision(context, identifier, "test-only-reviewer-1")
    assert first.status_code == 201 and first.json()["state"] == "REQUESTED"
    second = decision(context, identifier, "test-only-reviewer-2")
    assert second.status_code == 201 and second.json()["state"] == "APPROVED"


def test_two_independent_approvers_and_revoke(control_context):
    c = control_context
    http = c["control_http"]
    identifier = request_approval(c)
    assert decision(c, identifier, "test-only-valid-token").status_code == 403
    assert decision(c, identifier, "test-only-reviewer-1", header=False).status_code == 428
    first = decision(c, identifier, "test-only-reviewer-1")
    assert first.status_code == 201 and first.json()["state"] == "REQUESTED"
    assert decision(c, identifier, "test-only-reviewer-1").status_code == 409
    assert decision(c, identifier, "test-only-reviewer-2").json()["state"] == "APPROVED"
    current = http.get(f"/api/v1/approvals/{identifier}", headers=AUTH)
    revoked = http.post(
        f"/api/v1/approvals/{identifier}/revoke",
        json=dict(expected_version=current.json()["approval"]["version"], reason="fixture revocation"),
        headers=dict(AUTH, **{"If-Match": current.headers["ETag"], "Idempotency-Key": uuid4().hex}),
    )
    assert revoked.status_code == 200 and revoked.json()["state"] == "REVOKED"
    assert len(http.get(f"/api/v1/approvals/{identifier}", headers=AUTH).json()["decisions"]) == 3


@pytest.mark.parametrize("outcome,state", [("reject", "REJECTED"), ("return", "RETURNED")])
def test_approval_terminal_cannot_be_reused(control_context, outcome, state):
    identifier = request_approval(control_context)
    response = decision(control_context, identifier, "test-only-reviewer-1", outcome)
    assert response.status_code == 201 and response.json()["state"] == state
    assert decision(control_context, identifier, "test-only-reviewer-2").status_code == 409


def test_approval_expiry_and_new_result_invalidate(control_context):
    c = control_context
    identifier = request_approval(c)
    append_synthetic_snapshot(c, snapshot(c, 2))
    assert (
        c["control_http"].get(f"/api/v1/approvals/{identifier}", headers=AUTH).json()["approval"]["state"]
        == "INVALIDATED"
    )
    with psycopg.connect(c["admin_dsn"]) as connection:
        connection.execute(
            "UPDATE mt.approval_request SET expires_at=now()-interval '1 minute' WHERE approval_id=%s", (identifier,)
        )
    assert (
        c["control_http"].get(f"/api/v1/approvals/{identifier}", headers=AUTH).json()["approval"]["state"] == "EXPIRED"
    )


def test_approval_pagination_binding_and_stale_cursor(control_context):
    c = control_context
    http = c["control_http"]
    for _ in range(3):
        request_approval(c)
    first = http.get("/api/v1/approvals", params=dict(case_id=str(c["case_id"]), limit=1), headers=AUTH)
    cursor = first.json()["next_cursor"]
    assert cursor and len(cursor) <= 128
    assert (
        http.get(
            "/api/v1/approvals", params=dict(case_id=str(c["case_id"]), limit=1, cursor=cursor), headers=AUTH
        ).status_code
        == 200
    )
    assert (
        http.get(
            "/api/v1/approvals", params=dict(case_id=str(c["case_id"]), limit=2, cursor=cursor), headers=AUTH
        ).status_code
        == 422
    )
    request_approval(c)
    assert (
        http.get(
            "/api/v1/approvals", params=dict(case_id=str(c["case_id"]), limit=1, cursor=cursor), headers=AUTH
        ).status_code
        == 409
    )


def review_body(context):
    return dict(
        task_id=str(context["task_id"]),
        run_version=1,
        result_version=1,
        expected_review_version=0,
        decision="return_for_evidence",
        reason="self-owned persistence evidence; no model assessment",
        evidence_ids=[str(context["evidence_id"])],
        policy_version="policy-dev-1",
    )


def test_review_append_version_and_exact_evidence(control_context):
    c = control_context
    http = c["control_http"]
    body = review_body(c)
    context = http.get(f"/api/v1/analysis/tasks/{c['task_id']}/review-context", headers=AUTH)
    assert context.status_code == 200
    key = uuid4().hex
    headers = {
        "Authorization": "Bearer test-only-reviewer-1",
        "If-Match": context.headers["ETag"],
        "Idempotency-Key": key,
    }
    created = http.post("/api/v1/reviews", json=body, headers=headers)
    assert created.status_code == 201, created.json()
    replay = http.post("/api/v1/reviews", json=body, headers=headers)
    assert replay.json() == created.json()
    stale = http.post("/api/v1/reviews", json=body, headers=dict(headers, **{"Idempotency-Key": uuid4().hex}))
    assert stale.status_code == 412
    read = http.get(f"/api/v1/reviews/{created.json()['review_id']}", headers=AUTH)
    assert read.json() == created.json()
    listing = http.get("/api/v1/reviews", params=dict(case_id=str(c["case_id"])), headers=AUTH)
    assert listing.json()["items"] == [created.json()]
    with psycopg.connect(c["admin_dsn"]) as connection:
        assert (
            required_scalar(
                connection.execute("SELECT report_eligibility FROM mt.analysis_task WHERE task_id=%s", (c["task_id"],))
            )
            == "draft_only"
        )
        with pytest.raises(psycopg.errors.ObjectNotInPrerequisiteState):
            connection.execute(
                "UPDATE mt.review_record SET comments='forbidden' WHERE review_id=%s", (created.json()["review_id"],)
            )


def test_review_no_rules_no_write(control_context):
    c = control_context
    app = create_app(
        c["control_settings"],
        c["control_authority"],
        permission_authority=c["control_permission_authority"],
        conditional_permissions=c["control_conditional_permissions"],
    )
    with TestClient(app) as http:
        response = http.post(
            "/api/v1/reviews",
            json=review_body(c),
            headers=dict(AUTH, **{"Idempotency-Key": uuid4().hex, "If-Match": '"untrusted"'}),
        )
    assert response.status_code == 503
    with psycopg.connect(c["admin_dsn"]) as connection:
        assert required_scalar(connection.execute("SELECT count(*) FROM mt.review_record")) == 0


@pytest.mark.parametrize("invalid", ["revoked_source", "wrong_digest", "corrupt_bytes"])
def test_review_checks_new_evidence_outside_snapshot(control_context, invalid):
    c = control_context
    source, asset, evidence = uuid4(), uuid4(), uuid4()
    stored = c["control_app"].state.upload_service.store.put_part(
        Scope(c["actor"], c["case_id"]), uuid4(), 1, io.BytesIO(b"self-owned extra evidence")
    )
    with psycopg.connect(c["admin_dsn"]) as connection:
        connection.execute(
            "INSERT INTO mt.source_registry(source_id,org_id,case_id,name,source_type,authorization_ref,purpose,authorization_status,authorization_version) VALUES(%s,%s,%s,'extra fixture','synthetic','test-only',ARRAY['analysis'],%s,'test-version-1')",
            (source, c["actor"].org_id, c["case_id"], "revoked" if invalid == "revoked_source" else "verified"),
        )
        connection.execute(
            "INSERT INTO mt.object_version(object_id,org_id,case_id,bucket_alias,object_key,version_id,sha256,size_bytes) VALUES(%s,%s,%s,'test-only',%s,%s,%s,%s)",
            (
                stored.ref.object_id,
                c["actor"].org_id,
                c["case_id"],
                str(stored.ref.object_id),
                stored.ref.version_id,
                stored.ref.sha256,
                stored.size_bytes,
            ),
        )
        connection.execute(
            "INSERT INTO mt.media_asset(asset_id,org_id,case_id,content_id,source_id,object_id,sha256,mime,size_bytes,kind,mapping_version,state) SELECT %s,org_id,case_id,content_id,%s,%s,%s,mime,%s,'original','test-persistence/1','VALID' FROM mt.media_asset WHERE asset_id=%s",
            (asset, source, stored.ref.object_id, stored.ref.sha256, stored.size_bytes, c["asset_id"]),
        )
        connection.execute(
            "INSERT INTO mt.evidence_item(evidence_id,org_id,case_id,task_id,run_version,result_version,asset_id,type,object_id,sha256,captured_at,mapping_version,authorization_version,immutable_state) VALUES(%s,%s,%s,%s,1,1,%s,'synthetic',%s,%s,now(),'test-persistence/1','test-version-1','RECORDED')",
            (
                evidence,
                c["actor"].org_id,
                c["case_id"],
                c["task_id"],
                asset,
                stored.ref.object_id,
                "0" * 64 if invalid == "wrong_digest" else stored.ref.sha256,
            ),
        )
    if invalid == "corrupt_bytes":
        (c["control_settings"].object_root / str(stored.ref.object_id) / (stored.ref.version_id + ".bin")).write_bytes(
            b"tampered"
        )
    current = c["control_http"].get(f"/api/v1/analysis/tasks/{c['task_id']}/review-context", headers=AUTH)
    response = c["control_http"].post(
        "/api/v1/reviews",
        json=dict(review_body(c), evidence_ids=[str(evidence)]),
        headers={
            "Authorization": "Bearer test-only-reviewer-1",
            "If-Match": current.headers["ETag"],
            "Idempotency-Key": uuid4().hex,
        },
    )
    assert response.status_code == {"revoked_source": 403, "wrong_digest": 409, "corrupt_bytes": 503}[invalid], (
        response.json()
    )
    with psycopg.connect(c["admin_dsn"]) as connection:
        assert required_scalar(connection.execute("SELECT count(*) FROM mt.review_record")) == 0


def export_fixture(context):
    identifier = request_approval(context, purpose="report_export", kind="operation")
    approve(context, identifier)
    current = datetime.now(timezone.utc)
    body = dict(
        start_at=(current - timedelta(hours=1)).isoformat(),
        end_at=(current + timedelta(minutes=1)).isoformat(),
        case_id=str(context["case_id"]),
        purpose="self-owned-test-audit",
        approval_id=identifier,
    )
    response = context["control_http"].post(
        "/api/v1/audit/exports", json=body, headers=dict(AUTH, **{"Idempotency-Key": uuid4().hex})
    )
    assert response.status_code == 202, response.json()
    return response.json()["object_id"], identifier


def test_export_fixed_artifact_range_and_revocation(control_context):
    c = control_context
    http = c["control_http"]
    identifier, approval = export_fixture(c)
    path = f"/api/v1/audit/exports/{identifier}"
    assert http.get(path, headers=AUTH).json()["state"] == "REQUESTED"
    assert http.get(path + "/content", headers=AUTH).status_code == 409
    c["control_app"].state.exports.process(Scope(c["actor"], c["case_id"]), UUID(identifier))
    status = http.get(path, headers=AUTH)
    assert status.json()["state"] == "READY"
    full = http.get(path + "/content", headers=AUTH)
    assert full.status_code == 200
    assert hashlib.sha256(full.content).hexdigest() == status.json()["artifact"]["sha256"]
    partial = http.get(path + "/content", headers=dict(AUTH, Range="bytes=0-9"))
    assert partial.status_code == 206 and partial.content == full.content[:10]
    assert http.get(path + "/content", headers=dict(AUTH, Range="bytes=-10")).content == full.content[-10:]
    assert http.get(path + "/content", headers=dict(AUTH, Range="bytes=1-2,4-5")).status_code == 416
    current = http.get(f"/api/v1/approvals/{approval}", headers=AUTH)
    revoke = http.post(
        f"/api/v1/approvals/{approval}/revoke",
        json=dict(expected_version=current.json()["approval"]["version"], reason="test"),
        headers=dict(AUTH, **{"If-Match": current.headers["ETag"], "Idempotency-Key": uuid4().hex}),
    )
    assert revoke.status_code == 200
    assert http.get(path + "/content", headers=dict(AUTH, Range="bytes=0-9")).status_code == 403


def test_current_user_filters_database_cases_and_policy_draft(control_context):
    c = control_context
    http = c["control_http"]
    current = http.get("/api/v1/auth/me", headers=AUTH)
    assert current.status_code == 200
    assert current.json()["case_ids"] == [str(c["case_id"])]
    body = dict(
        kind="review",
        version="self-owned-policy-1",
        definition_ref="urn:test:policy-definition-1",
        approval_id=None,
        status="DRAFT",
    )
    headers = dict(AUTH, **{"Idempotency-Key": uuid4().hex})
    created = http.post("/api/v1/policies", json=body, headers=headers)
    assert created.status_code == 201, created.json()
    assert http.get(f"/api/v1/policies/{created.json()['policy_id']}", headers=AUTH).json() == created.json()
    assert http.get(f"/api/v1/policies/{created.json()['policy_id']}/definition", headers=AUTH).status_code == 503
    assert (
        http.post(
            "/api/v1/policies",
            json=dict(body, status="APPROVED"),
            headers=dict(AUTH, **{"Idempotency-Key": uuid4().hex}),
        ).status_code
        == 503
    )
    assert (
        http.post(
            "/api/v1/policies",
            json=dict(body, definition_ref="urn:test:different"),
            headers=dict(AUTH, **{"Idempotency-Key": uuid4().hex}),
        ).status_code
        == 409
    )
    assert http.get("/api/v1/policies", headers=AUTH).json()["items"] == [created.json()]


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/auth/me",
        "/api/v1/approvals",
        "/api/v1/reviews",
        "/api/v1/audit/events",
        "/api/v1/sources",
        "/api/v1/policies",
    ],
)
def test_control_reads_reject_missing_identity(control_context, path):
    c = control_context
    params = {"case_id": str(c["case_id"])} if path not in {"/api/v1/auth/me", "/api/v1/policies"} else {}
    response = c["control_http"].get(path, params=params)
    assert response.status_code == 401


def test_source_sync_and_deployment_adapters_default_to_unavailable(control_context):
    c = control_context
    http = c["control_http"]
    source = http.get(f"/api/v1/sources/{c['source_id']}", headers=AUTH)
    assert source.status_code == 200
    sync = http.post(
        f"/api/v1/sources/{c['source_id']}/authorization/sync",
        json=dict(expected_version=1),
        headers=dict(AUTH, **{"If-Match": source.headers["ETag"], "Idempotency-Key": uuid4().hex}),
    )
    assert sync.status_code == 503
    assert http.get(f"/api/v1/model-operations/{uuid4()}", headers=AUTH).status_code == 503
    assert (
        http.get("/api/v1/sources", params=dict(case_id=str(c["case_id"])), headers=AUTH).json()["items"][0][
            "authorization_status"
        ]
        == "verified"
    )


def test_case_membership_revocation_overrides_cached_identity(control_context):
    c = control_context
    identifier = request_approval(c)
    http = c["control_http"]
    assert http.get("/api/v1/approvals", params=dict(case_id=str(c["other_case_id"])), headers=AUTH).status_code == 404
    with psycopg.connect(c["admin_dsn"]) as connection:
        connection.execute(
            "DELETE FROM mt.case_membership WHERE case_id=%s AND user_id=%s", (c["case_id"], c["actor"].user_id)
        )
    assert http.get(f"/api/v1/approvals/{identifier}", headers=AUTH).status_code == 404
    assert http.get("/api/v1/approvals", params=dict(case_id=str(c["case_id"])), headers=AUTH).status_code == 404


def test_corrupt_approved_flag_is_not_an_effective_approval(control_context):
    c = control_context
    identifier = request_approval(c)
    with psycopg.connect(c["admin_dsn"]) as connection:
        connection.execute("UPDATE mt.approval_request SET state='APPROVED' WHERE approval_id=%s", (identifier,))
    assert (
        c["control_http"].get(f"/api/v1/approvals/{identifier}", headers=AUTH).json()["approval"]["state"]
        == "INVALIDATED"
    )


def test_policy_same_key_different_payload_and_db_definition_change_rejected(control_context):
    c = control_context
    http = c["control_http"]
    headers = dict(AUTH, **{"Idempotency-Key": uuid4().hex})
    body = dict(kind="review", version="version-1", definition_ref="urn:test:draft", approval_id=None, status="DRAFT")
    first = http.post("/api/v1/policies", json=body, headers=headers)
    assert first.status_code == 201
    assert http.post("/api/v1/policies", json=dict(body, version="version-2"), headers=headers).status_code == 409
    with psycopg.connect(c["admin_dsn"]) as connection:
        with pytest.raises(psycopg.errors.CheckViolation):
            connection.execute(
                "UPDATE mt.policy_registry SET definition_ref='urn:test:changed' WHERE policy_id=%s",
                (first.json()["policy_id"],),
            )


def test_export_checks_actual_digest(control_context):
    c = control_context
    identifier, _ = export_fixture(c)
    scope = Scope(c["actor"], c["case_id"])
    c["control_app"].state.exports.process(scope, UUID(identifier))
    status = c["control_http"].get(f"/api/v1/audit/exports/{identifier}", headers=AUTH).json()
    ref = status["artifact"]
    file = c["control_settings"].object_root / ref["object_id"] / (ref["version_id"] + ".bin")
    file.write_bytes(b"corrupt-self-owned-test-only")
    assert c["control_http"].get(f"/api/v1/audit/exports/{identifier}/content", headers=AUTH).status_code == 503


def test_export_authorization_change_rolls_back_and_records_orphan(control_context, monkeypatch):
    c = control_context
    identifier, approval = export_fixture(c)
    service = c["control_app"].state.exports
    put = service.store.put_part

    def expired_after_write(*args, **kwargs):
        stored = put(*args, **kwargs)
        with psycopg.connect(c["admin_dsn"]) as connection:
            connection.execute(
                "UPDATE mt.approval_request SET expires_at=now()-interval '1 minute' WHERE approval_id=%s", (approval,)
            )
        return stored

    monkeypatch.setattr(service.store, "put_part", expired_after_write)
    with pytest.raises(BusinessError) as error:
        service.process(Scope(c["actor"], c["case_id"]), UUID(identifier))
    assert error.value.code == "EXPORT_APPROVAL_INVALID"
    with psycopg.connect(c["admin_dsn"]) as connection:
        assert (
            required_scalar(connection.execute("SELECT state FROM mt.audit_export WHERE export_id=%s", (identifier,)))
            == "REQUESTED"
        )
    orphans = list(c["control_settings"].object_root.rglob("*.orphan.json"))
    assert len(orphans) == 1 and "EXPORT_RECEIPT_NOT_COMMITTED" in orphans[0].read_text()


def required_scalar(cursor):
    value = cursor.fetchone()
    assert value is not None
    return value[0]
