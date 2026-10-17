"""Explicit identity runtime ownership, TLS enforcement and private file loading."""

import importlib
import json
import ssl
from unittest.mock import Mock

import pytest
from business_app.db import Database
from business_app.identity.tokens import IntrospectionSettings, IntrospectionVerifier


def settings():
    return IntrospectionSettings(
        endpoint="https://identity.example.test/introspect",
        issuer="https://identity.example.test",
        audience="identity-config-test",
        client_id="config-test",
        client_secret="self-owned-test-secret",
        timeout_seconds=2,
        max_response_bytes=2048,
        max_token_bytes=128,
    )


def config_module():
    assert importlib.util.find_spec("business_app.identity.config") is not None, "IDENTITY_CONFIG_MISSING"
    return importlib.import_module("business_app.identity.config")


def test_ca_validation_cannot_be_disabled():
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    with pytest.raises(ValueError, match="TLS"):
        IntrospectionVerifier(settings(), ssl_context=context)


def test_config_permission_and_unknown_fields_rejected(tmp_path):
    module = config_module()
    path = tmp_path / "identity.json"
    path.write_text(json.dumps({"unknown": "must-not-pass"}))
    path.chmod(0o644)
    with pytest.raises(RuntimeError, match="CONFIGURATION"):
        module.load_private_config(path)
    path.chmod(0o600)
    with pytest.raises(RuntimeError, match="CONFIGURATION"):
        module.load_private_config(path)


def test_partial_open_closes_resources(monkeypatch):
    assert importlib.util.find_spec("business_app.identity.runtime") is not None, "IDENTITY_RUNTIME_MISSING"
    module = importlib.import_module("business_app.identity.runtime")
    verifier = Mock()
    monkeypatch.setattr(module, "IntrospectionVerifier", Mock(return_value=verifier))
    monkeypatch.setattr(module, "Database", Mock(side_effect=RuntimeError("DB_UNAVAILABLE")))
    monkeypatch.setattr(module.ssl, "create_default_context", Mock(return_value=ssl.create_default_context()))
    config = Mock(introspection=settings(), ca_file="unused", lookup_dsn="unused")
    with pytest.raises(RuntimeError, match="INITIALIZATION"):
        module.open_identity(config)
    verifier.close.assert_called_once()


def test_entrypoint_is_explicit_and_closes_once():
    assert importlib.util.find_spec("business_app.identity.entrypoint") is not None, "IDENTITY_ENTRYPOINT_MISSING"
    runtime = importlib.import_module("business_app.identity.runtime")
    verifier, lookup = Mock(), Mock()
    resource = runtime.IdentityResources(verifier, lookup)
    resource.close()
    resource.close()
    verifier.close.assert_called_once()
    lookup.close.assert_called_once()


@pytest.mark.parametrize(
    "kwargs",
    [
        {"connect_timeout_seconds": 0},
        {"statement_timeout_ms": -1},
        {"pool_timeout_seconds": float("inf")},
        {"connect_timeout_seconds": True},
    ],
)
def test_database_timeouts_are_bounded(kwargs):
    with pytest.raises(ValueError, match="TIMEOUT"):
        Database("host=localhost dbname=mt_business_test user=unused", **kwargs)
