"""One explicit task entry for the existing locked CPU development profile."""

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE = json.loads((ROOT / "config/stage-three-profile.json").read_text(encoding="utf-8"))
COMMANDS = (
    "help",
    "setup",
    "dev",
    "stop",
    "status",
    "lint",
    "format-check",
    "type-check",
    "test",
    "contract-test",
    "integration-test",
    "build",
    "security-scan",
    "clean",
    "pre-commit",
    "ci",
)


def python():
    return os.environ.get("MT_PYTHON", PROFILE["python_executable"])


def environment():
    env = dict(os.environ, PYTHONPATH=str(ROOT / "backend"), PYTHONDONTWRITEBYTECODE="1")
    node_bin = env.get("MT_NODE_BIN", "/home/glwy/.cache/media-trace-node/node-v22.21.1-linux-x64/bin")
    env["PATH"] = str(Path(python()).parent) + os.pathsep + node_bin + os.pathsep + env.get("PATH", "")
    env.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/home/glwy/.cache/media-trace-browsers")
    return env


def plan(name):
    py = python()
    scripts = lambda *items: [[py, "scripts/" + item] for item in items]
    if name == "setup":
        return [
            [py, "-m", "pip", "check"],
            [py, "scripts/verify_runtime_lock.py"],
            ["node", "--version"],
            ["npm", "--prefix", "frontend", "ci", "--no-audit", "--no-fund"],
        ]
    if name == "lint":
        return [[py, "-m", "ruff", "check", "--config", "ruff.toml", *PROFILE["lint_scope"]], *plan("type-check")]
    if name == "format-check":
        return [
            [py, "-m", "ruff", "format", "--check", *PROFILE["format_scope"]],
            [py, "scripts/stage_three_quality.py", "text"],
        ]
    if name == "type-check":
        return [
            [py, "scripts/stage_three_types.py", "check"],
            ["npm", "--prefix", "frontend", "exec", "--", "vue-tsc", "--noEmit", "-p", "frontend/tsconfig.json"],
        ]
    if name == "test":
        return [
            [py, "-m", "pytest", "tests/poc", "tests/stage_three", "-q"],
            [py, "scripts/verify_business_foundation.py", "run"],
            ["npm", "--prefix", "frontend", "test"],
        ]
    if name == "contract-test":
        return scripts("validate_inputs.py", "validate_database_contracts.py", "verify_generated_contracts.py")
    if name == "integration-test":
        return [[py, "scripts/run_ci.py", "integration"]]
    if name == "build":
        return [[py, "scripts/run_ci.py", "build"]]
    if name == "ci":
        return [[py, "scripts/run_ci.py", "all"]]
    if name == "security-scan":
        return [
            [py, "scripts/stage_three_quality.py", "secrets"],
            [py, "scripts/stage_three_quality.py", "dependencies"],
        ]
    if name == "pre-commit":
        return [
            [py, "scripts/stage_three_quality.py", "text"],
            [py, "scripts/stage_three_quality.py", "secrets"],
            [py, "-m", "ruff", "check", "--config", "ruff.toml", *PROFILE["lint_scope"]],
        ]
    if name == "stop":
        return [[py, "scripts/poc_control.py", "down"]]
    return []


def clean_paths(root=ROOT):
    base = root.resolve()
    paths = []
    for name in PROFILE["clean_allowlist"]:
        candidate = base / name
        if candidate.is_symlink() or not candidate.resolve().is_relative_to(base) or candidate.resolve() == base:
            raise RuntimeError("UNSAFE_CLEAN_TARGET")
        if candidate.exists():
            if not candidate.is_dir():
                raise RuntimeError("CLEAN_TARGET_NOT_DIRECTORY")
            paths.append(candidate)
    return paths


def isolated_ci_workspace():
    # Environment labels alone do not establish separation from the shared host.
    if os.environ.get("GITHUB_ACTIONS") != "true" or os.environ.get("RUNNER_ENVIRONMENT") != "github-hosted":
        return False
    paths = [os.environ.get(name, "") for name in ("GITHUB_WORKSPACE", "RUNNER_TEMP", "MT_RUNTIME_DIR")]
    if not all(paths) or not all(Path(value).is_absolute() for value in paths):
        return False
    workspace, temporary, runtime = [Path(value).resolve() for value in paths]
    shared = Path("/workspace/glwy").resolve()
    if any(path == shared or path.is_relative_to(shared) for path in (workspace, temporary, runtime)):
        return False
    return (
        ROOT.resolve() == workspace
        and runtime != temporary
        and runtime.is_relative_to(temporary)
        and not temporary.is_relative_to(workspace)
        and os.environ.get("MT_DOCKER_CONTEXT") == "default"
        and not os.environ.get("DOCKER_HOST")
    )


