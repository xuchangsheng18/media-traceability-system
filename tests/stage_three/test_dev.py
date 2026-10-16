import importlib.util
import json
import os
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("development_tasks", ROOT / "scripts/dev.py")
assert spec is not None and spec.loader is not None
dev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dev)


@pytest.mark.parametrize("command,read_only", [("pre-commit", True), ("lint", False)])
def test_only_precommit_disables_report_writes_without_disabling_checks(monkeypatch, command, read_only):
    monkeypatch.setenv("MT_PYTHON", sys.executable)
    monkeypatch.delenv("MT_TYPE_REPORT_DISABLED", raising=False)
    monkeypatch.delenv("MT_QUALITY_REPORT_DISABLED", raising=False)
    calls = []

    def run(arguments, **kwargs):
        calls.append((arguments, kwargs["env"]))
        return types.SimpleNamespace(returncode=0)

    monkeypatch.setattr(dev.subprocess, "run", run)
    assert dev.main([command]) == 0
    assert calls and any("secrets" in args for args, _ in calls) == read_only
    assert any("scripts/stage_three_types.py" in args for args, _ in calls)
    assert all((env.get("MT_TYPE_REPORT_DISABLED") == "1") == read_only for _, env in calls)
    assert all((env.get("MT_QUALITY_REPORT_DISABLED") == "1") == read_only for _, env in calls)


@pytest.mark.parametrize("unsafe", [False, True])
def test_read_only_secret_check_still_rejects_prohibited_files(monkeypatch, tmp_path, unsafe):
    script_dir = str(ROOT / "scripts")
    monkeypatch.syspath_prepend(script_dir)
    import stage_three_quality as quality

    monkeypatch.setattr(quality, "ROOT", tmp_path)
    monkeypatch.setattr(quality, "VALIDATION", tmp_path)
    monkeypatch.setattr(quality, "RUNTIME", tmp_path / "private-runtime")
    name = "credentials.json" if unsafe else "source.txt"
    (tmp_path / name).write_text("self-owned-nonsecret-fixture", encoding="utf-8")
    monkeypatch.setattr(quality, "tracked_files", lambda: [name])
    monkeypatch.setenv("MT_QUALITY_REPORT_DISABLED", "1")
    assert quality.secret_check() == int(unsafe)
    assert not (tmp_path / "stage-three-secrets-report.json").exists()


@pytest.mark.parametrize("known", [True, False])
def test_stage_capacity_text_uses_timestamped_snapshot_or_unknown(monkeypatch, known):
    script_dir = str(ROOT / "scripts")
    monkeypatch.syspath_prepend(script_dir)
    import generate_stage_three_docs as generation

    original = generation.read
    receipt = (
        {
            "foundation_capacity_observation": {
                "used_percent": "78%",
                "available_bytes": 12 * 1024**3,
                "observed_at": "synthetic-observation-2040",
            },
        }
        if known
        else {}
    )
    monkeypatch.setattr(
        generation,
        "read",
        lambda name: receipt if name.endswith("resource-readiness-snapshot.json") else original(name),
    )
    combined = "\n".join(generation.build().values())
    if known:
        assert "78%" in combined and "12GiB" in combined and "synthetic-observation-2040" in combined
    else:
        assert "容量未知" in combined
    assert "复查13%" not in combined and "观测使用率13%" not in combined


