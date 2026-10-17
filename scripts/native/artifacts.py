"""Verify native package bytes and pinned official checksums without installing."""

import argparse
import datetime
import hashlib
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

REQUIRED_VERSIONS = {
    "python": "3.10.22",
    "node": "22.21.1",
    "postgres": "16.15",
    "rabbitmq": "4.3.6",
    "erlang": "27.3.4.18",
    "nginx": "1.30.6",
    "seaweedfs": "4.48",
    "keycloak": "26.8.1",
}
OFFICIAL_PREFIXES = {
    "python": "https://github.com/conda-forge/miniforge/",
    "node": "https://nodejs.org/dist/",
    "postgres": "https://ftp.postgresql.org/pub/source/",
    "rabbitmq": "https://github.com/rabbitmq/rabbitmq-server/",
    "erlang": "https://github.com/erlang/otp/",
    "seaweedfs": "https://github.com/seaweedfs/seaweedfs/",
    "keycloak": "https://github.com/keycloak/keycloak/",
    "java": "https://github.com/adoptium/temurin21-binaries/",
    "nginx": "https://nginx.org/download/",
    "age": "https://github.com/FiloSottile/age/",
}


def official_url(component: str, url: Any) -> bool:
    if not isinstance(url, str) or component not in OFFICIAL_PREFIXES:
        return False
    parsed = urlsplit(url)
    return (
        url.startswith(OFFICIAL_PREFIXES[component])
        and parsed.scheme == "https"
        and parsed.username is None
        and parsed.password is None
        and not parsed.query
        and not parsed.fragment
        and ".." not in parsed.path.split("/")
    )


def artifact_file(root: Path, name: Any) -> Path:
    if not isinstance(name, str) or not name or "\\" in name or Path(name).is_absolute():
        raise ValueError("INVALID_RELATIVE_PATH")
    parts = Path(name).parts
    if ".." in parts:
        raise ValueError("PATH_ESCAPE")
    current = root
    for part in parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("SYMLINK_NOT_ALLOWED")
    if not current.resolve().is_relative_to(root.resolve()) or not current.is_file():
        raise ValueError("MISSING_ARTIFACT")
    return current


