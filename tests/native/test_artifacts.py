"""Native installation must fail closed before any administrator action."""

import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from scripts.native.artifacts import validate_artifacts

VERSIONS = {
    "python": "3.10.22",
    "node": "22.21.1",
    "postgres": "16.15",
    "rabbitmq": "4.3.6",
    "erlang": "27.3.4.13",
    "seaweedfs": "4.48",
    "keycloak": "26.8.1",
    "java": "21.0.12.1",
    "nginx": "1.29.2",
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


@pytest.mark.parametrize("tamper", [None, "wrong_tag", "wrong_tag_type", "wrong_digest", "wrong_repository"])
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