@pytest.mark.parametrize("conflict", ["custom_hook", "core_hooks_path", "missing_tool"])
def test_hook_installation_refuses_unsafe_or_incomplete_setup(monkeypatch, tmp_path, conflict):
    quality_spec = importlib.util.spec_from_file_location("hook_quality", ROOT / "scripts/stage_three_quality.py")
    assert quality_spec is not None and quality_spec.loader is not None
    quality = importlib.util.module_from_spec(quality_spec)
    quality_spec.loader.exec_module(quality)
    installer = getattr(quality, "install_hook", None)
    assert callable(installer), "safe hook installer is missing"
    monkeypatch.setattr(quality, "ROOT", tmp_path)
    monkeypatch.setattr(quality, "RUNTIME", tmp_path / "private-runtime")
    monkeypatch.setattr(quality.sys, "platform", "linux")
    hook = tmp_path / ".git/hooks/pre-commit"
    hook.parent.mkdir(parents=True)
    tool = quality.RUNTIME / quality.PROFILE["quality_environment_directory"] / "bin/python"
    if conflict != "missing_tool":
        tool.parent.mkdir(parents=True)
        tool.write_text("isolated-test-tool", encoding="utf-8")
    if conflict == "custom_hook":
        hook.write_text("#!/bin/sh\nexit 7\n", encoding="utf-8")

    def fake_run(command, **kwargs):
        if command[0] != "git":
            raise AssertionError("installer must not execute on a conflict")
        output = ("private-hooks" if conflict == "core_hooks_path" else "") if "config" in command else str(hook)
        return types.SimpleNamespace(returncode=0, stdout=output)

    monkeypatch.setattr(quality.subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match="CUSTOM_GIT_HOOK|CUSTOM_HOOKS_PATH|QUALITY_TOOLS_NOT_INSTALLED"):
        installer()
    if conflict == "custom_hook":
        assert hook.read_text() == "#!/bin/sh\nexit 7\n"


def test_unknown_command_is_rejected():
    with pytest.raises(SystemExit) as failure:
        dev.main(["delete-all"])
    assert failure.value.code == 2


def test_precommit_contains_format_types_and_frontend_checks():
    commands = dev.plan("pre-commit")
    assert any("format" in command and "--check" in command for command in commands)
    assert any("scripts/stage_three_types.py" in command for command in commands)
    assert ["npm", "--prefix", "frontend", "run", "lint"] in commands
    assert ["npm", "--prefix", "frontend", "run", "format-check"] in commands


@pytest.mark.parametrize("name,frontend", [("lint", "lint"), ("format-check", "format-check")])
def test_frontend_quality_is_part_of_same_local_ci_entry(name, frontend):
    assert ["npm", "--prefix", "frontend", "run", frontend] in dev.plan(name)


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
    assert quality_spec is not None and quality_spec.loader is not None
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


@pytest.mark.parametrize("command", ["format-check", "pre-commit"])
def test_new_python_module_is_checked_without_updating_a_file_list(monkeypatch, tmp_path, command):
    import subprocess

    monkeypatch.setenv("MT_PYTHON", sys.executable)
    for name in dev.PROFILE["format_scope"]:
        target = tmp_path / name
        if target.suffix == ".py":
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("", encoding="utf-8")
        else:
            target.mkdir(parents=True, exist_ok=True)
    added = tmp_path / "backend/business_app/identity/new_feature.py"
    added.parent.mkdir(parents=True, exist_ok=True)
    added.write_text("def unformatted( ):return 1\n", encoding="utf-8")
    formatter = next(args for args in dev.plan(command) if args[1:4] == ["-m", "ruff", "format"])
    result = subprocess.run(formatter, cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 1, "new modules must inherit the format gate"
    assert "new_feature.py" in result.stdout + result.stderr
    added.write_text("def unformatted():\n    return 1\n", encoding="utf-8")
    result = subprocess.run(formatter, cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_directory_format_scope_also_checks_new_module_text(monkeypatch, tmp_path):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    import stage_three_quality as quality

    for name in [
        "CONTRIBUTING.md",
        "SECURITY.md",
        "CODEOWNERS",
        ".editorconfig",
        ".env.example",
        ".python-version",
        ".nvmrc",
        ".pre-commit-config.yaml",
        ".codex/config.toml",
        "Makefile",
        "scripts/dev.ps1",
        "config/stage-three-profile.json",
    ]:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"fixture\n")
    added = tmp_path / "backend/business_app/identity/new_feature.py"
    added.parent.mkdir(parents=True)
    added.write_bytes(b"VALUE = 1\r\n")
    monkeypatch.setattr(quality, "ROOT", tmp_path)
    monkeypatch.setattr(quality, "PROFILE", {"format_scope": ["backend/business_app"]})
    monkeypatch.setattr(quality, "tracked_files", lambda: [added.relative_to(tmp_path).as_posix()])
    with pytest.raises(AssertionError, match="new_feature.py"):
        quality.text_check()
    added.write_bytes(b"VALUE = 1\n")
    assert quality.text_check() == 0
