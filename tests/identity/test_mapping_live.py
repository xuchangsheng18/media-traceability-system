"""Real Keycloak tokens plus existing isolated business identity schema."""

import json
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from business_app.db import Database
from business_app.errors import BusinessError
from business_app.identity.config import IdentityRuntimeConfig, load_private_config
from business_app.identity.directory import IdentityDirectory
from business_app.identity.runtime import open_identity
from business_app.identity.tokens import IntrospectionSettings
from psycopg import sql
from psycopg.conninfo import make_conninfo
from tools.identity_oidc_probe import PrivateValue, authorization_code_login


@pytest.fixture
def live_mapping(identity_realm, business_context, tmp_path):
    config, ctx = identity_realm, business_context
    bundle = authorization_code_login(config)
    role, password = "mt_live_lookup_" + uuid4().hex, uuid4().hex + uuid4().hex
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(sql.SQL("CREATE ROLE {} LOGIN NOSUPERUSER NOBYPASSRLS PASSWORD {}").format(sql.Identifier(role), sql.Literal(password)))
        admin.execute(sql.SQL("GRANT mt_identity_lookup TO {}").format(sql.Identifier(role)))
    manager = Database(ctx["admin_dsn"])
    with manager.engine.begin() as connection:
        identity_id = IdentityDirectory(connection).bind_identity(user_id=ctx["actor"].user_id, org_id=ctx["actor"].org_id,
            issuer=config["issuer"], subject=bundle.subject, mapping_version="self-owned-live-fixture-v1", enabled=True)
    settings = IntrospectionSettings(endpoint=config["issuer"] + "/protocol/openid-connect/token/introspect", issuer=config["issuer"],
        audience="media-trace-api", client_id="media-trace-api", client_secret=config["api_secret"], timeout_seconds=2,
        max_response_bytes=65536, max_token_bytes=16384)
    runtime = IdentityRuntimeConfig(settings, Path(config["ca_file"]), PrivateValue(make_conninfo(ctx["admin_dsn"], user=role, password=password)), ctx["settings"])
    resources = open_identity(runtime)
    try:
        yield config, ctx, bundle, resources, identity_id, runtime
    finally:
        resources.close()
        manager.close()
        with psycopg.connect(ctx["admin_dsn"]) as admin:
            admin.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
            admin.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))


def test_live_unmapped_subject_denied_without_email_mapping(live_mapping):
    config, ctx, token, resources, _, _ = live_mapping
    assert resources.authority.authenticate(token.access_token) == ctx["actor"]
    username, password = "unmapped-" + uuid4().hex, "Synthetic-Unmapped-2026!"
    response = config["admin"].request(
        "POST",
        config["admin_path"] + "/users",
        body={
            "username": username,
            "enabled": True,
            "firstName": "Synthetic",
            "lastName": "Unmapped",
            "email": username + "@example.invalid",
            "emailVerified": True,
            "credentials": [{"type": "password", "value": password, "temporary": False}],
        },
        expected=(201,),
    )
    user_id = response.headers["location"].rstrip("/").rsplit("/", 1)[1]
    try:
        unbound = authorization_code_login({**config, "username": username, "password": password})
    finally:
        config["admin"].request("DELETE", config["admin_path"] + "/users/" + user_id, expected=(204,))
    with pytest.raises(BusinessError) as failure:
        resources.authority.authenticate(unbound.access_token)
    assert failure.value.http_status == 401


@pytest.mark.parametrize("operation", ["disabled_user", "disabled_org", "revoked_mapping"])
def test_disabled_org_and_revoked_mapping_deny(live_mapping, operation):
    _, ctx, token, resources, identity, _ = live_mapping
    assert resources.authority.authenticate(token.access_token) == ctx["actor"]
    manager = Database(ctx["admin_dsn"])
    try:
        with manager.engine.begin() as connection:
            directory = IdentityDirectory(connection)
            if operation == "disabled_user":
                directory.disable_user(ctx["actor"].user_id, expected_version=1)
            elif operation == "disabled_org":
                directory.disable_organization(ctx["actor"].org_id, expected_version=1)
            else:
                directory.revoke_identity(identity, expected_version=1)
    finally:
        manager.close()
    with pytest.raises(BusinessError) as failure:
        resources.authority.authenticate(token.access_token)
    assert failure.value.http_status == 401


def test_keycloak_admin_has_no_business_case(live_mapping):
    config, ctx, token, resources, _, _ = live_mapping
    admin = config["admin"]
    clients = admin.request("GET", config["admin_path"] + "/clients").json()
    manager = next(c for c in clients if c["clientId"] == "realm-management")
    role = admin.request("GET", config["admin_path"] + "/clients/" + manager["id"] + "/roles/realm-admin").json()
    admin.request("POST", config["admin_path"] + "/users/" + config["user_id"] + "/role-mappings/clients/" + manager["id"], body=[role], expected=(204,))
    actor = resources.authority.authenticate(token.access_token)
    with pytest.raises(BusinessError) as failure:
        resources.authority.authorize_case(actor, ctx["case_id"], "case.read")
    assert failure.value.code == "FORMAL_POLICY_UNCONFIGURED"


def test_private_runtime_config_uses_real_idp_and_missing_business_providers_still_deny(live_mapping, tmp_path, monkeypatch):
    from dataclasses import asdict
    from business_app.identity.entrypoint import create_identity_app
    from fastapi.testclient import TestClient

    config, ctx, token, _, _, runtime = live_mapping
    root = tmp_path / "identity-config"
    root.mkdir(mode=0o700)
    ca = root / "ca.crt"
    ca.write_bytes(Path(config["ca_file"]).read_bytes())
    ca.chmod(0o600)
    path = root / "runtime.json"
    environment = {"MT_BUSINESS_DATABASE_DSN": ctx["settings"].database_dsn, "MT_BUSINESS_OBJECT_ROOT": str(ctx["settings"].object_root),
        "MT_BUSINESS_MAX_UPLOAD_BYTES": "1048576", "MT_BUSINESS_PART_SIZE_BYTES": "256000", "MT_BUSINESS_UPLOAD_TTL_SECONDS": "3600",
        "MT_BUSINESS_CURSOR_SECRET": ctx["settings"].cursor_secret}
    path.write_text(json.dumps(dict(introspection=asdict(runtime.introspection), ca_file=str(ca), lookup_dsn=runtime.lookup_dsn,
                                    business_environment=environment)))
    path.chmod(0o600)
    loaded = load_private_config(path)
    assert loaded.introspection.issuer == config["issuer"]
    monkeypatch.setenv("MT_IDENTITY_CONFIG", str(path))
    with TestClient(create_identity_app()) as app:
        response = app.get("/api/v1/auth/me", headers={"Authorization": "Bearer " + token.access_token})
        assert response.status_code == 503  # No invented directory/policy or business success.
