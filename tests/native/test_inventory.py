"""Read-only native inventory must distinguish project and neighboring services."""

import subprocess

import pytest

from scripts.native.inventory import EXPECTED_NAMES, collect_inventory


@pytest.fixture
def healthy_probes(monkeypatch):
    rows = []
    for index, name in enumerate(sorted(EXPECTED_NAMES)):
        project = "media-trace-identity" if name.startswith("media-trace-identity-") else "media-trace-py310"
        rows.append(f"{index:064x}\t{name}\t{project}")
    rows.append("neighbor-id\tprivate-neighbor-name\tother-project")
    outputs = {"containers": "\n".join(rows), "ports": ""}

    def run(command, **kwargs):
        if "docker" == command[0]:
            output = outputs["containers"]
        elif command[0] == "ss":
            output = outputs["ports"]
        elif command[-1] == "--version":
            output = "Python 3.10.22" if "python" in command[0] else "postgres (PostgreSQL) 16.15"
        else:
            raise AssertionError(command)
        return subprocess.CompletedProcess(command, 0, stdout=output, stderr="")

    monkeypatch.setattr(subprocess, "run", run)
    return outputs


def test_complete_readonly_inventory_excludes_neighbor_names(healthy_probes):
    result = collect_inventory()
    assert result["status"] == "PASS"
    assert len(result["project_containers"]) == 10
    assert result["neighbor_container_count"] == 1
    assert "private-neighbor-name" not in str(result)
    assert result["complete_data_inventory_asserted"] is False


def test_wrong_project_label_does_not_gain_migration_scope(healthy_probes):
    healthy_probes["containers"] = healthy_probes["containers"].replace("\tmedia-trace-py310", "\tother-project")
    assert collect_inventory()["status"] == "FAIL"


def test_staging_port_collision_blocks_preflight(healthy_probes):
    healthy_probes["ports"] = "LISTEN 0 512 127.0.0.1:24200 0.0.0.0:*\n"
    assert collect_inventory()["status"] == "FAIL"


def test_missing_docker_is_reported_without_mutation(monkeypatch):
    calls = []

    def absent(command, **kwargs):
        calls.append(command)
        raise FileNotFoundError("fixture")

    monkeypatch.setattr(subprocess, "run", absent)
    result = collect_inventory()
    assert result["status"] == "FAIL" and result["blockers"]
    assert result["services_changed"] is False
    assert all(not any(word in command for word in ["sudo", "install", "stop", "restart", "rm"]) for command in calls)


def test_inventory_does_not_publish_raw_failure_output(monkeypatch):
    def fail(command, **kwargs):
        return subprocess.CompletedProcess(command, 1, stdout="SECRET_FIXTURE", stderr="SECRET_FIXTURE")

    monkeypatch.setattr(subprocess, "run", fail)
    result = collect_inventory()
    assert "SECRET_FIXTURE" not in str(result)
    assert result["status"] == "FAIL"
