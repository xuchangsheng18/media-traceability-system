"""Permission denials with actual isolated resources and unchanged business state."""

import hashlib
import importlib
import json
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from business_app.errors import BusinessError
from business_app.main import create_app
from business_app.permissions.policy import DirectoryPermissionAuthority
from business_app.permissions.types import PermissionDecision
from fastapi.testclient import TestClient

from tests.business.http_fixtures import FixturePermissions
from tests.business.test_controls import AUTH
from tests.business.test_controls import control_context as control_context
from tests.business.test_t014_permissions import permission_context as permission_context
from tests.business.test_t014_permissions import reader

ROOT = Path(__file__).resolve().parents[2]
ROLE_CODES = [
    row["code"]
    for row in json.loads((ROOT / "docs/08-security/access-control-model.json").read_text(encoding="utf8"))["roles"]
]


def request_helpers():
    assert (ROOT / "tests/business/t014_requests.py").is_file(), "T014 real-resource request fixtures are missing"
    return importlib.import_module("tests.business.t014_requests")


def test_all_47_real_resource_requests_deny_before_business_side_effects(control_context):
    c = control_context
    helper = request_helpers()
    resources = helper.prepare_requests(c)
    app, http = c["control_app"], c["control_http"]
    original = app.state.permission_authority
    before = helper.business_state(c)

    class Unavailable:
        def check(self, principal, permission):
            raise TimeoutError("self-owned unavailable authority fixture")

    try:
        assert len(resources.requests) == 47
        for mode, port, expected, code in [
            ("unauthenticated", original, 401, "AUTHENTICATION_REQUIRED"),
            ("denied", FixturePermissions(frozenset(), frozenset()), 403, "PERMISSION_REQUIRED"),
            ("missing", None, 503, "FORMAL_POLICY_UNCONFIGURED"),
            ("unavailable", Unavailable(), 503, "IDENTITY_AUTHORITY_UNAVAILABLE"),
        ]:
            app.state.permission_authority = port
            observed = set()
            for operation, request in resources.requests.items():
                response = helper.send(http, request, authenticated=mode != "unauthenticated")
                assert response.status_code == expected, (operation, response.json())
                assert response.json()["code"] == code, (operation, response.json())
                observed.add(operation)
            assert observed == set(resources.requests)
            assert helper.business_state(c) == before, f"unauthorized business side effect in {mode}"
    finally:
        app.state.permission_authority = original
        resources.close()


@pytest.mark.parametrize("role_code", ROLE_CODES)
def test_each_candidate_role_has_no_implicit_permission_or_formal_allow(permission_context, role_code):
    ctx = permission_context
    lookup = reader(ctx)
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute("UPDATE mt.user_roles SET revoked_at=now() WHERE user_role_id=%s", (ctx["binding"],))
        role, relation = uuid4(), uuid4()
        admin.execute(
            "INSERT INTO mt.roles(role_id,code,description,enabled) VALUES(%s,%s,'self-owned candidate fixture',true)",
            (role, role_code),
        )
        admin.execute(
            "INSERT INTO mt.user_roles(user_role_id,user_id,role_id) VALUES(%s,%s,%s)",
            (relation, ctx["actor"].user_id, role),
        )
    assert lookup.read(ctx["principal"], "identity.read").eligible is False

    class ExplicitPolicy:
        version = "fixture-v1"

        def decide(self, fact):
            return PermissionDecision(fact.principal.actor, fact.permission, True, self.version, fact.version_digest)

    with pytest.raises(BusinessError) as denied:
        DirectoryPermissionAuthority(lookup, ExplicitPolicy()).check(ctx["principal"], "identity.read")
    assert (denied.value.code, denied.value.http_status) == ("PERMISSION_REQUIRED", 403)
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            "INSERT INTO mt.role_permissions(role_permission_id,role_id,permission_id) VALUES(%s,%s,%s)",
            (uuid4(), role, ctx["permission"]),
        )
    assert lookup.read(ctx["principal"], "identity.read").eligible is True
    with pytest.raises(BusinessError) as unconfigured:
        DirectoryPermissionAuthority(lookup, None).check(ctx["principal"], "identity.read")
    assert (unconfigured.value.code, unconfigured.value.http_status) == ("FORMAL_POLICY_UNCONFIGURED", 503)


