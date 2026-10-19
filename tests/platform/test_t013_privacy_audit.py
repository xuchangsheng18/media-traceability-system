"""Credential review must detect real material without echoing it to reports."""

import importlib
import importlib.util
import subprocess


def scanner():
    assert importlib.util.find_spec("scripts.identity.privacy") is not None, "IDENTITY_HISTORY_PRIVACY_AUDIT_MISSING"
    return importlib.import_module("scripts.identity.privacy").scan_bytes


def test_known_credential_and_token_are_detected_without_rendering_value():
    secret = b"self-owned-private-credential-" + b"q" * 32
    jwt = b"eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJzeW50aGV0aWMifQ." + b"k" * 64
    findings = scanner()(b"prefix\n" + secret + b"\n" + jwt, (secret,))
    assert {f["rule"] for f in findings} == {"known_private_value", "jwt_material"}
    assert [f["line"] for f in findings] == [2, 3]
    assert secret.decode() not in str(findings) and jwt.decode() not in str(findings)


def test_private_key_block_is_detected_but_key_creation_source_is_not():
    scan = scanner()
    label = b"PRIVATE KEY"
    material = b"-----BEGIN " + label + b"-----\n" + b"Q" * 128 + b"\n-----END " + label + b"-----"
    assert scan(material, ()) == [{"rule": "private_key_material", "line": 1}]
    assert scan(b'openssl("req", "-newkey", "rsa:3072", "-keyout", str(private_path))', ()) == []


def test_short_marker_empty_input_and_redacted_values_are_not_credentials():
    scan = scanner()
    assert scan(b"", ()) == []
    assert scan(b"token=<redacted> client_secret=*** PRIVATE KEY", (b"x", b"")) == []


def test_history_review_finds_credential_removed_from_current_files(tmp_path):
    scanner()
    module = importlib.import_module("scripts.identity.privacy")

    def git(*args):
        return subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True)

    git("init", "--quiet")
    git("config", "user.name", "Synthetic Review")
    git("config", "user.email", "synthetic@example.invalid")
    secret = b"self-owned-history-credential-" + b"r" * 32
    path = tmp_path / "removed.txt"
    path.write_bytes(secret)
    git("add", "removed.txt")
    git("commit", "--quiet", "-m", "self-owned fixture")
    path.write_bytes(b"redacted")
    git("add", "removed.txt")
    git("commit", "--quiet", "-m", "remove fixture credential")
    report = module.audit_history(tmp_path, (secret,))
    assert report["reachable_blobs"] == 2
    assert report["status"] == "FINDINGS_REQUIRE_REVIEW"
    assert len(report["findings"]) == 1
    assert report["findings"][0]["findings"] == [{"rule": "known_private_value", "line": 1}]
    assert secret.decode() not in str(report)
