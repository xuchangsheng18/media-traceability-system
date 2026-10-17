"""Explicit real identity test target; never substitutes a mock or skips silently."""

import copy
import json
import os
import secrets
import ssl
from pathlib import Path
from uuid import uuid4

import httpx
import pytest

from tests.business.conftest import business_context as business_context
from tests.business.conftest import business_template as business_template
from tests.business.conftest import database_dsn as database_dsn


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
