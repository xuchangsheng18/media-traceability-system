"""Native installation must fail closed before any administrator action."""

import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from scripts.native.artifacts import validate_artifacts


@pytest.mark.parametrize(
    "result_code,status,expected",
    [
        (
            0,
            "[GNUPG:] VALIDSIG D6786CE303D9A9022998DC6CC8464D549AF75C0A 2026-10-02 1 0 4 0 1 8 00 D6786CE303D9A9022998DC6CC8464D549AF75C0A",
            True,
        ),
        (1, "", False),
        (0, "[GNUPG:] GOODSIG not-validsig", False),
        (0, "[GNUPG:] VALIDSIG " + "A" * 40 + " date 1 0 4 0 1 8 00 " + "A" * 40, False),
    ],
)
def test_nginx_signature_requires_success_and_pinned_signer(tmp_path, monkeypatch, result_code, status, expected):
    from scripts.native.artifacts import verify_nginx_signature

    calls = []

    def run(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(
            returncode=0 if "--import" in command else result_code, stdout="" if "--import" in command else status
        )

    monkeypatch.setattr("scripts.native.artifacts.subprocess.run", run)
    assert verify_nginx_signature(tmp_path / "package", tmp_path / "sig", tmp_path / "key") is expected
    assert all("--no-options" in c and "--no-auto-key-retrieve" in c and "--homedir" in c for c in calls)


@pytest.mark.parametrize("bad_status", ["EXPKEYSIG", "EXPSIG", "REVKEYSIG"])
def test_nginx_expired_or_revoked_signatures_are_rejected(tmp_path, monkeypatch, bad_status):
    from scripts.native.artifacts import verify_nginx_signature

    valid = "[GNUPG:] VALIDSIG D6786CE303D9A9022998DC6CC8464D549AF75C0A 2026-10-02 1 0 4 0 1 8 00 D6786CE303D9A9022998DC6CC8464D549AF75C0A"
    monkeypatch.setattr(
        "scripts.native.artifacts.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout=valid + "\n[GNUPG:] " + bad_status + " signer"),
    )
    assert verify_nginx_signature(tmp_path / "package", tmp_path / "sig", tmp_path / "key") is False


@pytest.mark.parametrize("tamper", ["old_package_url", "old_signature_url", "old_package_filename"])
def test_nginx_signed_archive_must_match_exact_pinned_release(verified_lock, monkeypatch, tamper):
    lock, root = verified_lock
    item = next(x for x in lock["artifacts"] if x["component"] == "nginx")
    raw = (root / item["filename"]).read_bytes()
    item["filename"] = "nginx-1.30.6.tar.gz"
    (root / item["filename"]).write_bytes(raw)
    item["url"] = "https://nginx.org/download/nginx-1.30.6.tar.gz"
    (root / "signature.asc").write_bytes(b"synthetic-signature")
    (root / "key.asc").write_bytes(b"synthetic-public-key")
    item["provenance"] = {
        "method": "official_openpgp",
        "url": item["url"] + ".asc",
        "filename": "signature.asc",
        "sha256": hashlib.sha256(b"synthetic-signature").hexdigest(),
        "key_url": "https://nginx.org/keys/pluknet.key",
        "key_filename": "key.asc",
        "key_sha256": hashlib.sha256(b"synthetic-public-key").hexdigest(),
    }
    monkeypatch.setattr("scripts.native.artifacts.verify_nginx_signature", lambda *args: True)
    assert validate_artifacts(lock, root)["status"] == "PASS"
    if tamper == "old_package_url":
        item["url"] = "https://nginx.org/download/nginx-1.30.5.tar.gz"
    elif tamper == "old_signature_url":
        item["provenance"]["url"] = "https://nginx.org/download/nginx-1.30.5.tar.gz.asc"
    else:
        item["filename"] = "nginx-1.30.5.tar.gz"
        (root / item["filename"]).write_bytes(raw)
    assert validate_artifacts(lock, root)["status"] == "FAIL"


VERSIONS = {
    "python": "3.10.22",
    "node": "22.21.1",
    "postgres": "16.15",
    "rabbitmq": "4.3.6",
    "erlang": "27.3.4.18",
    "seaweedfs": "4.48",
    "keycloak": "26.8.1",
    "java": "21.0.12.1",
    "nginx": "1.30.6",
    "age": "1.1.1",
}
SOURCES = {
    "python": "https://github.com/conda-forge/miniforge/",
    "node": "https://nodejs.org/dist/",
    "postgres": "https://ftp.postgresql.org/pub/source/",
    "rabbitmq": "https://github.com/rabbitmq/rabbitmq-server/",
    "erlang": "https://github.com/erlang/otp/",
    "seaweedfs": "https://github.com/seaweedfs/seaweedfs/",
    "keycloak": "https://github.com/keycloak/keycloak/",
    "java": "https://github.com/adoptium/temurin21-binaries/",
    "nginx": "https://nginx.org/download/",
    "age": "https://github.com/FiloSottile/age/",
}


@pytest.fixture
def verified_lock(tmp_path):
    # Self-owned bytes and checksum fixtures; no real downloaded package is asserted.
    items = []
    for name, version in VERSIONS.items():
        path = name + ".tar.gz"
        data = ("synthetic-" + name).encode()
        (tmp_path / path).write_bytes(data)
        digest = hashlib.sha256(data).hexdigest()
        evidence = name + ".sha256"
        checksum = f"{digest}  {path}\n".encode()
        (tmp_path / evidence).write_bytes(checksum)
        items.append(
            {
                "component": name,
                "version": version,
                "architecture": "amd64",
                "filename": path,
                "sha256": digest,
                "url": SOURCES[name] + path,
                "license": "Synthetic-test-only",
                "dependencies": ["erlang"] if name == "rabbitmq" else [],
                "provenance": {
                    "method": "official_sha256",
                    "url": SOURCES[name] + evidence,
                    "filename": evidence,
                    "sha256": hashlib.sha256(checksum).hexdigest(),
                },
            }
        )
    return {"schema_version": 1, "architecture": "amd64", "artifacts": items}, tmp_path


def test_complete_verified_package_set_can_pass(verified_lock):
    lock, root = verified_lock
    report = validate_artifacts(lock, root)
    assert report["status"] == "PASS" and report["blockers"] == []
    assert report["installation_performed"] is False


@pytest.mark.parametrize("component,version", [("erlang", "27.3.4.13"), ("nginx", "1.29.2")])
def test_confirmed_exact_native_versions_cannot_be_downgraded(verified_lock, component, version):
    lock, root = verified_lock
    next(item for item in lock["artifacts"] if item["component"] == component)["version"] = version
    assert validate_artifacts(lock, root)["status"] == "FAIL"


def test_official_conda_python_package_binds_build_and_digest(verified_lock):
    lock, root = verified_lock
    item = next(x for x in lock["artifacts"] if x["component"] == "python")
    item["url"] = "https://conda.anaconda.org/conda-forge/linux-64/" + item["filename"]
    item["provenance"]["method"] = "conda_release_api"
    item["provenance"]["url"] = "https://api.anaconda.org/release/conda-forge/python/3.10.22"
    data = {
        "distributions": [{"basename": "linux-64/" + item["filename"], "version": "3.10.22", "sha256": item["sha256"]}],
    }
    p = root / item["provenance"]["filename"]
    raw = json.dumps(data).encode()
    p.write_bytes(raw)
    item["provenance"]["sha256"] = hashlib.sha256(raw).hexdigest()
    assert validate_artifacts(lock, root)["status"] == "PASS"
    data["distributions"][0]["basename"] = "osx-64/" + item["filename"]
    raw = json.dumps(data).encode()
    p.write_bytes(raw)
    item["provenance"]["sha256"] = hashlib.sha256(raw).hexdigest()
    assert validate_artifacts(lock, root)["status"] == "FAIL"


@pytest.mark.parametrize(
    "change",
    [
        "missing_digest",
        "tampered_bytes",
        "wrong_architecture",
        "path_escape",
        "untrusted_source",
        "missing_component",
        "duplicate_component",
        "old_broker",
        "old_erlang",
        "missing_provenance",
        "self_computed_only",
        "tampered_checksum",
        "wrong_checksum_line",
        "missing_dependency",
        "cycle",
        "missing_license",
    ],
)
def test_invalid_installation_inputs_fail_closed(verified_lock, change):
    lock, root = verified_lock
    item = lock["artifacts"][0]
    if change == "missing_digest":
        item["sha256"] = None
    elif change == "tampered_bytes":
        (root / item["filename"]).write_bytes(b"changed")
    elif change == "wrong_architecture":
        item["architecture"] = "arm64"
    elif change == "path_escape":
        item["filename"] = "../outside"
    elif change == "untrusted_source":
        item["url"] = "https://github.com.evil.invalid/package.tar.gz"
    elif change == "missing_component":
        lock["artifacts"].pop()
    elif change == "duplicate_component":
        lock["artifacts"].append(copy.deepcopy(item))
    elif change == "old_broker":
        next(x for x in lock["artifacts"] if x["component"] == "rabbitmq")["version"] = "3.12.1"
    elif change == "old_erlang":
        next(x for x in lock["artifacts"] if x["component"] == "erlang")["version"] = "25.3.2.8"
    elif change == "missing_provenance":
        item.pop("provenance")
    elif change == "self_computed_only":
        item["provenance"]["method"] = "self_computed"
    elif change in {"tampered_checksum", "wrong_checksum_line"}:
        evidence = root / item["provenance"]["filename"]
        evidence.write_bytes(b"unrelated checksum\n")
        if change == "wrong_checksum_line":
            item["provenance"]["sha256"] = hashlib.sha256(evidence.read_bytes()).hexdigest()
    elif change == "missing_dependency":
        item["dependencies"] = ["not-in-lock"]
    elif change == "cycle":
        next(x for x in lock["artifacts"] if x["component"] == "erlang")["dependencies"] = ["rabbitmq"]
    else:
        item["license"] = ""
    report = validate_artifacts(lock, root)
    assert report["status"] == "FAIL" and report["blockers"]
    assert report["installation_performed"] is False


def test_missing_artifact_directory_does_not_get_created(verified_lock):
    lock, root = verified_lock
    target = root / "missing"
    assert validate_artifacts(lock, target)["status"] == "FAIL"
    assert not target.exists()


@pytest.mark.parametrize(
    "tamper", [None, "wrong_tag", "wrong_tag_type", "wrong_digest", "wrong_repository", "api_path_escape"]
)
def test_official_release_api_binds_version_asset_and_bytes(verified_lock, tamper):
    lock, root = verified_lock
    item = next(x for x in lock["artifacts"] if x["component"] == "rabbitmq")
    metadata: dict[str, Any] = {
        "tag_name": "v4.3.6",
        "assets": [
            {"name": item["filename"], "digest": "sha256:" + item["sha256"], "browser_download_url": item["url"]}
        ],
    }
    url = "https://api.github.com/repos/rabbitmq/rabbitmq-server/releases/tags/v4.3.6"
    if tamper == "wrong_tag":
        metadata["tag_name"] = "v3.12.1"
    elif tamper == "wrong_tag_type":
        metadata["tag_name"] = None
    elif tamper == "wrong_digest":
        metadata["assets"][0]["digest"] = "sha256:" + "0" * 64
    elif tamper == "wrong_repository":
        url = "https://api.github.com/repos/other-owner/rabbitmq-server/releases/tags/v4.3.6"
    elif tamper == "api_path_escape":
        url = "https://api.github.com/repos/rabbitmq/rabbitmq-server/releases/../../../other-owner/releases/1"
    data = json.dumps(metadata).encode()
    (root / "release.json").write_bytes(data)
    item["provenance"] = {
        "method": "github_release_api",
        "url": url,
        "filename": "release.json",
        "sha256": hashlib.sha256(data).hexdigest(),
    }
    result = validate_artifacts(lock, root)
    assert result["status"] == ("PASS" if tamper is None else "FAIL")


def test_cli_missing_inputs_returns_nonzero_without_installing(tmp_path):
    lock = tmp_path / "lock.json"
    lock.write_text(json.dumps({"schema_version": 1, "architecture": "amd64", "artifacts": []}))
    result = subprocess.run(
        [sys.executable, "scripts/native/artifacts.py", "verify", "--lock", str(lock), "--root", str(tmp_path)],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert json.loads(result.stdout)["status"] == "FAIL"


@pytest.mark.parametrize("component,tag", [("erlang", "OTP-27.3.4.18"), ("java", "jdk-21.0.12.1")])
def test_component_specific_official_release_tags(verified_lock, component, tag):
    lock, root = verified_lock
    item = next(x for x in lock["artifacts"] if x["component"] == component)
    metadata = {
        "tag_name": tag,
        "assets": [
            {"name": item["filename"], "digest": "sha256:" + item["sha256"], "browser_download_url": item["url"]}
        ],
    }
    raw = json.dumps(metadata).encode()
    (root / "release.json").write_bytes(raw)
    item["provenance"] = {
        "method": "github_release_api",
        "url": SOURCES[component].replace("https://github.com/", "https://api.github.com/repos/") + "releases/123",
        "filename": "release.json",
        "sha256": hashlib.sha256(raw).hexdigest(),
    }
    assert validate_artifacts(lock, root)["status"] == "PASS"
    metadata["tag_name"] = "v" + item["version"]
    raw = json.dumps(metadata).encode()
    (root / "release.json").write_bytes(raw)
    item["provenance"]["sha256"] = hashlib.sha256(raw).hexdigest()
    assert validate_artifacts(lock, root)["status"] == "FAIL"
