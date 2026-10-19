"""Disposable hosted CI only: reproduce fixed identity origins, never install on the shared host."""

import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

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


def pinned_transport_plan(versions: dict[str, Any]) -> dict[str, dict[str, str]]:
    """Only the already-declared official repository with the exact locked digest."""
    result = {}
    try:
        for name in ("postgres", "nginx"):
            image = versions["images"][name]
            locked = image["reference"]
            official = "docker.io/library/" + name
            if (
                not isinstance(locked, str)
                or re.fullmatch(r"docker\.m\.daocloud\.io/library/" + name + r"@sha256:[a-f0-9]{64}", locked) is None
                or image.get("official_repository") != official
            ):
                raise ValueError()
            result[name] = {"locked": locked, "source": official + "@" + locked.rsplit("@", 1)[1]}
    except (ValueError, KeyError, TypeError, AttributeError):
        raise RuntimeError("IDENTITY_CI_IMAGE_TRANSPORT_NOT_PINNED") from None
    return result


def configure_image_transport() -> Path:
    """Hosted VM only: source-policy changes transport, never manifest content."""
    temporary = hosted_runner()
    plan = pinned_transport_plan(json.loads((common.ROOT / "config/identity/versions.json").read_text()))
    private = temporary / "identity-ci-private"
    private.mkdir(mode=0o700, exist_ok=True)
    policy = private / "source-policy.json"
    rules = [
        {
            "action": "CONVERT",
            "selector": {"identifier": "docker-image://" + route["locked"]},
            "updates": {"identifier": "docker-image://" + route["source"]},
        }
        for route in plan.values()
    ]
    fd = os.open(policy, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as output:
        json.dump({"rules": rules}, output)
        output.flush()
        os.fsync(output.fileno())
    for name, route in plan.items():
        execute(["docker", "--context", common.CONTEXT, "pull", route["source"]], "pull-source-" + name)
        # A repository alias lets runtime --pull=never resolve the unchanged locked reference.
        alias = route["locked"].split("@", 1)[0] + ":identity-ci-" + os.environ["GITHUB_RUN_ID"]
        execute(["docker", "--context", common.CONTEXT, "tag", route["source"], alias], "alias-source-" + name)
        original = common.docker("image", "inspect", route["source"], "--format", "{{.Id}}")
        resolved = common.docker("image", "inspect", route["locked"], "--format", "{{.Id}}")
        if original != resolved or re.fullmatch(r"sha256:[a-f0-9]{64}", original) is None:
            raise RuntimeError("IDENTITY_CI_IMAGE_TRANSPORT_MISMATCH")
    return policy


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
    source_policy = configure_image_transport()
    os.environ["EXPERIMENTAL_BUILDKIT_SOURCE_POLICY"] = str(source_policy)
    execute(["docker", "--context", common.CONTEXT, "pull", common.image("keycloak")], "pull-keycloak")
    # This is an empty disposable runner, not the operational migration path.
    # The operational 48GiB admission guard and all shared-server settings stay unchanged.
    control.prepare_configuration()
    for name, tag in (
        ("postgres", "media-trace-identity-postgres:16.15-alpine-1"),
        ("keycloak", "media-trace-identity-keycloak:26.8.1-1"),
    ):
        execute(
            [
                "docker",
                "--context",
                common.CONTEXT,
                "build",
                "--pull=false",
                "-t",
                tag,
                "-f",
                str(common.ROOT / ("deploy/identity/Dockerfile." + name)),
                str(common.ROOT / "deploy/identity"),
            ],
            "build-" + name,
            timeout=900,
        )
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
        output.write("EXPERIMENTAL_BUILDKIT_SOURCE_POLICY=" + str(source_policy) + "\n")
    print(
        '{"status":"PASS","disposable_identity_started":true,"same_digest_official_transport":true,"shared_server_modified":false}'
    )


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
