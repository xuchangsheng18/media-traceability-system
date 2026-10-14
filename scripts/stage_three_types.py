"""Separately hashed Python type tools; never install into the runtime interpreter."""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = Path(os.environ.get("MT_RUNTIME_DIR", "/workspace/glwy/runtime/media-traceability-system"))
LOCK = ROOT / "config/locks/requirements-stage-three-types.lock"
ARTIFACTS = ROOT / "config/locks/stage-three-type-artifacts.json"


def verify_artifacts(lock_path: Path, artifacts_path: Path) -> None:
    entries = json.loads(artifacts_path.read_text())["artifacts"]
    expected = {(entry["name"].lower().replace("_", "-"), entry["version"], entry["sha256"]) for entry in entries}
    lines = re.findall(r"^([\w.-]+)==([^ ]+) --hash=sha256:([0-9a-f]{64})$", lock_path.read_text(), re.M)
    observed = {(name.lower().replace("_", "-"), version, digest) for name, version, digest in lines}
    if expected != observed or len(lines) != len(entries) or len(observed) != len(entries):
        raise RuntimeError("TYPE_LOCK_ARTIFACT_CLOSURE_MISMATCH")
    for entry in entries:
        file = Path(entry.get("local_path", RUNTIME / "stage-three-type-artifacts" / entry["filename"]))
        if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest() != entry["sha256"]:
            raise RuntimeError("TYPE_ARTIFACT_DIGEST_MISMATCH")


def setup_type_environment(runtime_dir: Path, base_python: Path) -> Path:
    if runtime_dir.resolve().is_relative_to(ROOT.resolve()):
        raise RuntimeError("TYPE_ENVIRONMENT_MUST_BE_OUTSIDE_SOURCE")
    target = runtime_dir / "stage-three-type-tools"
    if any(path.is_symlink() for path in [runtime_dir, target, *runtime_dir.parents]):
        raise RuntimeError("TYPE_ENVIRONMENT_SYMLINK_REJECTED")
    version = subprocess.check_output(
        [str(base_python), "-c", "import sys; print('.'.join(map(str,sys.version_info[:3])))"], text=True
    ).strip()
    if version != "3.10.22":
        raise RuntimeError("TYPE_TOOLS_REQUIRE_LOCKED_PYTHON_3_10_22")
    before = subprocess.check_output([str(base_python), "-m", "pip", "freeze"])
    cache = runtime_dir / "stage-three-type-artifacts"
    cache.mkdir(parents=True, exist_ok=True)
    metadata = json.loads(ARTIFACTS.read_text())
    for entry in metadata["artifacts"]:
        if Path(entry["filename"]).name != entry["filename"]:
            raise RuntimeError("INVALID_TYPE_ARTIFACT_NAME")
        path = cache / entry["filename"]
        if path.is_symlink():
            raise RuntimeError("TYPE_ARTIFACT_SYMLINK_REJECTED")
        if not path.exists():
            if not entry["url"].startswith("https://files.pythonhosted.org/"):
                raise RuntimeError("TYPE_ARTIFACT_SOURCE_REJECTED")
            urllib.request.urlretrieve(entry["url"], path)
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            raise RuntimeError("TYPE_ARTIFACT_DIGEST_MISMATCH")
    verify_artifacts(LOCK, ARTIFACTS)
    py = target / "bin/python"
    if not py.exists():
        subprocess.run([str(base_python), "-m", "venv", "--system-site-packages", str(target)], check=True)
    subprocess.run(
        [
            str(py),
            "-m",
            "pip",
            "install",
            "--no-index",
            "--find-links",
            str(cache),
            "--require-hashes",
            "--no-deps",
            "-r",
            str(LOCK),
        ],
        check=True,
    )
    subprocess.run([str(py), "-m", "pip", "check"], check=True)
    after = subprocess.check_output([str(base_python), "-m", "pip", "freeze"])
    if before != after or py.resolve() == base_python.resolve():
        # venv python is normally a symlink to base; prefix identity, not binary identity,
        # determines package installation destination.
        prefix = subprocess.check_output([str(py), "-c", "import sys; print(sys.prefix)"], text=True).strip()
        if before != after or Path(prefix).resolve() != target.resolve():
            raise RuntimeError("ORIGINAL_RUNTIME_CHANGED_OR_INVALID_TOOL_PREFIX")
    print(
        json.dumps(
            {
                "status": "PASS",
                "tool_packages": len(metadata["artifacts"]),
                "original_runtime_packages_unchanged": before == after,
                "tool_python": str(py),
                "mypy": subprocess.check_output([str(py), "-m", "mypy", "--version"], text=True).strip(),
            }
        )
    )
    return py


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["setup"])
    args = parser.parse_args()
    if args.action == "setup":
        setup_type_environment(RUNTIME, Path(sys.executable))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
