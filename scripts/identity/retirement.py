"""Prepare independent private retirement candidates; never adopt or delete them."""

import argparse
import hashlib
import json
import os
import secrets
from pathlib import Path
from typing import Any, TypedDict

from business_app.identity.config import private_file
from business_app.identity.tokens import unique_object

from . import common


class CandidateContents(TypedDict):
    configuration: str
    credentials: dict[str, Any]


def _contains_secret(value: Any, secret: str) -> bool:
    if isinstance(value, str):
        return secret in value
    if isinstance(value, dict):
        return any(_contains_secret(k, secret) or _contains_secret(v, secret) for k, v in value.items())
    if isinstance(value, list):
        return any(_contains_secret(v, secret) for v in value)
    return False


def candidate_contents(configuration: str, credentials: dict[str, Any]) -> CandidateContents:
    """Require a consistent pair before stripping only the temporary bootstrap."""
    keys = ("bootstrap-admin-client-id", "bootstrap-admin-client-secret")
    rows: dict[str, list[str]] = {k: [] for k in keys}
    lines = configuration.splitlines(keepends=True)
    for line in lines:
        key, separator, value = line.strip().partition("=")
        key = key.strip()
        if key in rows and separator:
            rows[key].append(value)
    if (
        not all(isinstance(credentials.get(k), str) and credentials[k] for k in ("db_admin", "db_keycloak"))
        or len(rows[keys[0]]) != 1
        or rows[keys[0]] != ["bootstrap-project-service"]
        or len(rows[keys[1]]) != 1
        or not isinstance(credentials.get("bootstrap_admin"), str)
        or not secrets.compare_digest(rows[keys[1]][0], credentials["bootstrap_admin"])
    ):
        raise RuntimeError("IDENTITY_RETIREMENT_SOURCE_REVIEW_REQUIRED")
    candidate: CandidateContents = {
        "configuration": "".join(line for line in lines if line.strip().partition("=")[0].strip() not in keys),
        "credentials": {key: value for key, value in credentials.items() if key != "bootstrap_admin"},
    }
    if _contains_secret(candidate, credentials["bootstrap_admin"]):
        raise RuntimeError("IDENTITY_RETIREMENT_SOURCE_RETAINED_SECRET_REVIEW_REQUIRED")
    return candidate


def _directory(path: Path) -> None:
    if not path.is_absolute() or any(p.is_symlink() for p in [path, *path.parents]):
        raise RuntimeError("IDENTITY_RETIREMENT_PRIVATE_DIRECTORY_REQUIRED")
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    if path.stat().st_uid != os.geteuid() or path.stat().st_mode & 0o077:
        raise RuntimeError("IDENTITY_RETIREMENT_PRIVATE_DIRECTORY_REQUIRED")


def _write(path: Path, data: bytes) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as destination:
        destination.write(data)
        destination.flush()
        os.fsync(destination.fileno())


def prepare_files(output: Path) -> dict[str, Any]:
    runtime = common.private_runtime(common.RUNTIME)
    parent = runtime.parent / "identity-retirement"
    if output.parent != parent or output.name in {"", ".", ".."} or output.is_symlink():
        raise RuntimeError("IDENTITY_RETIREMENT_PRIVATE_DIRECTORY_REQUIRED")
    if output.exists():
        raise RuntimeError("IDENTITY_RETIREMENT_CANDIDATE_EXISTS")
    try:
        original_credentials = private_file(runtime / "credentials.json", runtime)
        original_configuration = private_file(runtime / "keycloak-v2.conf", runtime)
        values = json.loads(original_credentials, object_pairs_hook=unique_object)
        candidate = candidate_contents(original_configuration.decode(), values)
    except (ValueError, OSError, TypeError, UnicodeError):
        raise RuntimeError("IDENTITY_RETIREMENT_SOURCE_REVIEW_REQUIRED") from None
    _directory(parent)
    output.mkdir(mode=0o700)  # Exclusive; a partial prior attempt requires inspection.
    marker = {"version": 1, "bootstrap_creation_disabled": True, "bootstrap_retirement_verified": False}
    _write(output / "credentials.json", (json.dumps(candidate["credentials"]) + "\n").encode())
    _write(output / "keycloak-v2.conf", candidate["configuration"].encode())
    _write(output / "bootstrap-retired.json", (json.dumps(marker) + "\n").encode())
    result = {
        "status": "PREPARED_PRIVATE_CANDIDATES_NOT_ADOPTED",
        "source_sha256": {
            "credentials.json": hashlib.sha256(original_credentials).hexdigest(),
            "keycloak-v2.conf": hashlib.sha256(original_configuration).hexdigest(),
        },
        "candidate_sha256": {
            name: hashlib.sha256((output / name).read_bytes()).hexdigest()
            for name in ("credentials.json", "keycloak-v2.conf", "bootstrap-retired.json")
        },
        "output_directory": str(output),
        "database_credentials_preserved": True,
        "bootstrap_deleted": False,
        "shared_configuration_replaced": False,
        "flag_scope": "actions_performed_by_preparation_not_observed_server_object_state",
        "shared_services_restarted": False,
        "actual_personal_handover_verified": False,
        "formal_accepted": False,
        "adoption_blockers": [
            "fresh named-person MFA management session and independent recovery access",
            "actual encrypted backups and independent key custody",
            "controlled new secret-volume adoption and agreed maintenance window",
            "old bootstrap token/secret refusal and restart checks against the adopted target",
            "retained historical configuration/backup custody and software admission review",
        ],
    }
    _write(output / "manifest.json", (json.dumps(result, indent=2) + "\n").encode())
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare private files only; never delete a bootstrap client.")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if not args.apply:
        print('{"applied":false,"bootstrap_deleted":false,"shared_configuration_replaced":false}')
        return
    if args.output is None:
        parser.error("--apply requires --output")
    try:
        print(json.dumps(prepare_files(args.output)))
    except (RuntimeError, ValueError, OSError, TypeError):
        print('{"status":"FAIL","error":"IDENTITY_RETIREMENT_PREPARATION_NOT_CONFIRMED","bootstrap_deleted":false}')
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
