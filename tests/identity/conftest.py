"""Explicit real identity test target; never substitutes a mock or skips silently."""

import copy
import json
import os
import secrets
import ssl
from pathlib import Path
from uuid import uuid4

import httpx
import psycopg
import pytest
from business_app.db import Database
from business_app.identity.config import IdentityRuntimeConfig
from business_app.identity.directory import IdentityDirectory
from business_app.identity.runtime import open_identity
from business_app.identity.tokens import IntrospectionSettings
from psycopg import sql
from psycopg.conninfo import make_conninfo

from tests.business import conftest as business_fixtures

business_context = business_fixtures.business_context
business_template = business_fixtures.business_template
database_dsn = business_fixtures.database_dsn
from tools.identity_oidc_probe import PrivateValue, authorization_code_login


@pytest.fixture(scope="session")
def identity_config():
    name = os.environ.get("MT_IDENTITY_TEST_CONFIG")
    if not name:
        pytest.fail("MT_IDENTITY_TEST_CONFIG_REQUIRED_REAL_IDENTITY_TESTS_NOT_EXECUTED")
    path = Path(name)
    if path.is_symlink() or path.stat().st_mode & 0o077 or path.stat().st_uid != os.geteuid():
        pytest.fail("PRIVATE_IDENTITY_TEST_CONFIGURATION_REQUIRED")
    data = json.loads(path.read_text())
    assert data["public_url"] == "https://172.16.58.179:18443"
    assert data["admin_url"] == "https://localhost:18444"
    assert Path(data["ca_file"]).is_file()
    return data


@pytest.fixture
def identity_http(identity_config):
    context = ssl.create_default_context(cafile=identity_config["ca_file"])
    with httpx.Client(verify=context, trust_env=False, timeout=5, follow_redirects=False) as client:
        yield client


@pytest.fixture
def identity_realm(identity_config):
    from scripts.identity.common import ROOT
    from scripts.identity.provision import AdminClient
    from tools.identity_oidc_probe import REDIRECT, PrivateValue

    admin = AdminClient()
    name = "media-trace-acceptance-" + uuid4().hex
    api_secret = PrivateValue(secrets.token_hex(32))
    password = PrivateValue(secrets.token_hex(24))
    realm = copy.deepcopy(json.loads((ROOT / "config/identity/realm.template.json").read_text()))
    realm["realm"] = name
    realm["clients"][0]["secret"] = api_secret
    probe = realm["clients"][1]
    probe.update(
        clientId="media-trace-probe", enabled=True, redirectUris=[REDIRECT], webOrigins=["https://localhost:18444"]
    )
    probe["attributes"]["post.logout.redirect.uris"] = REDIRECT
    path = "/admin/realms/" + name
    created = False
    try:
        admin.request("POST", "/admin/realms", body=realm, expected=(201,))
        created = True
        username = "synthetic-" + uuid4().hex
        response = admin.request(
            "POST",
            path + "/users",
            body={
                "username": username,
                "enabled": True,
                "firstName": "Synthetic",
                "lastName": "Identity",
                "email": username + "@example.invalid",
                "emailVerified": True,
                "credentials": [{"type": "password", "value": password, "temporary": False}],
            },
            expected=(201,),
        )
        user_id = response.headers["location"].rstrip("/").rsplit("/", 1)[1]
        clients = admin.request("GET", path + "/clients").json()
        yield {
            **identity_config,
            "issuer": identity_config["public_url"] + "/realms/" + name,
            "realm": name,
            "client_id": "media-trace-probe",
            "api_secret": api_secret,
            "username": username,
            "password": password,
            "user_id": user_id,
            "admin": admin,
            "admin_path": path,
            "api_id": next(c["id"] for c in clients if c["clientId"] == "media-trace-api"),
            "probe_id": next(c["id"] for c in clients if c["clientId"] == "media-trace-probe"),
        }
    finally:
        try:
            if created:
                admin.request("DELETE", path, expected=(204, 404))
        finally:
            admin.close()


@pytest.fixture
def live_mapping(identity_realm, business_context, tmp_path):
    config, ctx = identity_realm, business_context
    bundle = authorization_code_login(config)
    role, password = "mt_live_lookup_" + uuid4().hex, uuid4().hex + uuid4().hex
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            sql.SQL("CREATE ROLE {} LOGIN NOSUPERUSER NOBYPASSRLS PASSWORD {}").format(
                sql.Identifier(role), sql.Literal(password)
            )
        )
        admin.execute(sql.SQL("GRANT mt_identity_lookup TO {}").format(sql.Identifier(role)))
    manager = Database(ctx["admin_dsn"])
    with manager.engine.begin() as connection:
        identity_id = IdentityDirectory(connection).bind_identity(
            user_id=ctx["actor"].user_id,
            org_id=ctx["actor"].org_id,
            issuer=config["issuer"],
            subject=bundle.subject,
            mapping_version="self-owned-live-fixture-v1",
            enabled=True,
        )
    settings = IntrospectionSettings(
        endpoint=config["issuer"] + "/protocol/openid-connect/token/introspect",
        issuer=config["issuer"],
        audience="media-trace-api",
        client_id="media-trace-api",
        client_secret=config["api_secret"],
        timeout_seconds=2,
        max_response_bytes=65536,
        max_token_bytes=16384,
    )
    runtime = IdentityRuntimeConfig(
        settings,
        Path(config["ca_file"]),
        PrivateValue(make_conninfo(ctx["admin_dsn"], user=role, password=password)),
        ctx["settings"],
    )
    resources = open_identity(runtime)
    try:
        yield config, ctx, bundle, resources, identity_id, runtime
    finally:
        resources.close()
        manager.close()
        with psycopg.connect(ctx["admin_dsn"]) as admin:
            admin.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
            admin.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))
