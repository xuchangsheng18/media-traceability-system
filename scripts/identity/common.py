"""Fixed boundaries shared by identity deployment operations."""

import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = Path("/workspace/glwy/runtime/media-traceability-system/identity")
PROJECT = "media-trace-identity"
CONTEXT = "desktop-linux"
PUBLIC_URL = "https://172.16.58.179:18443"
ADMIN_URL = "https://localhost:18444"
SERVICES = {"api", "inference", "postgres", "rabbitmq", "s3", "web", "worker"}
MINIMUM_FREE = 48 * 1024**3  # 20GiB database + 20GiB recovery + 8GiB images/headroom.


def run(args: list[str], *, timeout: int = 30) -> str:
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
    if result.returncode:
        raise RuntimeError("IDENTITY_OBSERVATION_COMMAND_FAILED")
    return result.stdout.strip()


def docker(*args: str) -> str:
    return run(["docker", "--context", CONTEXT, *args])


def ci_transport_active() -> bool:
    selected = os.environ.get("MT_IDENTITY_CI_IMAGE_TRANSPORT")
    if selected is None:
        return False
    try:
        temporary = Path(os.environ.get("RUNNER_TEMP", "/"))
        if (
            selected != "official-pinned-v1"
            or os.environ.get("GITHUB_ACTIONS") != "true"
            or os.environ.get("RUNNER_ENVIRONMENT") != "github-hosted"
            or os.environ.get("GITHUB_REPOSITORY") != "xuchangsheng18/media-traceability-system"
            or re.fullmatch(r"[0-9]+", os.environ.get("GITHUB_RUN_ID", "")) is None
            or Path(os.environ.get("GITHUB_WORKSPACE", "/")).resolve() != ROOT.resolve()
            or not temporary.is_absolute()
            or temporary == Path("/")
            or any(p.is_symlink() for p in [temporary, *temporary.parents])
            or temporary.stat().st_uid != os.geteuid()
        ):
            raise ValueError()
        private = temporary / "identity-ci-private"
        marker = private / "ownership.json"
        if (
            not private.is_dir()
            or private.is_symlink()
            or private.stat().st_uid != os.geteuid()
            or private.stat().st_mode & 0o077
            or not marker.is_file()
            or marker.is_symlink()
            or marker.stat().st_uid != os.geteuid()
            or marker.stat().st_mode & 0o077
            or marker.stat().st_size > 4096
            or json.loads(marker.read_text())
            != {"run_id": os.environ["GITHUB_RUN_ID"], "project": "media-trace-identity"}
        ):
            raise ValueError()
    except (ValueError, OSError, KeyError, TypeError):
        raise RuntimeError("IDENTITY_CI_TRANSPORT_PROFILE_REQUIRED") from None
    return True


def image(name: str) -> str:
    values = json.loads((ROOT / "config/identity/versions.json").read_text())
    reference = values["images"][name]["reference"]
    if not re.fullmatch(r"[a-z0-9./_-]+@sha256:[a-f0-9]{64}", reference):
        raise RuntimeError("IDENTITY_IMAGE_NOT_PINNED")
    if ci_transport_active() and name in {"postgres", "nginx"}:
        official = "docker.io/library/" + name
        if values["images"][name].get("official_repository") != official or not reference.startswith(
            "docker.m.daocloud.io/library/" + name + "@"
        ):
            raise RuntimeError("IDENTITY_CI_IMAGE_TRANSPORT_NOT_PINNED")
        return official + "@" + str(reference).rsplit("@", 1)[1]
    return str(reference)


def ci_compose_override() -> Path | None:
    if not ci_transport_active():
        return None
    path = Path(os.environ["RUNNER_TEMP"]) / "identity-ci-private/compose-source-override.json"
    expected = (
        json.dumps({"services": {"identity-gateway": {"image": image("nginx")}}}, sort_keys=True) + "\n"
    ).encode()
    if (
        not path.is_file()
        or path.is_symlink()
        or path.stat().st_uid != os.geteuid()
        or path.stat().st_mode & 0o077
        or path.stat().st_size != len(expected)
        or path.read_bytes() != expected
    ):
        raise RuntimeError("IDENTITY_CI_TRANSPORT_OVERRIDE_INVALID")
    return path


def private_runtime(path: Path) -> Path:
    path = path.absolute()
    if path != RUNTIME.absolute() or any(p.is_symlink() for p in [path, *path.parents]):
        raise RuntimeError("IDENTITY_RUNTIME_PATH_FORBIDDEN")
    if path.exists() and (not path.is_dir() or path.stat().st_mode & 0o077):
        raise RuntimeError("IDENTITY_RUNTIME_PERMISSION_INVALID")
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    return path