@pytest.mark.parametrize(
    "state,expected",
    [("role", 403), ("permission", 403), ("role_disabled", 403), ("identity", 401), ("user", 401), ("unit", 401)],
)
def test_same_old_bearer_is_rechecked_after_real_directory_revocation(permission_context, state, expected):
    ctx = permission_context
    lookup = reader(ctx)

    class Identity:
        def authenticate_principal(self, bearer):
            assert bearer == "test-only-valid-token"
            return ctx["principal"]

        def authenticate(self, bearer):
            pytest.fail("HTTP scope must reuse the already bound principal")

        def authorize_case(self, actor, case_id, action):
            return ctx["authority"].authorize_case(actor, case_id, action)

        def authorize_source(self, scope, source_id, purpose):
            return ctx["authority"].authorize_source(scope, source_id, purpose)

    class Policy:
        version = "self-owned-policy-v1"

        def decide(self, fact):
            return PermissionDecision(fact.principal.actor, fact.permission, True, self.version, fact.version_digest)

    class Directory:
        def current(self, actor):
            return dict(
                user_id=str(actor.user_id),
                org_id=str(actor.org_id),
                roles=["self-owned-fixture"],
                permissions=["identity.read"],
                case_ids=[str(ctx["case_id"])],
            )

    app = create_app(
        ctx["settings"],
        Identity(),
        identity_directory=Directory(),
        permission_authority=DirectoryPermissionAuthority(lookup, Policy()),
        conditional_permissions=ctx["conditional_permissions"],
        authorization_fence=ctx["authorization_fence"],
    )
    with TestClient(app) as http:
        assert http.get("/api/v1/auth/me", headers=AUTH).status_code == 200
        query, identifier = {
            "role": ("UPDATE mt.user_roles SET revoked_at=now() WHERE user_role_id=%s", ctx["binding"]),
            "permission": (
                "UPDATE mt.role_permissions SET revoked_at=now() WHERE role_permission_id=%s",
                ctx["relation"],
            ),
            "role_disabled": ("UPDATE mt.roles SET enabled=false WHERE role_id=%s", ctx["role"]),
            "identity": (
                "UPDATE mt.user_identities SET enabled=false,revoked_at=now() WHERE identity_id=%s",
                ctx["identity"],
            ),
            "user": ("UPDATE mt.users SET enabled=false WHERE user_id=%s", ctx["actor"].user_id),
            "unit": ("UPDATE mt.organizations SET enabled=false WHERE org_id=%s", ctx["actor"].org_id),
        }[state]
        with psycopg.connect(ctx["admin_dsn"]) as admin:
            admin.execute(query, (identifier,))
        response = http.get("/api/v1/auth/me", headers=AUTH)
        assert response.status_code == expected
        assert response.json()["code"] == ("PERMISSION_REQUIRED" if expected == 403 else "AUTHENTICATION_REQUIRED")


@pytest.mark.parametrize("cross_unit", [False, True])
def test_function_permission_never_grants_unrelated_case_or_unit_resources(control_context, cross_unit):
    c = control_context
    helper = request_helpers()
    case, source = uuid4(), uuid4()
    org = c["other_actor"].org_id if cross_unit else c["actor"].org_id
    with psycopg.connect(c["admin_dsn"]) as admin:
        admin.execute(
            "INSERT INTO mt.cases(case_id,org_id,display_code,status) VALUES(%s,%s,'unrelated-fixture','ACTIVE')",
            (case, org),
        )
        admin.execute(
            "INSERT INTO mt.source_registry(source_id,org_id,case_id,name,source_type,authorization_ref,purpose,authorization_status,authorization_version) VALUES(%s,%s,%s,'other-case-sentinel','synthetic','fixture',ARRAY['upload'],'verified','fixture/1')",
            (source, org, case),
        )
        assert admin.execute("SELECT source_id FROM mt.source_registry WHERE source_id=%s", (source,)).fetchone() == (
            source,
        )
    before = helper.business_state(c)
    assert c["control_http"].get(f"/api/v1/sources/{c['source_id']}", headers=AUTH).status_code == 200
    response = c["control_http"].get(f"/api/v1/sources/{source}", headers=AUTH)
    assert response.status_code == 404
    assert "other-case-sentinel" not in response.text
    assert helper.business_state(c) == before


