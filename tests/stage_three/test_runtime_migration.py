"""The selected environment must be the authorized, security-patched runtime."""

import importlib.metadata
import platform
import sys
from pathlib import Path

import yaml
from packaging.specifiers import SpecifierSet


def test_running_environment_matches_authorized_python311_baseline():
    root = Path(__file__).resolve().parents[2]
    versions = yaml.safe_load((root / "config/versions.yaml").read_text())
    assert sys.version_info[:3] == (3, 11, 17)
    assert platform.python_version() == versions["python"]["version"] == "3.11.17"
    assert Path(sys.prefix).resolve() == Path(versions["python"]["prefix"]).resolve()
    assert versions["python"]["full_lock"] == "config/locks/requirements-py311.lock"
    import tomllib

    project = tomllib.loads((root / "backend/pyproject.toml").read_text())["project"]
    assert platform.python_version() in SpecifierSet(project["requires-python"])
    assert importlib.metadata.version("Pillow") == versions["media"]["pillow"] == "13.0.0"
    assert importlib.metadata.version("certifi") == "2026.10.19"


def test_actual_runtime_artifacts_have_verified_official_origin_chain():
    import hashlib
    import json
    from urllib.parse import urlsplit

    root = Path(__file__).resolve().parents[2]
    record = json.loads((root / "docs/00-project/validation/python311-artifact-inventory.json").read_text())
    assert (
        record["runtime_lock_sha256"]
        == hashlib.sha256((root / "config/locks/requirements-py311.lock").read_bytes()).hexdigest()
    )
    assert len(record["wheels"]) == record["official_origin_verified_wheel_count"] == 100
    assert len(record["conda_packages"]) == record["official_origin_verified_conda_count"] == 26
    for row in record["wheels"] + record["conda_packages"]:
        artifact = urlsplit(row["url"])
        metadata = urlsplit(row["official_metadata_url"])
        assert artifact.scheme == metadata.scheme == "https"
        assert artifact.hostname in {
            "files.pythonhosted.org",
            "download.pytorch.org",
            "download-r2.pytorch.org",
            "conda.anaconda.org",
        }
        assert metadata.hostname in {"pypi.org", "download.pytorch.org", "api.anaconda.org"}
        assert artifact.username is None and artifact.password is None
        assert row["publisher_sha256"] == row["sha256"]
        assert len(row["official_metadata_sha256"]) == 64
        assert row["origin_verification"] in {
            "PUBLISHER_METADATA_SHA256_MATCHES_ACTUAL_WHEEL",
            "PUBLISHER_METADATA_SHA256_MATCHES_INSTALLED_PACKAGE_RECORD",
            "OFFICIAL_ARTIFACT_BYTES_SHA256_MATCHES_INSTALLED_PACKAGE_RECORD",
        }


def test_active_operator_commands_select_the_supported_interpreter():
    root = Path(__file__).resolve().parents[2]
    for name in [
        "CONTRIBUTING.md",
        "docs/10-deployment/development-runbook.md",
        "docs/10-deployment/business-development-runbook.md",
    ]:
        text = (root / name).read_text()
        assert "/opt/conda/glwy/envs/py311/bin/python" in text, name
        assert "/opt/conda/glwy/envs/py310/bin/python" not in text, name
    for name in [
        "docs/03-development/t034-development-configuration.md",
        "docs/03-development/t034-material-structure-receipt.md",
    ]:
        text = (root / name).read_text()
        assert "linux-py311-cpu-internal-rnd" in text, name
        assert "linux-py310-cpu-internal-rnd" not in text, name
