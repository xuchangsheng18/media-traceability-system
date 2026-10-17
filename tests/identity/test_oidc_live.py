"""Actual Keycloak signatures, PKCE and revocation; no mocked authority responses."""

import ssl
import time
from dataclasses import replace

import pytest
from business_app.errors import BusinessError
from business_app.identity.tokens import IntrospectionSettings, IntrospectionVerifier

from tools.identity_oidc_probe import authorization_code_login, client, exchange, introspect, obtain_code


def verifier(config):
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
    return IntrospectionVerifier(settings, ssl_context=ssl.create_default_context(cafile=config["ca_file"]))


def test_real_browser_pkce_signature_and_binding(identity_realm):
    config = identity_realm
    bundle = authorization_code_login(config)
    checker = verifier(config)
    try:
        verified = checker.verify(bundle.access_token)
        assert verified.subject == config["user_id"]
        with pytest.raises(BusinessError):
            checker.verify(bundle.id_token)
        prefix, signature = bundle.access_token.rsplit(".", 1)
        forged = prefix + "." + ("B" if signature[0] != "B" else "A") + signature[1:]
        with pytest.raises(BusinessError):
            checker.verify(forged)
        for change in ({"issuer": "https://wrong.invalid"}, {"audience": "wrong-audience"}):
            wrong = IntrospectionVerifier(
                replace(checker.settings, **change), ssl_context=ssl.create_default_context(cafile=config["ca_file"])
            )
            try:
                with pytest.raises(BusinessError):
                    wrong.verify(bundle.access_token)
            finally:
                wrong.close()
    finally:
        checker.close()


def test_wrong_pkce_and_authorization_code_replay_rejected(identity_realm):
    config = identity_realm
    code = obtain_code(config)
    with pytest.raises(RuntimeError, match="PROTOCOL"):
        exchange(config, code, verifier_override="A" * 64)
    fresh = obtain_code(config)
    exchange(config, fresh)
    with pytest.raises(RuntimeError, match="PROTOCOL"):
        exchange(config, fresh)


def test_password_grant_is_disabled_with_valid_fixture_credentials(identity_realm):
    config = identity_realm
    with client(config) as http:
        response = http.post(
            config["issuer"] + "/protocol/openid-connect/token",
            data={
                "grant_type": "password",
                "client_id": config["client_id"],
                "username": config["username"],
                "password": config["password"],
            },
        )
        assert response.status_code == 400
        assert response.json().get("error") == "unauthorized_client"


@pytest.mark.parametrize("operation", ["disable_user", "terminate_sessions", "revoke_refresh", "logout"])
def test_actual_revocation_rejected_within_ten_seconds(identity_realm, operation):
    config = identity_realm
    bundle = authorization_code_login(config)
    assert introspect(config, bundle.access_token).get("active") is True
    start = time.monotonic()
    if operation == "disable_user":
        config["admin"].request(
            "PUT", config["admin_path"] + "/users/" + config["user_id"], body={"enabled": False}, expected=(204,)
        )
    elif operation == "terminate_sessions":
        config["admin"].request(
            "POST", config["admin_path"] + "/users/" + config["user_id"] + "/logout", expected=(204,)
        )
    else:
        with client(config) as http:
            if operation == "revoke_refresh":
                response = http.post(
                    config["issuer"] + "/protocol/openid-connect/revoke",
                    data={
                        "client_id": config["client_id"],
                        "token": bundle.refresh_token,
                        "token_type_hint": "refresh_token",
                    },
                )
                assert response.status_code == 200
            else:
                response = http.post(
                    config["issuer"] + "/protocol/openid-connect/logout",
                    data={"client_id": config["client_id"], "refresh_token": bundle.refresh_token},
                )
                assert response.status_code in {200, 204}
    while time.monotonic() - start < 10:
        if introspect(config, bundle.access_token).get("active") is False:
            return
        time.sleep(0.1)
    pytest.fail("LIVE_REVOCATION_EXCEEDED_TEN_SECONDS")


def test_actual_expired_token_rejected(identity_realm):
    config = identity_realm
    config["admin"].request(
        "PUT",
        config["admin_path"] + "/clients/" + config["probe_id"],
        body={"attributes": {"pkce.code.challenge.method": "S256", "access.token.lifespan": "3"}},
        expected=(204,),
    )
    bundle = authorization_code_login(config)
    checker = verifier(config)
    try:
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            try:
                checker.verify(bundle.access_token)
            except BusinessError as error:
                assert error.http_status == 401
                return
            time.sleep(0.1)
        pytest.fail("REAL_EXPIRED_TOKEN_WAS_ACCEPTED")
    finally:
        checker.close()


def test_client_secret_rotation_revokes_old_secret(identity_realm):
    config = identity_realm
    bundle = authorization_code_login(config)
    rotated = (
        config["admin"]
        .request("POST", config["admin_path"] + "/clients/" + config["api_id"] + "/client-secret")
        .json()["value"]
    )
    with pytest.raises(RuntimeError, match="PROTOCOL"):
        introspect(config, bundle.access_token)
    assert introspect({**config, "api_secret": rotated}, bundle.access_token).get("active") is True
