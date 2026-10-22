"""Real isolated restart/restore/rollback; no shared service lifecycle action."""

import time
from uuid import uuid4

import pytest
from business_app.errors import BusinessError

from tests.identity import recovery_lab as recovery_fixtures
from tests.platform import test_t013_identity_operations as operation_fixtures
from tools.identity_oidc_probe import PrivateValue

recovery_lab = recovery_fixtures.recovery_lab
recovery_key = operation_fixtures.recovery_key


def test_restart_and_database_dependency_readiness(recovery_lab):
    lab = recovery_lab
    lab.seed()
    before = lab.snapshot()
    token = lab.login()
    lab.assert_exact_business_mapping(token["access_token"])
    lab.restart()
    assert lab.snapshot() == before, "RECOVERY_LAB_READINESS_RESTART_SNAPSHOT_CHANGED"
    assert lab.introspect(token["access_token"])["active"] is True, "RECOVERY_LAB_READINESS_RESTART_SESSION_INACTIVE"
    try:
        lab.compose("stop", "identity-postgres")
        lab.wait_dependency_down()
        assert lab.readiness()["status"] == "DOWN", "RECOVERY_LAB_READINESS_DATABASE_STATE_NOT_DOWN"
        marker = "self-owned-fault-query-" + uuid4().hex
        lab.private_values.append(marker)
        with lab.http() as http:
            response = http.get(
                lab.issuer + "/.well-known/openid-configuration", params={"code": marker, "token": marker}
            )
        assert response.status_code >= 500 and marker not in response.text, (
            "RECOVERY_LAB_READINESS_DISCOVERY_FAILURE_BOUNDARY"
        )
        with pytest.raises(BusinessError) as failure:
            lab.verify(token["access_token"])
        assert failure.value.http_status == 503, "RECOVERY_LAB_READINESS_VERIFIER_STATUS_NOT_503"
    finally:
        lab.compose("start", "identity-postgres")
        lab.wait_ready()
    assert lab.snapshot() == before, "RECOVERY_LAB_READINESS_RECOVERED_SNAPSHOT_CHANGED"
    assert lab.verify(token["access_token"]).subject == lab.user_id, "RECOVERY_LAB_READINESS_RECOVERED_SUBJECT_CHANGED"
    lab.assert_exact_business_mapping(token["access_token"])
    lab.record("restart_persistence_and_dependency_readiness", state_persistent=True, database_failure_denied=True)


def test_encrypted_restore_reconciles_old_sessions_keys_and_rollback(recovery_lab, recovery_key):
    from scripts.identity.reconcile import reconcile

    lab = recovery_lab
    lab.seed()
    token = lab.login()
    before = lab.snapshot()
    lab.assert_exact_business_mapping(token["access_token"])
    old_secret = lab.api_secret
    backup = lab.backup(recovery_key)
    # The backup deliberately precedes revocation and a newer client secret.
    lab.revoke_sessions()
    original_current_secret = lab.rotate_secret()
    assert lab.introspect(token["access_token"])["active"] is False
    original_volume = lab.data_volume
    original_snapshot = lab.snapshot()
    started = time.monotonic()
    lab.restore(backup, recovery_key)
    assert lab.data_volume != original_volume
    assert lab.snapshot() == before
    lab.api_secret = old_secret
    # Positive control: a stale backup can revive the formerly revoked token.
    assert lab.introspect(token["access_token"])["active"] is True

    class RefuseClientDiscovery:
        def request(self, method, path, **kwargs):
            if method == "GET" and path.endswith("/clients"):
                raise RuntimeError("SELF_OWNED_CLIENT_DISCOVERY_FAILURE")
            return lab.admin.request(method, path, **kwargs)

    with pytest.raises(RuntimeError, match="SELF_OWNED_CLIENT_DISCOVERY_FAILURE"):
        reconcile(RefuseClientDiscovery(), realm=lab.realm, expected_realm_id=lab.realm_id, client_id="media-trace-api")
    assert lab.admin.request("GET", lab.admin_path).json()["enabled"] is False
    with pytest.raises(BusinessError):
        lab.verify(token["access_token"])

    class RefuseSecretRotation:
        def request(self, method, path, **kwargs):
            if method == "POST" and path.endswith("/client-secret"):
                raise RuntimeError("SELF_OWNED_RECOVERY_OPERATION_FAILURE")
            return lab.admin.request(method, path, **kwargs)

    with pytest.raises(RuntimeError, match="SELF_OWNED_RECOVERY_OPERATION_FAILURE"):
        reconcile(RefuseSecretRotation(), realm=lab.realm, expected_realm_id=lab.realm_id, client_id="media-trace-api")
    assert lab.admin.request("GET", lab.admin_path).json()["enabled"] is False
    with pytest.raises(BusinessError):
        lab.verify(token["access_token"])
    result = reconcile(lab.admin, realm=lab.realm, expected_realm_id=lab.realm_id, client_id="media-trace-api")
    lab.api_secret = PrivateValue(result.client_secret)
    lab.private_values.append(lab.api_secret)
    assert lab.introspect(token["access_token"])["active"] is False
    assert lab.introspect_status(token["access_token"], old_secret) == 401
    assert lab.refresh_status(token["refresh_token"]) == 400
    assert set(before["signing_kids"]).isdisjoint(lab.snapshot()["signing_kids"])
    fresh = lab.login()
    assert lab.verify(fresh["access_token"]).subject == lab.user_id
    lab.assert_exact_business_mapping(fresh["access_token"])
    lab.restart()
    assert lab.introspect(token["access_token"])["active"] is False
    assert lab.introspect_status(fresh["access_token"], old_secret) == 401
    assert lab.verify(fresh["access_token"]).subject == lab.user_id
    restored_volume = lab.data_volume
    rollback_result = lab.rollback()
    assert lab.data_volume == original_volume
    after_rollback = lab.snapshot()
    for key in ["realm_id", "user_id", "user_enabled", "clients"]:
        assert after_rollback[key] == original_snapshot[key]
    assert set(original_snapshot["signing_kids"]).isdisjoint(after_rollback["signing_kids"])
    assert lab.introspect(token["access_token"])["active"] is False
    assert lab.introspect_status(fresh["access_token"], result.client_secret) == 401
    assert lab.introspect_status(fresh["access_token"], original_current_secret) == 401
    rollback_fresh = lab.login()
    assert lab.verify(rollback_fresh["access_token"]).subject == lab.user_id
    lab.assert_exact_business_mapping(rollback_fresh["access_token"])
    lab.record(
        "restore_session_key_invalidation_and_rollback",
        **result.public_report(),
        stale_backup_token_revival_positive_control=True,
        old_token_denied=True,
        old_refresh_denied=True,
        old_secret_denied=True,
        exact_mapping_verified=True,
        restore_elapsed_seconds=round(time.monotonic() - started, 3),
        separate_data_volumes=original_volume != restored_volume,
        original_volume_retained=True,
        failed_reconciliation_left_realm_disabled=True,
        failed_client_discovery_left_realm_disabled=True,
        rollback_reconciliation=rollback_result.public_report(),
    )