def test_revoked_function_permission_rejects_old_cursor_and_idempotent_receipt(control_context):
    c = control_context
    helper = request_helpers()
    from tests.business.test_controls import request_approval

    request_approval(c)
    key = uuid4().hex
    body = dict(
        case_id=str(c["case_id"]),
        object_type="task",
        object_id=str(c["task_id"]),
        object_version=1,
        purpose="review",
        policy_version="policy-dev-1",
        reason="self-owned replay fixture",
        run_version=1,
        result_version=1,
    )
    headers = dict(AUTH, **{"Idempotency-Key": key})
    first = c["control_http"].post("/api/v1/approvals", json=body, headers=headers)
    assert first.status_code == 201
    page = c["control_http"].get("/api/v1/approvals", params=dict(case_id=str(c["case_id"]), limit=1), headers=AUTH)
    cursor = page.json()["next_cursor"]
    assert cursor
    before = helper.business_state(c)
    c["control_app"].state.permission_authority = FixturePermissions(frozenset(), frozenset())
    for response in [
        c["control_http"].get(
            "/api/v1/approvals", params=dict(case_id=str(c["case_id"]), limit=1, cursor=cursor), headers=AUTH
        ),
        c["control_http"].post("/api/v1/approvals", json=body, headers=headers),
    ]:
        assert response.status_code == 403 and response.json()["code"] == "PERMISSION_REQUIRED"
    assert helper.business_state(c) == before


def test_upload_permission_revocation_refuses_old_part_cursor_and_write_receipt(business_context):
    c = business_context
    helper = request_helpers()
    body = dict(
        case_id=str(c["case_id"]),
        source_id=str(c["source_id"]),
        filename="self-owned.bin",
        size_bytes=6,
        mime="image/png",
        sha256=hashlib.sha256(b"ABCDEF").hexdigest(),
    )
    key = uuid4().hex
    app = create_app(
        replace(c["settings"], part_size_bytes=3),
        c["authority"],
        permission_authority=c["permission_authority"],
        conditional_permissions=c["conditional_permissions"],
        authorization_fence=c["authorization_fence"],
    )
    with TestClient(app) as http:
        created = http.post("/api/v1/uploads", json=body, headers=dict(AUTH, **{"Idempotency-Key": key}))
        assert created.status_code == 201
        upload = created.json()["upload_id"]
        part_headers = {}
        for number, data in [(1, b"ABC"), (2, b"DEF")]:
            headers = dict(
                AUTH,
                **{
                    "Idempotency-Key": uuid4().hex,
                    "Content-Length": "3",
                    "X-Part-Sha256": hashlib.sha256(data).hexdigest(),
                },
            )
            assert (
                http.put(f"/api/v1/uploads/{upload}/parts/{number}", content=data, headers=headers).status_code == 200
            )
            if number == 1:
                part_headers = headers
        page = http.get(f"/api/v1/uploads/{upload}/parts", params=dict(limit=1), headers=AUTH)
        assert page.status_code == 200
        cursor = page.json()["next_cursor"]
        assert cursor
        before = helper.business_state(c)
        app.state.permission_authority = FixturePermissions(frozenset(), frozenset())
        responses = [
            http.get(f"/api/v1/uploads/{upload}/parts", params=dict(limit=1, cursor=cursor), headers=AUTH),
            http.put(f"/api/v1/uploads/{upload}/parts/1", content=b"ABC", headers=part_headers),
            http.post("/api/v1/uploads", json=body, headers=dict(AUTH, **{"Idempotency-Key": key})),
        ]
        assert all(r.status_code == 403 and r.json()["code"] == "PERMISSION_REQUIRED" for r in responses)
        assert helper.business_state(c) == before
