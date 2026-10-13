import importlib.util
import json
import os
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
