"""Private identity operations must preserve keys and reject unsafe targets."""

import importlib
import os

import pytest


def modules():
    common = importlib.import_module("scripts.identity.common")
    assert importlib.util.find_spec("scripts.identity.certificates") is not None, "CERTIFICATE_IMPLEMENTATION_MISSING"
    return common, importlib.import_module("scripts.identity.certificates")


def test_wrong_runtime_root_rejected(tmp_path):
    _, cert = modules()
    with pytest.raises(RuntimeError, match="RUNTIME"):
        cert.prepare(tmp_path / "not-approved")


def test_ca_not_recreated(tmp_path, monkeypatch):
    common, cert = modules()
    runtime = tmp_path / "identity"
    monkeypatch.setattr(common, "RUNTIME", runtime)
    result = cert.prepare(runtime)
    key = (runtime / "pki/ca.key").read_bytes()
    assert cert.prepare(runtime) == result
    assert (runtime / "pki/ca.key").read_bytes() == key
    assert "PRIVATE KEY" not in str(result)
    assert (runtime.stat().st_mode & 0o777) == 0o700
    assert all((p.stat().st_mode & 0o777) == 0o600 for p in (runtime / "pki").iterdir() if p.is_file())


def test_symlink_and_partial_pki_rejected(tmp_path, monkeypatch):
    common, cert = modules()
    runtime = tmp_path / "identity"
    monkeypatch.setattr(common, "RUNTIME", runtime)
    runtime.mkdir(mode=0o700)
    (runtime / "pki").symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(RuntimeError):
        cert.prepare(runtime)
    (runtime / "pki").unlink()
    (runtime / "pki").mkdir(mode=0o700)
    (runtime / "pki/ca.key").write_text("incomplete")
    with pytest.raises(RuntimeError, match="INCOMPLETE"):
        cert.prepare(runtime)


def test_broad_runtime_permissions_rejected(tmp_path, monkeypatch):
    common, cert = modules()
    runtime = tmp_path / "identity"
    monkeypatch.setattr(common, "RUNTIME", runtime)
    runtime.mkdir()
    os.chmod(runtime, 0o755)
    with pytest.raises(RuntimeError, match="PERMISSION"):
        cert.prepare(runtime)


def test_secret_volume_verifies_content():
    assert importlib.util.find_spec("scripts.identity.volumes") is not None, "VOLUME_VERIFIER_MISSING"
    module = importlib.import_module("scripts.identity.volumes")
    expected = {"ca.crt": "a" * 64, "tls.key": "b" * 64}
    module.verify_volume_contents(dict(expected), expected)
    for actual in ({}, {"ca.crt": "a" * 64}, {**expected, "tls.key": "c" * 64}, {**expected, "other": "d" * 64}):
        with pytest.raises(RuntimeError, match="VOLUME"):
            module.verify_volume_contents(actual, expected)


def test_bootstrap_service_uses_no_human_password_grant(tmp_path, monkeypatch):
    common, _ = modules()
    control = importlib.import_module("scripts.identity.control")
    runtime = tmp_path / "identity"
    monkeypatch.setattr(common, "RUNTIME", runtime)
    monkeypatch.setattr(control, "prepare", lambda _: {})
    monkeypatch.setattr(control, "install", lambda _: {})
    control.prepare_configuration()
    config = runtime / "keycloak-v2.conf"
    assert config.is_file(), "SERVICE_BOOTSTRAP_CONFIGURATION_MISSING"
    value = config.read_text()
    assert "bootstrap-admin-client-id=bootstrap-project-service" in value
    assert "bootstrap-admin-client-secret=" in value
    assert "bootstrap-admin-username" not in value and "bootstrap-admin-password" not in value


def test_realm_policy_exact_and_no_password_grant():
    import json
    from pathlib import Path

    path = Path(__file__).resolve().parents[2] / "config/identity/realm.template.json"
    assert path.is_file(), "REALM_TEMPLATE_MISSING"
    data = json.loads(path.read_text())
    assert data["accessTokenLifespan"] == 300
    assert data["ssoSessionIdleTimeout"] == 1800
    assert data["ssoSessionMaxLifespan"] == 28800
    assert data["revokeRefreshToken"] is True and data["refreshTokenMaxReuse"] == 0
    assert data["registrationAllowed"] is False and data["rememberMe"] is False
    for c in data["clients"]:
        assert c["directAccessGrantsEnabled"] is False and c["implicitFlowEnabled"] is False
        assert "*" not in str(c["redirectUris"])


def test_provision_refuses_unapproved_overwrite():
    assert importlib.util.find_spec("scripts.identity.provision") is not None, "REALM_PROVISION_MISSING"
    module = importlib.import_module("scripts.identity.provision")
    with pytest.raises(RuntimeError, match="DIFFERS"):
        module.validate_existing({"registrationAllowed": True}, {"registrationAllowed": False})
    module.validate_existing({"registrationAllowed": False, "id": "server-field"}, {"registrationAllowed": False})


def test_verify_rejects_missing_acceptance_evidence():
    assert importlib.util.find_spec("scripts.identity.verify") is not None, "ACCEPTANCE_AGGREGATOR_MISSING"
    module = importlib.import_module("scripts.identity.verify")
    report = module.evaluate({})
    assert report["status"] == "NOT_COMPLETE" and len(report["checks"]) == 22
    assert all(c["status"] == "NOT_EXECUTED" for c in report["checks"])
    with pytest.raises(RuntimeError, match="EVIDENCE"):
        module.evaluate({"IDP-01": {"status": "PASS"}})


