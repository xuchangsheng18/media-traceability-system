"""T014 strict permission catalog and real business-route boundaries."""

import importlib
import importlib.util
import json
import re
import time
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

import pytest
import yaml
from business_app.errors import BusinessError
from business_app.main import create_app
from business_app.permissions.catalog import load_catalog
from business_app.permissions.types import Principal
from business_app.settings import BusinessSettings
from business_app.types import Actor, Scope
from fastapi import FastAPI, Request
from fastapi.routing import APIRoute, iter_route_contexts
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
CATALOG = load_catalog(ROOT)
MATRIX = json.loads((ROOT / "docs/08-security/t014-interface-scope-matrix.json").read_text(encoding="utf8"))
MOUNTED = [CATALOG[row["operation_id"]] for row in MATRIX["operations"] if row["runtime_route"] is not None]


class SyntheticIdentity:
    def __init__(self):
        self.principal = Principal(
            Actor(uuid4(), uuid4()), "https://identity.example.test", "fixture-subject", int(time.time()) + 600
        )
        self.principal_calls = self.legacy_calls = self.scope_calls = 0

    def authenticate_principal(self, token):
        self.principal_calls += 1
        if token != "fixture-valid-token":
            raise BusinessError("AUTHENTICATION_REQUIRED", 401)
        return self.principal

    def authenticate(self, token):
        self.legacy_calls += 1
        if token != "fixture-valid-token":
            raise BusinessError("AUTHENTICATION_REQUIRED", 401)
        return self.principal.actor

    def authorize_case(self, actor, case_id, action):
        self.scope_calls += 1
        return Scope(actor, case_id)

    def authorize_source(self, scope, source_id, purpose):
        self.scope_calls += 1


class SyntheticPermissions:
    def __init__(self, mode="deny"):
        self.mode = mode
        self.calls: list[tuple[Principal, str]] = []

    def check(self, principal, permission):
        self.calls.append((principal, permission))
        if self.mode == "deny":
            raise BusinessError("PERMISSION_REQUIRED", 403)
        if self.mode == "unavailable":
            raise RuntimeError("fixture permission service unavailable")
        if self.mode == "invalid":
            return True
        return None


def business_app(tmp_path, mode="deny"):
    settings = BusinessSettings(
        "host=127.0.0.1 port=1 dbname=mt_business_guard user=unreachable",
        tmp_path / "objects",
        1024,
        256,
        60,
        "fixture-cursor-key-" + uuid4().hex,
    )
    identity, permissions = SyntheticIdentity(), SyntheticPermissions(mode)
    app = create_app(settings, identity)
    app.state.permission_authority = None if mode == "missing" else permissions
    return app, identity, permissions


def invoke(client, operation, *, authorization=None):
    # Well-formed paths and payloads; exact permission errors and zero scope calls
    # prove these denials occur before validation, lookup, writes or replay logic.
    path = re.sub(
        r"\{([^}]+)\}",
        lambda m: "1" if m[1] in {"part_no", "run_version", "result_version"} else str(uuid4()),
        operation.path,
    )
    headers = {"Idempotency-Key": uuid4().hex, "If-Match": '"fixture"'}
    if authorization is not None:
        headers["Authorization"] = authorization
    return client.request(operation.method, path, headers=headers, json={})


def guard_module():
    assert (ROOT / "backend/business_app/permissions/guard.py").is_file(), "T014 unified guard is missing"
    return importlib.import_module("business_app.permissions.guard")


def catalog_module():
    assert importlib.util.find_spec("business_app.permissions") is not None, "T014 permission package is missing"
    return importlib.import_module("business_app.permissions.catalog")


def test_catalog_matches_all_73_operations_and_41_permissions():
    catalog = catalog_module().load_catalog(ROOT)
    assert len(catalog) == 73
    assert len({item.permission for item in catalog.values()}) == 41
    assert [item.operation_id for item in catalog.values() if item.public] == ["devLogin"]
    assert catalog["getCurrentUser"].permission == "identity.read"
    assert catalog["getCurrentUser"].path == "/api/v1/auth/me"
    assert catalog["health"].public is False