def digest(path: Path, algorithm: str = "sha256") -> str:
    result = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def validate_artifacts(lock: dict[str, Any], artifact_root: Path) -> dict[str, Any]:
    blockers: list[str] = []
    checked: list[str] = []
    root = Path(artifact_root)
    if lock.get("schema_version") != 1 or lock.get("architecture") != "amd64":
        blockers.append("UNSUPPORTED_SCHEMA_OR_ARCHITECTURE")
    items = lock.get("artifacts", [])
    if not isinstance(items, list):
        items = []
        blockers.append("INVALID_ARTIFACT_LIST")
    names = [item.get("component") for item in items if isinstance(item, dict)]
    if len(names) != len(items) or any(not isinstance(name, str) for name in names):
        blockers.append("INVALID_COMPONENT")
    names = [name for name in names if isinstance(name, str)]
    if len(set(names)) != len(names):
        blockers.append("DUPLICATE_COMPONENT")
    for required_name in sorted(set(OFFICIAL_PREFIXES) - set(names)):
        blockers.append(required_name + ":MISSING_COMPONENT")
    if not root.is_dir() or root.is_symlink():
        blockers.append("MISSING_OR_SYMLINK_ARTIFACT_ROOT")
    dependencies: dict[str, list[str]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        name = item.get("component")
        if not isinstance(name, str):
            continue
        try:
            version = item.get("version")
            if not isinstance(version, str) or not re.fullmatch(r"\d+(?:[.\w+~-]*\d)?", version):
                raise ValueError("MISSING_EXACT_VERSION")
            if name in REQUIRED_VERSIONS and version != REQUIRED_VERSIONS[name]:
                raise ValueError("BASELINE_VERSION_MISMATCH")
            if (name == "erlang" and not version.startswith("27.")) or (
                name == "java" and not version.startswith("21.")
            ):
                raise ValueError("INCOMPATIBLE_RUNTIME")
            if item.get("architecture") != "amd64" or not item.get("license"):
                raise ValueError("ARCHITECTURE_OR_LICENSE_MISSING")
            if not official_url(name, item.get("url")):
                raise ValueError("UNTRUSTED_SOURCE")
            expected = item.get("sha256")
            if not isinstance(expected, str) or not re.fullmatch(r"[a-f0-9]{64}", expected):
                raise ValueError("MISSING_SHA256")
            package = artifact_file(root, item.get("filename"))
            if digest(package) != expected:
                raise ValueError("ARTIFACT_DIGEST_MISMATCH")
            provenance = item.get("provenance")
            if not isinstance(provenance, dict):
                raise ValueError("MISSING_OFFICIAL_PROVENANCE")
            method = provenance.get("method")
            if method not in {"official_sha256", "official_sha512", "github_release_api"}:
                raise ValueError("UNSUPPORTED_PROVENANCE")
            provenance_url = provenance.get("url")
            if method == "github_release_api":
                prefix = OFFICIAL_PREFIXES.get(name, "")
                if not prefix.startswith("https://github.com/"):
                    raise ValueError("MISSING_OFFICIAL_PROVENANCE")
                api_prefix = prefix.replace("https://github.com/", "https://api.github.com/repos/") + "releases/"
                if not isinstance(provenance_url, str) or not provenance_url.startswith(api_prefix):
                    raise ValueError("MISSING_OFFICIAL_PROVENANCE")
            elif not official_url(name, provenance_url):
                raise ValueError("MISSING_OFFICIAL_PROVENANCE")
            evidence = artifact_file(root, provenance.get("filename"))
            if digest(evidence) != provenance.get("sha256"):
                raise ValueError("PROVENANCE_DIGEST_MISMATCH")
            if method == "github_release_api":
                metadata = json.loads(evidence.read_text(encoding="utf-8"))
                if not isinstance(metadata, dict) or not isinstance(metadata.get("tag_name"), str):
                    raise ValueError("RELEASE_VERSION_MISMATCH")
                if metadata["tag_name"].removeprefix("v") != version:
                    raise ValueError("RELEASE_VERSION_MISMATCH")
                assets = metadata.get("assets")
                if not isinstance(assets, list):
                    raise ValueError("RELEASE_ASSET_MISSING")
                matches = [asset for asset in assets if isinstance(asset, dict) and asset.get("name") == package.name]
                if (
                    len(matches) != 1
                    or matches[0].get("digest") != "sha256:" + expected
                    or matches[0].get("browser_download_url") != item["url"]
                ):
                    raise ValueError("RELEASE_ASSET_MISMATCH")
            else:
                algorithm = "sha512" if method == "official_sha512" else "sha256"
                upstream_digest = digest(package, algorithm)
                expected_line = re.compile(
                    r"^" + upstream_digest + r"\s+\*?" + re.escape(package.name) + r"$", re.MULTILINE
                )
                if not expected_line.search(evidence.read_text(encoding="utf-8").replace("\r\n", "\n")):
                    raise ValueError("OFFICIAL_CHECKSUM_ENTRY_MISSING")
            deps = item.get("dependencies")
            if not isinstance(deps, list) or any(not isinstance(dep, str) or dep not in names for dep in deps):
                raise ValueError("UNRESOLVED_DEPENDENCY")
            dependencies[name] = deps
            checked.append(name)
        except (ValueError, OSError) as exc:
            # Only fixed reason codes are public; do not echo raw file contents or paths.
            code = str(exc) if isinstance(exc, ValueError) and str(exc).isupper() else "UNREADABLE_ARTIFACT"
            blockers.append(name + ":" + code)
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(name: str) -> None:
        if name in visiting:
            raise ValueError("DEPENDENCY_CYCLE")
        if name in visited:
            return
        visiting.add(name)
        for dep in dependencies.get(name, []):
            visit(dep)
        visiting.remove(name)
        visited.add(name)

    try:
        for name in dependencies:
            visit(name)
    except ValueError:
        blockers.append("DEPENDENCY_CYCLE")
    return {
        "schema_version": 1,
        "observed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "scope": "offline_native_package_and_official_checksum_verification_not_installation",
        "status": "FAIL" if blockers else "PASS",
        "blockers": blockers,
        "verified_components": sorted(checked),
        "installation_performed": False,
        "installation_ready": False,
        "complete_os_dependency_and_signature_admission_asserted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["verify"])
    parser.add_argument("--lock", required=True, type=Path)
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args()
    try:
        lock = json.loads(args.lock.read_text(encoding="utf-8"))
        if not isinstance(lock, dict):
            raise ValueError("INVALID_LOCK")
        report = validate_artifacts(lock, args.root)
    except (OSError, ValueError):
        report = {"status": "FAIL", "blockers": ["UNREADABLE_LOCK"], "installation_performed": False}
    print(json.dumps(report, ensure_ascii=True))
    return int(report["status"] != "PASS")


if __name__ == "__main__":
    raise SystemExit(main())
