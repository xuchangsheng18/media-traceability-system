"""Disposable hosted CI only: reproduce fixed identity origins, never install on the shared host."""

import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

from . import common, control


def hosted_runner() -> Path:
    values = os.environ
    if (
        values.get("GITHUB_ACTIONS") != "true"
        or values.get("RUNNER_ENVIRONMENT") != "github-hosted"
        or values.get("GITHUB_REPOSITORY") != "xuchangsheng18/media-traceability-system"
        or re.fullmatch(r"[0-9]+", values.get("GITHUB_RUN_ID", "")) is None
        or Path(values.get("GITHUB_WORKSPACE", "/")).resolve() != common.ROOT.resolve()
    ):
        raise RuntimeError("IDENTITY_CI_DISPOSABLE_RUNNER_REQUIRED")
    root = Path(values.get("RUNNER_TEMP", "/"))
    if not root.is_absolute() or root == Path("/") or not root.is_dir() or root.stat().st_uid != os.geteuid():
        raise RuntimeError("IDENTITY_CI_DISPOSABLE_RUNNER_REQUIRED")
    if any(p.is_symlink() for p in [root, *root.parents]):
        raise RuntimeError("IDENTITY_CI_DISPOSABLE_RUNNER_REQUIRED")
    return root


def execute(args: list[str], name: str, *, timeout: int = 600) -> None:
    root = hosted_runner() / "identity-ci-private"
    root.mkdir(mode=0o700, exist_ok=True)
    log = root / (name + ".private.log")
    with log.open("xb") as output:
        log.chmod(0o600)
        result = subprocess.run(args, cwd=common.ROOT, stdout=output, stderr=subprocess.STDOUT, timeout=timeout)
    if result.returncode:
        raise RuntimeError("IDENTITY_CI_STAGE_FAILED_" + name.upper())


def prepare() -> None:
    temporary = hosted_runner()
    private = temporary / "identity-ci-private"
    private.mkdir(mode=0o700, exist_ok=True)
    marker = private / "ownership.json"
    if marker.exists() or common.RUNTIME.parent.exists():
        raise RuntimeError("IDENTITY_CI_FRESH_RUNNER_REQUIRED")
    if shutil.disk_usage(temporary).free < 8 * 1024**3:
        raise RuntimeError("IDENTITY_CI_DISK_CAPACITY_REQUIRED")
    if subprocess.check_output(
        ["docker", "ps", "-aq", "--filter", "label=com.docker.compose.project=" + common.PROJECT], text=True
    ).strip():
        raise RuntimeError("IDENTITY_CI_PROJECT_ALREADY_EXISTS")
    if subprocess.check_output(
        ["docker", "volume", "ls", "-q", "--filter", "label=com.docker.compose.project=" + common.PROJECT], text=True
    ).strip():
        raise RuntimeError("IDENTITY_CI_PROJECT_ALREADY_EXISTS")
    contexts = subprocess.check_output(["docker", "context", "ls", "--format", "{{.Name}}"], text=True).splitlines()
    if common.CONTEXT in contexts:
        raise RuntimeError("IDENTITY_CI_CONTEXT_ALREADY_EXISTS")
    marker.write_text(json.dumps({"run_id": os.environ["GITHUB_RUN_ID"], "project": common.PROJECT}) + "\n")
    marker.chmod(0o600)
    execute(["docker", "context", "create", common.CONTEXT, "--docker", "host=unix:///var/run/docker.sock"], "context")
    execute(
        [
            "sudo",
            "install",
            "-d",
            "-m",
            "700",
            "-o",
            str(os.geteuid()),
            "-g",
            str(os.getegid()),
            str(common.RUNTIME.parent),
        ],
        "private-root",
    )
    execute(["sudo", "ip", "address", "add", "172.16.58.179/32", "dev", "lo"], "loopback-origin")
    for name in ["postgres", "keycloak", "nginx"]:
        execute(["docker", "--context", common.CONTEXT, "pull", common.image(name)], "pull-" + name)
    # This is an empty disposable runner, not the operational migration path.
    # The operational 48GiB admission guard and all shared-server settings stay unchanged.
    control.prepare_configuration()
    execute(control.command("build", "--pull=false"), "build", timeout=900)
    execute(control.command("up", "-d", "--no-build", "--pull", "never", "--wait", "--wait-timeout", "240"), "up")
    browser_root = private / "browser"
    browser_root.mkdir(mode=0o700)
    node, certutil = shutil.which("node"), shutil.which("certutil")
    if node is None or certutil is None:
        raise RuntimeError("IDENTITY_CI_BROWSER_TOOLS_REQUIRED")
    target = private / "test-target.json"
    target.write_text(
        json.dumps(
            {
                "public_url": "https://172.16.58.179:18443",
                "admin_url": "https://localhost:18444",
                "ca_file": str(common.RUNTIME / "pki/ca.crt"),
                "node_executable": node,
                "certutil": certutil,
                "browser_cache": os.environ["PLAYWRIGHT_BROWSERS_PATH"],
                "private_test_root": str(browser_root),
            }
        )
    )
    target.chmod(0o600)
    environment = Path(os.environ["GITHUB_ENV"])
    if not environment.resolve().is_relative_to(temporary.resolve()) or environment.is_symlink():
        raise RuntimeError("IDENTITY_CI_ENVIRONMENT_PATH_INVALID")
    with environment.open("a") as output:
        output.write("MT_IDENTITY_TEST_CONFIG=" + str(target) + "\n")
    print('{"status":"PASS","disposable_identity_started":true,"shared_server_modified":false}')


def cleanup() -> None:
    temporary = hosted_runner()
    marker = temporary / "identity-ci-private/ownership.json"
    if not marker.exists():
        return
    value = json.loads(marker.read_text())
    if value != {"run_id": os.environ["GITHUB_RUN_ID"], "project": common.PROJECT}:
        raise RuntimeError("IDENTITY_CI_OWNERSHIP_MISMATCH")
    if common.RUNTIME.exists():
        execute(control.command("down"), "down", timeout=120)
    print('{"status":"PASS","ci_project_stopped":true,"volumes_deleted":false}')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "cleanup"])
    args = parser.parse_args()
    try:
        (prepare if args.action == "prepare" else cleanup)()
        return 0
    except (RuntimeError, OSError, subprocess.SubprocessError) as error:
        # Only our constant diagnostic codes are public. Captured command logs stay private.
        code = (
            str(error)
            if isinstance(error, RuntimeError) and str(error).startswith("IDENTITY_")
            else "IDENTITY_CI_FAILED"
        )
        print(json.dumps({"status": "FAIL", "error": code, "raw_logs_published": False}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