@pytest.mark.parametrize("change", ["missing_permission", "duplicate_operation", "unknown_permission", "wrong_method"])
def test_catalog_rejects_missing_duplicate_or_unbound_permissions(tmp_path, change):
    module = catalog_module()
    document = yaml.safe_load((ROOT / "docs/03-api/openapi.yaml").read_text(encoding="utf8"))
    operation = document["paths"]["/auth/me"]["get"]
    if change == "missing_permission":
        operation.pop("x-required-permission")
    elif change == "duplicate_operation":
        operation["operationId"] = "health"
    elif change == "unknown_permission":
        operation["x-required-permission"] = "undeclared.permission"
    else:
        document["paths"]["/auth/me"]["post"] = document["paths"]["/auth/me"].pop("get")
    for folder in ["docs/03-api", "docs/08-security"]:
        (tmp_path / folder).mkdir(parents=True)
    (tmp_path / "docs/03-api/openapi.yaml").write_text(yaml.safe_dump(document), encoding="utf8")
    model = json.loads((ROOT / "docs/08-security/access-control-model.json").read_text(encoding="utf8"))
    (tmp_path / "docs/08-security/access-control-model.json").write_text(json.dumps(model), encoding="utf8")
    with pytest.raises(ValueError, match="PERMISSION_CATALOG_INVALID"):
        module.load_catalog(tmp_path)


def test_catalog_rejects_new_public_exception(tmp_path):
    module = catalog_module()
    document = yaml.safe_load((ROOT / "docs/03-api/openapi.yaml").read_text(encoding="utf8"))
    document["paths"]["/auth/me"]["get"]["security"] = []
    for folder in ["docs/03-api", "docs/08-security"]:
        (tmp_path / folder).mkdir(parents=True)
    (tmp_path / "docs/03-api/openapi.yaml").write_text(yaml.safe_dump(document), encoding="utf8")
    (tmp_path / "docs/08-security/access-control-model.json").write_bytes(
        (ROOT / "docs/08-security/access-control-model.json").read_bytes()
    )
    with pytest.raises(ValueError, match="PERMISSION_CATALOG_INVALID"):
        module.load_catalog(tmp_path)


def test_effective_route_set_is_exactly_43_and_does_not_skip_included_routers(tmp_path):
    app, _, _ = business_app(tmp_path)
    routes = [
        r
        for r in iter_route_contexts(app.routes)
        if isinstance(r.original_route, APIRoute) and (r.path or "").startswith("/api/v1/")
    ]
    assert len(routes) == len(MOUNTED) == 43
    assert {r.operation_id for r in routes} == {op.operation_id for op in MOUNTED}
    assert len(set(CATALOG) - {op.operation_id for op in MOUNTED}) == 30
    app.state.business_database.close()


@pytest.mark.parametrize("operation", MOUNTED, ids=lambda op: op.operation_id)
def test_all_43_mounted_business_operations_require_authentication(tmp_path, operation):
    app, identity, permissions = business_app(tmp_path)
    with TestClient(app) as client:
        response = invoke(client, operation)
    assert response.status_code == 401, response.json()
    assert response.json()["code"] == "AUTHENTICATION_REQUIRED"
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert identity.principal_calls == identity.legacy_calls == identity.scope_calls == 0
    assert permissions.calls == []


@pytest.mark.parametrize("operation", MOUNTED, ids=lambda op: op.operation_id)
def test_all_43_operations_deny_missing_permission(tmp_path, operation):
    app, identity, permissions = business_app(tmp_path)
    with TestClient(app) as client:
        response = invoke(client, operation, authorization="Bearer fixture-valid-token")
    assert response.status_code == 403, response.json()
    assert response.json()["code"] == "PERMISSION_REQUIRED"
    assert permissions.calls == [(identity.principal, operation.permission)]
    assert identity.principal_calls == 1
    assert identity.legacy_calls == identity.scope_calls == 0


