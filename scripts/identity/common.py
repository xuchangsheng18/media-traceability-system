"""Fixed boundaries shared by identity deployment operations."""

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = Path("/workspace/glwy/runtime/media-traceability-system/identity")
PROJECT = "media-trace-identity"
CONTEXT = "desktop-linux"
SERVICES = {"api", "inference", "postgres", "rabbitmq", "s3", "web", "worker"}
MINIMUM_FREE = 48 * 1024**3  # 20GiB database + 20GiB recovery + 8GiB images/headroom.


def run(args: list[str], *, timeout: int = 30) -> str:
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
    if result.returncode:
        raise RuntimeError("IDENTITY_OBSERVATION_COMMAND_FAILED")
    return result.stdout.strip()


def docker(*args: str) -> str:
    return run(["docker", "--context", CONTEXT, *args])


def image(name: str) -> str:
    values = json.loads((ROOT / "config/identity/versions.json").read_text())
    reference = values["images"][name]["reference"]
    import re

    if not re.fullmatch(r"[a-z0-9./_-]+@sha256:[a-f0-9]{64}", reference):
        raise RuntimeError("IDENTITY_IMAGE_NOT_PINNED")
    return str(reference)


def private_runtime(path: Path) -> Path:
    path = path.absolute()
    if path != RUNTIME.absolute() or any(p.is_symlink() for p in [path, *path.parents]):
        raise RuntimeError("IDENTITY_RUNTIME_PATH_FORBIDDEN")
    if path.exists() and (not path.is_dir() or path.stat().st_mode & 0o077):
        raise RuntimeError("IDENTITY_RUNTIME_PERMISSION_INVALID")
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    return path
