"""Identity preflight must fail closed without mutating Docker."""

import copy
import importlib
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
import yaml


def preflight():
    assert importlib.util.find_spec("scripts.identity") is not None, "IDENTITY_PREFLIGHT_PACKAGE_MISSING"
    return importlib.import_module("scripts.identity.preflight")


def snapshot():
    return {
        "platform": "linux",
        "architecture": "x86_64",
        "python": "3.11.17",
        "docker_context": "desktop-linux",
        "docker_server_version": "29.8.2",
        "host_available_bytes": 100 * 1024**3,
        "vm_available_bytes": 100 * 1024**3,
        "occupied_ports": [],
        "services": {s: "healthy" for s in ("api", "inference", "postgres", "rabbitmq", "s3", "web", "worker")},
        "time_synchronized": True,
    }


@pytest.mark.parametrize("port", [18443, 18444])
def test_preflight_rejects_port_collision(port):
    value = snapshot()
    value["occupied_ports"] = [port]
    assert "IDENTITY_PORT_IN_USE" in preflight().validate(value)


def test_vm_space_is_not_host_space():
    value = snapshot()
    value["vm_available_bytes"] = 5368709120
    assert "VM_CAPACITY_INSUFFICIENT" in preflight().validate(value)
    value["vm_available_bytes"] = 30 * 1024**3
    assert "VM_CAPACITY_INSUFFICIENT" in preflight().validate(value), "needs 20GiB database plus restore and images"


def test_valid_preflight_and_missing_observations():
    module = preflight()
    assert module.validate(snapshot()) == []
    for field in snapshot():
        value = snapshot()
        del value[field]
        assert module.validate(value), field


def test_preflight_validation_is_pure():
    value = snapshot()
    before = copy.deepcopy(value)
    with patch("subprocess.run", side_effect=AssertionError("MUTATING_OR_EXTERNAL_CALL")):
        assert preflight().validate(value) == []
    assert value == before


@pytest.mark.parametrize(
    "field,value",
    [
        ("vm_available_bytes", True),
        ("occupied_ports", ""),
        ("time_synchronized", False),
        ("services", {}),
        ("docker_context", "default"),
    ],
)
def test_invalid_preflight_fields_fail_closed(field, value):
    record = snapshot()
    record[field] = value
    assert preflight().validate(record)


def test_compose_isolates_secrets_ports_and_resources():
    root = Path(__file__).resolve().parents[2]
    target = root / "deploy/identity/compose.yaml"
    assert target.is_file(), "IDENTITY_COMPOSE_MISSING"
    config = yaml.safe_load(target.read_text())
    assert config["name"] == "media-trace-identity"
    services = config["services"]
    assert set(services) == {"identity-gateway", "keycloak", "identity-postgres"}
    assert services["identity-gateway"]["ports"] == ["172.16.58.179:18443:8443", "127.0.0.1:18444:8444"]
    assert "ports" not in services["keycloak"] and "ports" not in services["identity-postgres"]
    assert sum(float(s["cpus"]) for s in services.values()) == 3
    assert [services[s]["mem_limit"] for s in ("keycloak", "identity-postgres", "identity-gateway")] == [
        "3g",
        "2g",
        "1g",
    ]
    assert "secrets" not in str(config.get("environment", {}))
    assert "start-dev" not in target.read_text() and ":latest" not in target.read_text()
    assert services["identity-gateway"]["read_only"] is True


def test_control_requires_apply(monkeypatch):
    assert importlib.util.find_spec("scripts.identity.control") is not None, "IDENTITY_CONTROL_MISSING"
    module = importlib.import_module("scripts.identity.control")
    with patch("subprocess.run", side_effect=AssertionError("EXTERNAL_CALL")):
        report = module.preview("up")
    assert report["applied"] is False and report["project"] == "media-trace-identity"