def test_oidc_probe_rejects_unapproved_target():
    assert importlib.util.find_spec("tools.identity_oidc_probe") is not None, "LIVE_OIDC_PROBE_MISSING"
    module = importlib.import_module("tools.identity_oidc_probe")
    with pytest.raises(RuntimeError, match="CONFIGURATION"):
        module.validate_probe_config({"issuer": "http://attacker.invalid"})


def test_keycloak_server_default_attributes_do_not_override_required_pkce():
    module = importlib.import_module("scripts.identity.provision")
    expected = {"attributes": {"pkce.code.challenge.method": "S256"}}
    actual = {"attributes": {"pkce.code.challenge.method": "S256", "realm_client": "false"}}
    module.validate_existing(actual, expected)
    with pytest.raises(RuntimeError, match="DIFFERS"):
        module.validate_existing({"attributes": {"pkce.code.challenge.method": "plain"}}, expected)


@pytest.fixture
def recovery_key(tmp_path):
    import subprocess

    home = tmp_path / "gpg-home"
    home.mkdir(mode=0o700)
    base = ["gpg", "--homedir", str(home), "--batch", "--pinentry-mode", "loopback", "--passphrase", ""]
    subprocess.run(
        [*base, "--quick-generate-key", "Synthetic recovery <self-owned@example.invalid>", "rsa2048", "sign", "1d"],
        capture_output=True,
        check=True,
    )
    listing = subprocess.check_output([*base, "--with-colons", "--list-keys"], stderr=subprocess.DEVNULL).decode()
    fingerprint = next(line.split(":")[9] for line in listing.splitlines() if line.startswith("fpr:"))
    subprocess.run([*base, "--quick-add-key", fingerprint, "rsa2048", "encr", "1d"], capture_output=True, check=True)
    public = tmp_path / "recipient.asc"
    public.write_bytes(subprocess.check_output([*base, "--armor", "--export", fingerprint]))
    try:
        yield home, public, fingerprint
    finally:
        subprocess.run(["gpgconf", "--homedir", str(home), "--kill", "gpg-agent"], capture_output=True)


def test_backup_has_no_plaintext_artifact(tmp_path, recovery_key):
    import io

    assert importlib.util.find_spec("scripts.identity.backup") is not None, "ENCRYPTED_BACKUP_MISSING"
    module = importlib.import_module("scripts.identity.backup")
    home, recipient, fingerprint = recovery_key
    destination = tmp_path / "synthetic.dump.gpg"
    data = b"self-owned-plain-dump-fixture"
    report = module.encrypt_stream(io.BytesIO(data), destination, recipient, home, fingerprint)
    assert destination.is_file() and destination.stat().st_mode & 0o777 == 0o600
    assert data not in destination.read_bytes()
    assert report["encrypted"] is True and report["signed"] is True
    assert not list(tmp_path.glob("*.partial"))
    with pytest.raises(RuntimeError):
        module.encrypt_stream(io.BytesIO(data), destination, recipient, home, fingerprint)


def test_restore_refuses_original_volume():
    assert importlib.util.find_spec("scripts.identity.restore") is not None, "ISOLATED_RESTORE_MISSING"
    module = importlib.import_module("scripts.identity.restore")
    for project in ("media-trace-identity", "media-trace-py310", "../restore", "unrelated"):
        with pytest.raises(RuntimeError, match="RESTORE"):
            module.validate_restore_target(project, set())
    module.validate_restore_target("media-trace-identity-restore", set())
    with pytest.raises(RuntimeError, match="RESTORE"):
        module.validate_restore_target("media-trace-identity-restore", {"media-trace-identity-restore"})


def test_restore_container_gets_graceful_shutdown_window(monkeypatch):
    module = importlib.import_module("scripts.identity.restore")
    calls = []
    monkeypatch.setattr(module.common, "docker", lambda *args: calls.append(args))
    module.stop_restore_container("media-trace-identity-restore-1234abcd-postgres")
    assert calls == [("stop", "--time", "60", "media-trace-identity-restore-1234abcd-postgres")]


def test_corrupt_or_missing_key_fails_closed(tmp_path, recovery_key):
    import io

    assert importlib.util.find_spec("scripts.identity.restore") is not None, "ISOLATED_RESTORE_MISSING"
    backup = importlib.import_module("scripts.identity.backup")
    restore = importlib.import_module("scripts.identity.restore")
    home, recipient, fingerprint = recovery_key
    path = tmp_path / "synthetic.dump.gpg"
    backup.encrypt_stream(io.BytesIO(b"self-owned-dump"), path, recipient, home, fingerprint)
    restore.verify_encrypted(path, home, fingerprint)
    empty = tmp_path / "empty-key-home"
    empty.mkdir(mode=0o700)
    with pytest.raises(RuntimeError, match="RESTORE"):
        restore.verify_encrypted(path, empty, fingerprint)
    content = bytearray(path.read_bytes())
    content[len(content) // 2] ^= 1
    path.write_bytes(content)
    with pytest.raises(RuntimeError, match="RESTORE"):
        restore.verify_encrypted(path, home, fingerprint)