@pytest.mark.parametrize("operation", MOUNTED, ids=lambda op: op.operation_id)
@pytest.mark.parametrize(
    "mode,code", [("missing", "FORMAL_POLICY_UNCONFIGURED"), ("unavailable", "IDENTITY_AUTHORITY_UNAVAILABLE")]
)
def test_all_43_operations_fail_closed_on_missing_or_unavailable_permissions(tmp_path, operation, mode, code):
    app, identity, permissions = business_app(tmp_path, mode)
    with TestClient(app) as client:
        response = invoke(client, operation, authorization="Bearer fixture-valid-token")
    assert response.status_code == 503, response.json()
    assert response.json()["code"] == code
    assert identity.principal_calls == 1
    assert identity.legacy_calls == identity.scope_calls == 0
    assert permissions.calls == ([] if mode == "missing" else [(identity.principal, operation.permission)])


@pytest.mark.parametrize("change", ["new", "duplicate", "outside_namespace", "mount", "guard_override"])
def test_new_or_duplicated_business_route_fails_startup_audit(tmp_path, change):
    app, _, _ = business_app(tmp_path)
    if change == "mount":
        app.mount("/api/v1/shadow", FastAPI())
    elif change == "guard_override":
        app.dependency_overrides[guard_module().authorize_business_route] = lambda: None
    else:
        path, operation = {
            "new": ("/api/v1/undeclared", "undeclared"),
            "duplicate": ("/api/v1/auth/me", "getCurrentUser"),
            "outside_namespace": ("/unguarded", "unguarded"),
        }[change]
        app.add_api_route(path, lambda: {"must_not_run": True}, methods=["GET"], operation_id=operation)
    with pytest.raises(RuntimeError, match="PERMISSION_ROUTE_COVERAGE_INVALID"):
        with TestClient(app):
            pass
    app.state.business_database.close()


def test_business_401_has_bearer_challenge(tmp_path):
    app, _, _ = business_app(tmp_path)
    with TestClient(app) as client:
        response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid-token"})
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_duplicate_authorization_header_is_rejected(tmp_path):
    app, identity, permissions = business_app(tmp_path)
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/auth/me",
            headers=[("Authorization", "Bearer fixture-valid-token"), ("Authorization", "Bearer fixture-valid-token")],
        )
    assert response.status_code == 401
    assert identity.principal_calls == identity.legacy_calls == 0
    assert permissions.calls == []


@pytest.mark.parametrize(
    "header", ["Bearer", "Bearer ", "Basic fixture", "Bearer invalid token", "Bearer token\tother"]
)
def test_malformed_authorization_is_rejected_before_identity_lookup(tmp_path, header):
    app, identity, permissions = business_app(tmp_path)
    with TestClient(app) as client:
        response = client.get("/api/v1/auth/me", headers={"Authorization": header})
    assert response.status_code == 401
    assert identity.principal_calls == identity.legacy_calls == 0
    assert permissions.calls == []


def test_request_reuses_exact_principal_and_rejects_changed_headers_or_expiry(tmp_path):
    from business_app.auth import authorize_request

    module = guard_module()
    app, identity, permissions = business_app(tmp_path, "allow")
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/auth/me",
            "app": app,
            "headers": [(b"authorization", b"Bearer fixture-valid-token")],
        }
    )
    module.require_permission("identity.read")(request)
    case = uuid4()
    assert authorize_request(request, case, "case.read") == Scope(identity.principal.actor, case)
    assert identity.principal_calls == 1 and identity.legacy_calls == 0
    request.scope["headers"] = [(b"authorization", b"Bearer different-token")]
    request.__dict__.pop("_headers", None)
    with pytest.raises(BusinessError) as changed:
        authorize_request(request, case, "case.read")
    assert changed.value.http_status == 401
    request.scope["headers"] = [(b"authorization", b"Bearer fixture-valid-token")]
    request.__dict__.pop("_headers", None)
    request.state.business_principal = replace(identity.principal, expires_at=0)
    with pytest.raises(BusinessError) as expired:
        authorize_request(request, case, "case.read")
    assert expired.value.http_status == 401
    app.state.business_database.close()


def test_unknown_permission_and_truthy_authority_return_do_not_allow(tmp_path):
    module = guard_module()
    app, _, _ = business_app(tmp_path, "invalid")
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/auth/me",
            "app": app,
            "headers": [(b"authorization", b"Bearer fixture-valid-token")],
        }
    )
    for permission in ["undeclared.permission", "identity.read"]:
        with pytest.raises(BusinessError) as caught:
            module.require_permission(permission)(request)
        assert caught.value.http_status == 503
    app.state.business_database.close()
