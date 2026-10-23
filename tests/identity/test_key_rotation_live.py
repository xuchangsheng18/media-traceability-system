"""Rotate only a disposable realm; inspect public JWKS, never private keys."""

import base64
import json
import ssl
from dataclasses import replace

import pytest
from business_app.errors import BusinessError
from business_app.identity.tokens import IntrospectionVerifier

from tests.identity.test_oidc_live import verifier
from tools.identity_oidc_probe import PrivateValue, authorization_code_login, client, json_request


def key_id(token):
    # Inspection only: the actual issuer/introspection verifies the signature.
    header = token.split(".", 1)[0]
    return json.loads(base64.b64decode(header + "=" * (-len(header) % 4), altchars=b"-_", validate=True))["kid"]


def test_signing_rotation_preserves_old_key_until_explicit_retirement(identity_realm):
    config = identity_realm
    assert config["realm"].startswith("media-trace-acceptance-")
    original = authorization_code_login(config)
    old_kid = key_id(original.access_token)
    checker = verifier(config)
    try:
        assert checker.verify(original.access_token).subject == config["user_id"]
        with client(config) as http:
            discovery = json_request(http, "GET", config["issuer"] + "/.well-known/openid-configuration")
            assert discovery["issuer"] == config["issuer"]
            assert discovery["jwks_uri"] == config["issuer"] + "/protocol/openid-connect/certs"
        metadata = config["admin"].request("GET", config["admin_path"] + "/keys").json()
        old_provider = next(k["providerId"] for k in metadata["keys"] if k["kid"] == old_kid)
        realm_id = config["admin"].request("GET", config["admin_path"]).json()["id"]
        config["admin"].request(
            "POST",
            config["admin_path"] + "/components",
            expected=(201,),
            body={
                "name": "synthetic-rotation-key",
                "parentId": realm_id,
                "providerType": "org.keycloak.keys.KeyProvider",
                "providerId": "rsa-generated",
                "config": {"priority": ["10000"], "enabled": ["true"], "active": ["true"], "keySize": ["2048"]},
            },
        )
        rotated = authorization_code_login(config)
        new_kid = key_id(rotated.access_token)
        assert new_kid != old_kid
        with client(config) as http:
            keys = json_request(http, "GET", discovery["jwks_uri"])["keys"]
        assert {old_kid, new_kid} <= {k["kid"] for k in keys}
        assert checker.verify(original.access_token).subject == config["user_id"]
        assert checker.verify(rotated.access_token).subject == config["user_id"]
        # Removing the retired provider is explicit, within this test realm only.
        config["admin"].request("DELETE", config["admin_path"] + "/components/" + old_provider, expected=(204,))
        with pytest.raises(BusinessError) as failure:
            checker.verify(original.access_token)
        assert failure.value.http_status == 401
        assert checker.verify(rotated.access_token).subject == config["user_id"]
    finally:
        checker.close()


def test_client_secret_rotation_denies_the_old_adapter(identity_realm):
    config = identity_realm
    token = authorization_code_login(config)
    old = verifier(config)
    new = None
    try:
        assert old.verify(token.access_token).subject == config["user_id"]
        secret = PrivateValue(
            config["admin"]
            .request("POST", config["admin_path"] + "/clients/" + config["api_id"] + "/client-secret")
            .json()["value"]
        )
        new = IntrospectionVerifier(
            replace(old.settings, client_secret=secret),
            ssl_context=ssl.create_default_context(cafile=config["ca_file"]),
        )
        with pytest.raises(BusinessError) as failure:
            old.verify(token.access_token)
        assert failure.value.http_status == 503
        assert str(failure.value) == "IDENTITY_AUTHORITY_UNAVAILABLE"
        assert new.verify(token.access_token).subject == config["user_id"]
    finally:
        old.close()
        if new is not None:
            new.close()
