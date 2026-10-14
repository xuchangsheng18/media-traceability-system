import importlib.util
import json
import os
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("development_tasks", ROOT / "scripts/dev.py")
dev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dev)


def test_unknown_command_is_rejected():
    with pytest.raises(SystemExit) as failure:
        dev.main(["delete-all"])
    assert failure.value.code == 2


def test_dry_run_never_executes_or_validates_external_stack(monkeypatch, capsys):
    monkeypatch.setattr(dev.subprocess, "run", lambda *a, **k: pytest.fail("dry run executed command"))
    assert dev.main(["integration-test", "--dry-run"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["executed"] is False and result["status"] == "PLAN_ONLY"


def test_failed_check_stops_subsequent_commands(monkeypatch):
    calls = []
    monkeypatch.setattr(dev, "python", lambda: __import__("sys").executable)
    monkeypatch.setattr(dev, "plan", lambda name: [["first"], ["must-not-run"]])

    def fail(command, **kwargs):
        calls.append(command)
        return type("Result", (), {"returncode": 42})()

    monkeypatch.setattr(dev.subprocess, "run", fail)
    assert dev.main(["test"]) == 42
    assert calls == [["first"]]


def test_clean_allowlist_never_includes_data_or_source(tmp_path):
    for name in [".pytest_cache", ".ruff_cache", "data", "weights", ".git", "backend"]:
        (tmp_path / name).mkdir()
    assert {path.name for path in dev.clean_paths(tmp_path)} == {".pytest_cache", ".ruff_cache"}


def test_clean_symlink_escape_is_rejected(tmp_path):
    outside = tmp_path.parent / (tmp_path.name + "-outside")
    outside.mkdir()
    try:
        (tmp_path / ".pytest_cache").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("host lacks symlink creation permission; CI Linux exercises this")
    with pytest.raises(RuntimeError, match="UNSAFE_CLEAN_TARGET"):
        dev.clean_paths(tmp_path)


def test_clean_dry_run_preserves_cache_and_original(tmp_path, monkeypatch, capsys):
    cache = tmp_path / ".pytest_cache"
    cache.mkdir()
    original = tmp_path / "data"
    original.mkdir()
    monkeypatch.setattr(dev, "ROOT", tmp_path)
    monkeypatch.setattr(dev, "clean_paths", lambda: [cache])
    assert dev.main(["clean"]) == 0
    assert cache.exists() and original.exists()
    assert json.loads(capsys.readouterr().out)["volumes_or_business_data_removed"] is False


def test_shared_host_build_requires_explicit_flag(monkeypatch):
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    with pytest.raises(RuntimeError, match="EXPLICIT_COMMAND_FLAG"):
        dev.stack_change_guard(False)


def test_existing_development_stack_is_only_observed_by_default():
    assert dev.plan("dev") == []
    assert dev.plan("stop")[0][-1] == "down"
    assert not any("--volumes" in command or "-v" in command for command in dev.plan("stop"))


def test_command_profile_keeps_exact_development_version():
    assert dev.PROFILE["python_executable"] == "/opt/conda/glwy/envs/py310/bin/python"
    assert dev.PROFILE["production_release_or_formal_data_access"] is False
    assert not dev.PROFILE["formal_approval_refs"]


def test_environment_uses_explicit_runtime_and_preserves_custom_node_path(monkeypatch):
    monkeypatch.setenv("MT_NODE_BIN", "/synthetic/node/bin")
    env = dev.environment()
    assert env["PATH"].split(os.pathsep)[:2] == [str(Path(dev.python()).parent), "/synthetic/node/bin"]
    assert env["PYTHONDONTWRITEBYTECODE"] == "1"


def hosted_environment(monkeypatch, tmp_path):
    workspace = tmp_path / "checkout"
    temporary = tmp_path / "runner-temp"
    monkeypatch.setattr(dev, "ROOT", workspace)
    for key, value in {
        "GITHUB_ACTIONS": "true",
        "RUNNER_ENVIRONMENT": "github-hosted",
        "GITHUB_WORKSPACE": str(workspace),
        "RUNNER_TEMP": str(temporary),
        "MT_RUNTIME_DIR": str(temporary / "runtime"),
        "MT_DOCKER_CONTEXT": "default",
    }.items():
        monkeypatch.setenv(key, value)
    monkeypatch.delenv("DOCKER_HOST", raising=False)


def test_hosted_runner_still_requires_explicit_stack_flag(monkeypatch, tmp_path):
    hosted_environment(monkeypatch, tmp_path)
    assert dev.isolated_ci_workspace()
    with pytest.raises(RuntimeError, match="EXPLICIT_COMMAND_FLAG"):
        dev.stack_change_guard(False)
    dev.stack_change_guard(True)


@pytest.mark.parametrize(
    "key,value",
    [
        ("RUNNER_ENVIRONMENT", "self-hosted"),
        ("GITHUB_WORKSPACE", "/workspace/glwy/projects/media-traceability-system"),
        ("MT_RUNTIME_DIR", "/workspace/glwy/runtime/media-traceability-system"),
        ("MT_RUNTIME_DIR", "/different-runtime"),
        ("RUNNER_TEMP", "relative"),
        ("MT_DOCKER_CONTEXT", "desktop-linux"),
        ("DOCKER_HOST", "tcp://other-daemon:2375"),
    ],
)
def test_ci_label_cannot_skip_shared_capacity_check(monkeypatch, tmp_path, key, value):
    hosted_environment(monkeypatch, tmp_path)
    monkeypatch.setenv(key, value)
    assert not dev.isolated_ci_workspace()
    monkeypatch.setitem(
        sys.modules,
        "poc_control",
        types.SimpleNamespace(
            compose=lambda *a, **k: types.SimpleNamespace(
                stdout="Filesystem 1B Used Available Use% Mounted\n/dev/data 100 99 1 99% /data\n"
            )
        ),
    )
    with pytest.raises(RuntimeError, match="CAPACITY_BELOW"):
        dev.stack_change_guard(True)


@pytest.mark.parametrize("output", ["", "df failed", "/dev/data 100 0 unknown 0% /data"])
def test_unreadable_capacity_stops_stack_action(monkeypatch, output):
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.setitem(
        sys.modules, "poc_control", types.SimpleNamespace(compose=lambda *a, **k: types.SimpleNamespace(stdout=output))
    )
    with pytest.raises(RuntimeError, match="CAPACITY_UNREADABLE"):
        dev.stack_change_guard(True)


def test_exact_capacity_threshold_allows_explicit_action(monkeypatch):
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    minimum = dev.PROFILE["minimum_free_bytes_before_stack_changes"]
    monkeypatch.setitem(
        sys.modules,
        "poc_control",
        types.SimpleNamespace(
            compose=lambda *a, **k: types.SimpleNamespace(stdout=f"/dev/data 9999999999 0 {minimum} 0% /data")
        ),
    )
    dev.stack_change_guard(True)


def test_wrong_service_set_is_not_reported_healthy(monkeypatch, capsys):
    rows = [{"Service": "api", "State": "running", "Health": "healthy"}] * 7
    monkeypatch.setitem(
        sys.modules,
        "poc_control",
        types.SimpleNamespace(
            compose=lambda *a, **k: types.SimpleNamespace(stdout="\n".join(json.dumps(row) for row in rows))
        ),
    )
    assert dev.status() == 1
    assert json.loads(capsys.readouterr().out)["status"] == "NOT_READY"


def quality_module():
    quality_spec = importlib.util.spec_from_file_location("quality_checks", ROOT / "scripts/stage_three_quality.py")
    module = importlib.util.module_from_spec(quality_spec)
    quality_spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "raw",
    [
        None,
        [],
        {},
        {"metadata": {}},
        {"error": {}, "headers": {"set-cookie": "private-example"}},
        {"metadata": {"vulnerabilities": {"high": 0, "critical": 0}}},
    ],
)
def test_failed_or_empty_audit_is_not_zero_vulnerabilities_and_does_not_publish_headers(raw):
    normalized, failed = quality_module().normalize_npm_report(raw)
    assert failed and "error" in normalized
    assert "private-example" not in json.dumps(normalized)


def test_complete_npm_report_keeps_all_severity_counts_and_drops_headers():
    report = {
        "auditReportVersion": 2,
        "vulnerabilities": {},
        "metadata": {
            "vulnerabilities": {"info": 0, "low": 0, "moderate": 0, "high": 0, "critical": 0, "total": 0},
            "dependencies": {"total": 123},
        },
        "headers": {"set-cookie": "private-example"},
    }
    normalized, failed = quality_module().normalize_npm_report(report)
    assert not failed and normalized["metadata"]["vulnerabilities"]["total"] == 0
    assert normalized["metadata"]["dependencies"]["total"] == 123
    assert "headers" not in normalized