def stack_change_guard(allowed):
    if not allowed:
        raise RuntimeError("STACK_CHANGE_REQUIRES_EXPLICIT_COMMAND_FLAG_USE_READ_ONLY_STATUS_FIRST")
    # A hosted fresh workspace has no existing shared PostgreSQL filesystem to inspect.
    # This is an operational guard, not an authorization or security boundary.
    if isolated_ci_workspace():
        return
    from poc_control import compose

    lines = compose(
        "exec", "-T", "postgres", "df", "-P", "-B1", "/var/lib/postgresql/data", capture=True
    ).stdout.splitlines()
    free = lines[-1].split() if lines else []
    if len(free) < 6 or not free[3].isdigit():
        raise RuntimeError("DEVELOPMENT_DATA_FILESYSTEM_CAPACITY_UNREADABLE")
    if int(free[3]) < PROFILE["minimum_free_bytes_before_stack_changes"]:
        raise RuntimeError("DEVELOPMENT_DATA_FILESYSTEM_CAPACITY_BELOW_STACK_CHANGE_GUARD")


def status():
    from poc_control import compose

    services = [json.loads(line) for line in compose("ps", "--format", "json", capture=True).stdout.splitlines()]
    summary = [
        {"service": item["Service"], "state": item["State"], "health": item.get("Health", "unknown")}
        for item in services
    ]
    expected = {"api", "web", "worker", "inference", "postgres", "s3", "rabbitmq"}
    healthy = (
        len(summary) == len(expected)
        and {item["service"] for item in summary} == expected
        and all(item["state"] == "running" and item["health"] == "healthy" for item in summary)
    )
    print(json.dumps({"status": "PASS" if healthy else "NOT_READY", "services": summary, "services_changed": False}))
    return 0 if healthy else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=COMMANDS, nargs="?", default="help")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--tools", action="store_true", help="Set up the separately locked quality tools; preserve project py310"
    )
    parser.add_argument("--apply", action="store_true", help="Apply clean only to the exact cache allowlist")
    parser.add_argument(
        "--allow-stack-changes",
        action="store_true",
        help="Allow the named development stack action subject to capacity",
    )
    args = parser.parse_args(argv)
    if args.command == "help":
        print(
            json.dumps(
                {
                    "commands": COMMANDS,
                    "profile": PROFILE["profile"],
                    "python": python(),
                    "scope": "CPU_development_not_production_or_business_acceptance",
                }
            )
        )
        return 0
    if args.command == "clean":
        targets = clean_paths()
        if args.apply and not args.dry_run:
            for target in targets:
                shutil.rmtree(target)
        print(
            json.dumps(
                {
                    "status": "PASS",
                    "dry_run": not args.apply or args.dry_run,
                    "targets": [p.relative_to(ROOT).as_posix() for p in targets],
                    "volumes_or_business_data_removed": False,
                }
            )
        )
        return 0
    commands = plan(args.command)
    if args.command == "setup" and args.tools:
        commands.append([python(), "scripts/stage_three_quality.py", "setup-tools"])
        commands.append([python(), "scripts/stage_three_types.py", "setup"])
    if args.command == "dev":
        commands = [[python(), "scripts/poc_control.py", "up"]] if args.allow_stack_changes else []
    if args.dry_run:
        print(
            json.dumps(
                {
                    "status": "PLAN_ONLY",
                    "command": args.command,
                    "commands": commands,
                    "observes_existing_stack": args.command in {"dev", "status"} and not commands,
                    "executed": False,
                }
            )
        )
        return 0
    try:
        if not Path(python()).is_file():
            raise RuntimeError("LOCKED_PY310_EXECUTABLE_MISSING_USE_WINDOWS_SERVER_ENTRY_OR_PREPARE_LOCKED_RUNTIME")
        if args.command in {"integration-test", "build", "ci"} or args.command == "dev" and args.allow_stack_changes:
            stack_change_guard(args.allow_stack_changes)
        if args.command in {"dev", "status"} and not commands:
            return status()
        for command in commands:
            result = subprocess.run(command, cwd=ROOT, env=environment(), check=False)
            if result.returncode:
                return result.returncode
        return 0
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        print(
            json.dumps(
                {
                    "status": "FAIL_OR_BLOCKED",
                    "command": args.command,
                    "error_type": type(exc).__name__,
                    "reason": str(exc) if isinstance(exc, RuntimeError) else "COMMAND_EXECUTION_FAILED",
                }
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
