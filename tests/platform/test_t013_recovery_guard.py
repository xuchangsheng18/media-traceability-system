"""Recovery must quarantine stale identity state without changing a live realm."""

import importlib
import importlib.util
from types import SimpleNamespace

import pytest


def implementation():
    assert importlib.util.find_spec("scripts.identity.reconcile") is not None, "RESTORE_RECONCILIATION_MISSING"
    return importlib.import_module("scripts.identity.reconcile")


@pytest.mark.parametrize("realm", ["master", "media-trace", "../media-trace", "media-trace-acceptance-"])
def test_reconciliation_refuses_shared_or_malformed_realm(realm):
    module = implementation()
    with pytest.raises(RuntimeError, match="ISOLATED"):
        module.reconcile(None, realm=realm, expected_realm_id="fixture", client_id="media-trace-api")


def test_reconciliation_checks_realm_identity_before_mutation():
    module = implementation()

    class WrongRealm:
        def request(self, method, path, **kwargs):
            assert method == "GET"
            return SimpleNamespace(json=lambda: {"id": "different", "realm": "media-trace-acceptance-" + "a" * 32})

    with pytest.raises(RuntimeError, match="IDENTITY"):
        module.reconcile(
            WrongRealm(),
            realm="media-trace-acceptance-" + "a" * 32,
            expected_realm_id="expected",
            client_id="media-trace-api",
        )


def test_private_reconciliation_result_does_not_render_secret():
    module = implementation()
    result = module.Reconciliation("self-owned-test-secret", 123, 2)
    assert "self-owned-test-secret" not in repr(result)
    assert result.public_report() == {
        "sessions_cleared": True,
        "not_before": 123,
        "retired_signing_providers": 2,
        "client_secret_rotated": True,
        "public_cutover": False,
        "formal_accepted": False,
    }


@pytest.mark.parametrize("failure", ["timeout", "missing_client"])
def test_verified_restored_realm_is_quarantined_before_client_discovery(failure):
    module = implementation()
    realm = "media-trace-acceptance-" + "b" * 32
    state = {"id": "confirmed-fixture", "realm": realm, "enabled": True}

    class ClientDiscoveryFailure:
        def request(self, method, path, **kwargs):
            if method == "GET" and path == "/admin/realms/" + realm:
                return SimpleNamespace(json=lambda: dict(state))
            if method == "PUT" and path == "/admin/realms/" + realm:
                state.update(kwargs["body"])
                return SimpleNamespace()
            if method == "GET" and path.endswith("/clients"):
                if failure == "timeout":
                    raise RuntimeError("SELF_OWNED_CLIENT_DISCOVERY_TIMEOUT")
                return SimpleNamespace(json=lambda: [])
            raise AssertionError("UNEXPECTED_RECONCILIATION_OPERATION")

    with pytest.raises(RuntimeError):
        module.reconcile(
            ClientDiscoveryFailure(), realm=realm, expected_realm_id="confirmed-fixture", client_id="media-trace-api"
        )
    assert state["enabled"] is False