def test_control_rejects_unscanned_images():
    module = importlib.import_module("scripts.identity.control")
    assert hasattr(module, "check_image_admission"), "IMAGE_SCAN_GUARD_MISSING"
    for status in (None, "NOT_EXECUTED", {"status": "FAIL"}, {"status": "PASS_NO_HIGH_OR_CRITICAL", "high": 1}):
        with pytest.raises(RuntimeError, match="SCAN"):
            module.check_image_admission({"security_scan": status})


def test_postgres_candidate_removes_vulnerable_bookworm_toolchain():
    import json

    root = Path(__file__).resolve().parents[2]
    versions = json.loads((root / "config/identity/versions.json").read_text())
    pg = versions["images"]["postgres"]
    assert pg["version"] == "16.15-alpine3.24", "VULNERABLE_POSTGRES_VARIANT_STILL_SELECTED"
    assert pg["runtime_uid"] == 70
    assert pg["reference"] in (root / "deploy/identity/Dockerfile.postgres").read_text()


def test_runtime_postgres_has_no_go_privilege_helper_and_runs_nonroot():
    root = Path(__file__).resolve().parents[2]
    dockerfile = (root / "deploy/identity/Dockerfile.postgres").read_text()
    assert "USER 70:70" in dockerfile, "RUNTIME_POSTGRES_STILL_STARTS_AS_ROOT"
    assert "rm /usr/local/bin/gosu /usr/local/bin/su-exec" in dockerfile


def test_control_rejects_runtime_image_drift():
    module = importlib.import_module("scripts.identity.control")
    assert hasattr(module, "check_runtime_image_ids"), "RUNTIME_IMAGE_DRIFT_GUARD_MISSING"
    expected = {k: "sha256:" + "a" * 64 for k in ("keycloak", "postgres", "nginx")}
    module.check_runtime_image_ids(expected, dict(expected))
    with pytest.raises(RuntimeError, match="IMAGE"):
        module.check_runtime_image_ids(expected, {**expected, "postgres": "sha256:" + "b" * 64})
    with pytest.raises(RuntimeError, match="IMAGE"):
        module.check_runtime_image_ids({}, {})


def test_gateway_readonly_root_has_writable_cache():
    root = Path(__file__).resolve().parents[2]
    gateway = yaml.safe_load((root / "deploy/identity/compose.yaml").read_text())["services"]["identity-gateway"]
    assert gateway["read_only"] is True
    assert any(p.startswith("/var/cache/nginx:") for p in gateway["tmpfs"]), "READONLY_NGINX_CACHE_NOT_MOUNTED"


def test_owned_port_recognition_does_not_allow_foreign_bindings():
    module = importlib.import_module("scripts.identity.control")
    assert hasattr(module, "owned_ports_from_inspect"), "OWNED_PORT_GUARD_MISSING"
    value: Any = {
        "Config": {
            "Labels": {
                "com.docker.compose.project": "media-trace-identity",
                "com.docker.compose.service": "identity-gateway",
            }
        },
        "State": {"Running": True},
        "NetworkSettings": {
            "Ports": {
                "8443/tcp": [{"HostIp": "172.16.58.179", "HostPort": "18443"}],
                "8444/tcp": [{"HostIp": "127.0.0.1", "HostPort": "18444"}],
            }
        },
    }
    assert module.owned_ports_from_inspect([value]) == {18443, 18444}
    value["Config"]["Labels"]["com.docker.compose.project"] = "foreign"
    assert module.owned_ports_from_inspect([value]) == set()


def test_oidc_web_identity_uses_minimal_basic_scope():
    import json

    root = Path(__file__).resolve().parents[2]
    realm = json.loads((root / "config/identity/realm.template.json").read_text())
    web = next(c for c in realm["clients"] if c["clientId"] == "media-trace-web")
    assert web["defaultClientScopes"] == ["basic"], "STABLE_SUBJECT_CLAIM_SCOPE_MISSING"
