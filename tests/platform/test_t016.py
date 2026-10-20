"""One-use credentials are bound to explicit rules and never implicit approval."""

import importlib
import importlib.util
from dataclasses import replace
from datetime import datetime, timezone
from typing import Any, cast
from uuid import UUID

import pytest
from business_app.contracts import validate_api
from business_app.errors import BusinessError
from business_app.types import Actor, Scope


def api():
    name = "business_app.controls.operation_tokens"
    assert importlib.util.find_spec(name) is not None, "T016_OPERATION_TOKEN_CAPABILITY_REQUIRED"
    return importlib.import_module(name)


@pytest.mark.parametrize("ttl", [True, 0, -1, 1.5, None, "60"])
def test_invalid_token_ttl_does_not_become_a_successful_rule(ttl):
    module = api()
    with pytest.raises(ValueError):
        module.OperationTokenRule("sealEvidence", "self-owned-rule-1", ttl)


@pytest.mark.parametrize("action", ["", "sealEvidence,createReport", "rolloutModel", "exportAudit", None])
def test_ambiguous_or_unimplemented_actions_cannot_be_signed(action):
    module = api()
    with pytest.raises(ValueError):
        module.OperationTokenRule(action, "self-owned-rule-1", 60)


@pytest.mark.parametrize("key", [b"", b"short", "not-bytes", bytearray(b"x" * 32), None])
def test_invalid_key_material_is_rejected_before_derivation(key):
    module = api()
    with pytest.raises(ValueError):
        module.OperationTokenKey("self-owned-key-1", key)


def test_secret_material_is_not_exposed_by_repr():
    module = api()
    key = module.OperationTokenKey("self-owned-key-1", b"self-owned-test-secret-material-32")
    assert "self-owned-test-secret-material-32" not in repr(key)


@pytest.mark.parametrize("defect", ["unknown", "model", "purpose", "organization", "missing_rule"])
def test_only_the_explicit_case_task_seal_mapping_can_resolve(defect):
    module = api()
    assert hasattr(module, "resolve_rule"), "T016_EXPLICIT_CASE_ACTION_RULE_REQUIRED"
    scope = Scope(Actor(UUID(int=4), UUID(int=2)), UUID(int=3))
    approval = dict(object_type="task", purpose="seal", policy_version="self-owned-approval-1")

    class Rules:
        def resolve(self, scope, approval):
            return module.OperationTokenRule("sealEvidence", "self-owned-rule-1", 60)

    provider: Any = Rules()
    if defect == "unknown":
        approval["object_type"] = "unknown"
    elif defect == "model":
        approval.update(object_type="model_release", purpose="model_release")
    elif defect == "purpose":
        approval["purpose"] = "report_export"
    elif defect == "organization":
        scope = Scope(scope.actor, cast(Any, None))
    else:
        provider = None
    with pytest.raises(BusinessError):
        module.resolve_rule(provider, scope, approval)


def binding(module):
    return {
        "token_id": UUID(int=1),
        "org_id": UUID(int=2),
        "case_id": UUID(int=3),
        "actor_id": UUID(int=4),
        "approval_id": UUID(int=5),
        "approval_version": 3,
        "object_type": "task",
        "object_id": UUID(int=6),
        "object_version": 2,
        "purpose": "seal",
        "action": "sealEvidence",
        "approval_policy_version": "self-owned-approval-1",
        "permission_policy_version": "self-owned-permission-1",
        "rule_version": "self-owned-rule-1",
        "recovery_generation": "self-owned-generation-1",
        "key_id": "self-owned-key-1",
        "principal_sha256": "a" * 64,
        "request_sha256": "b" * 64,
        "idempotency_key": "self-owned-request-1",
        "storage_version": 1,
        "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "expires_at": datetime(2026, 1, 1, 0, 1, tzinfo=timezone.utc),
    }


def test_credential_is_reconstructable_but_hash_and_identifier_are_not_credentials():
    module = api()
    key = module.OperationTokenKey("self-owned-key-1", b"self-owned-test-secret-material-32")
    item = binding(module)
    first = module.derive_token(item, key)
    assert first == "mtop1.00000000000000000000000000000001.E-kfRvmXCTw-BdqAlZZKeubAsCLF9PRgcQ79k5sbSyA"
    assert first == module.derive_token(dict(item), key)
    assert first.startswith("mtop1.00000000000000000000000000000001.") and len(first) == 82
    assert module.token_identifier(first) == item["token_id"]
    for bad in (str(item["token_id"]), "a" * 64, first + "=", first.replace("mtop1.", "mtop2.")):
        with pytest.raises(BusinessError):
            module.token_identifier(bad)
    assert module.derive_token(dict(item, action="createReport"), key) != first
    assert module.derive_token(dict(item, recovery_generation="self-owned-generation-2"), key) != first
    assert module.derive_token(dict(item, approval_version=4), key) != first
    assert module.derive_token(item, replace(key, material=b"another-self-owned-test-key-00000")) != first


@pytest.mark.parametrize("field", ["case_id", "actor_id", "action", "approved"])
def test_client_cannot_add_scope_action_or_approval_claims(field):
    body = dict(approval_id=str(UUID(int=5)), object_id=str(UUID(int=6)), object_version=2, purpose="seal")
    with pytest.raises(BusinessError):
        validate_api("OperationTokenRequest", dict(body, **{field: "not-authority"}))


def test_case_issuance_and_same_transaction_consumption_capability():
    import importlib

    module = importlib.import_module("business_app.controls.operation_tokens")
    assert hasattr(module, "OperationTokens"), "T016_CASE_ISSUANCE_AND_CONSUMPTION_REQUIRED"


def test_credential_response_formatter_forbids_http_caching(monkeypatch):
    """Formatter-only harness; production authorization is covered separately."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    router_module = importlib.import_module("business_app.controls.router")
    scope = Scope(Actor(UUID(int=1), UUID(int=2)), UUID(int=3))

    class SyntheticFormatterOnlyService:
        def issue(self, current, body, request, key):
            assert current == scope and key == "self-owned-formatter-only"
            return dict(
                operation_token="synthetic-response-formatter-only",
                expires_at="2099-01-01T00:00:00+00:00",
                object_version=1,
            )

    monkeypatch.setattr(router_module, "resource_scope", lambda *args: scope)
    app = FastAPI()
    app.state.operation_tokens = SyntheticFormatterOnlyService()
    app.include_router(router_module.router)
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/operation-tokens",
            headers={"Idempotency-Key": "self-owned-formatter-only"},
            json=dict(approval_id=str(UUID(int=4)), object_id=str(UUID(int=5)), object_version=1, purpose="seal"),
        )
    assert response.status_code == 200
    assert response.headers.get("Cache-Control") == "no-store"
