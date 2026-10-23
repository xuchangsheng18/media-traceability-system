"""Verify encrypted backup before restoring to a new network-isolated database."""

import argparse
import json
import os
import re
import subprocess
import time
from pathlib import Path

from . import common
from .backup import digest, private_home


def validate_restore_target(project: str, existing: set[str]) -> None:
    if re.fullmatch(r"media-trace-identity-restore(?:-[a-f0-9]{8})?", project) is None or project in existing:
        raise RuntimeError("ISOLATED_NEW_IDENTITY_RESTORE_TARGET_REQUIRED")


def stop_restore_container(container: str) -> None:
    common.run(["docker", "--context", common.CONTEXT, "stop", "--time", "60", container], timeout=90)


def initialized_database_ready(container: str) -> bool:
    try:
        result = subprocess.run(
            [
                "docker",
                "--context",
                common.CONTEXT,
                "exec",
                container,
                "sh",
                "-ec",
                'test "$(cat /proc/1/comm)" = postgres; '
                "psql -U keycloak -d keycloak -Atc 'SELECT current_database(),current_user'",
            ],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0 and result.stdout.strip() == b"keycloak|keycloak"
    except subprocess.TimeoutExpired:
        return False


def verify_encrypted(path: Path, gpg_home: Path, signer: str) -> str:
    private_home(gpg_home)
    if (
        path.is_symlink()
        or not path.is_file()
        or path.stat().st_mode & 0o077
        or path.stat().st_uid != os.geteuid()
        or re.fullmatch(r"[a-fA-F0-9]{40}(?:[a-fA-F0-9]{24})?", signer) is None
    ):
        raise RuntimeError("IDENTITY_RESTORE_INPUT_INVALID")
    result = subprocess.run(
        [
            "gpg",
            "--homedir",
            str(gpg_home),
            "--batch",
            "--pinentry-mode",
            "error",
            "--status-fd",
            "1",
            "--output",
            os.devnull,
            "--decrypt",
            str(path),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    rows = [line.split() for line in result.stdout.splitlines()]
    signatures = [row for row in rows if row[:2] == ["[GNUPG:]", "VALIDSIG"]]
    valid = any(signer.upper() in {row[2].upper(), row[-1].upper()} for row in signatures if len(row) >= 3)
    if result.returncode or not valid or "[GNUPG:] DECRYPTION_OKAY" not in result.stdout:
        raise RuntimeError("IDENTITY_RESTORE_SIGNATURE_OR_DECRYPTION_FAILED")
    return digest(path)


def restore_database(backup: Path, project: str, home: Path, signer: str) -> dict[str, object]:
    existing = set(common.docker("volume", "ls", "--format", "{{.Name}}").splitlines())
    validate_restore_target(project, {p.removesuffix("_identity-data") for p in existing})
    verified = verify_encrypted(backup, home, signer)
    container, volume = project + "-postgres", project + "_identity-data"
    if common.docker("ps", "-aq", "--filter", "name=^/" + container + "$"):
        raise RuntimeError("IDENTITY_RESTORE_CONTAINER_EXISTS")
    common.docker("volume", "create", "--label", "com.docker.compose.project=" + project, volume)
    common.docker(
        "run",
        "-d",
        "--name",
        container,
        "--network",
        "none",
        "--cpus",
        "1",
        "--memory",
        "2g",
        "--pids-limit",
        "128",
        "--label",
        "com.docker.compose.project=" + project,
        "-e",
        "POSTGRES_USER=identity_admin",
        "-e",
        "POSTGRES_DB=postgres",
        "-e",
        "POSTGRES_PASSWORD_FILE=/etc/identity/admin-password",
        "-v",
        common.PROJECT + "_postgres-secrets-v2:/etc/identity:ro",
        "-v",
        volume + ":/var/lib/postgresql/data",
        "media-trace-identity-postgres:16.15-alpine-1",
        "postgres",
        "-c",
        "config_file=/etc/identity/postgres.conf",
    )
    start = time.monotonic()
    try:
        ready = False
        for _ in range(60):
            if initialized_database_ready(container):
                ready = True
                break
            if time.monotonic() - start > 60:
                break
            time.sleep(0.5)
        if not ready or digest(backup) != verified:
            raise RuntimeError("IDENTITY_RESTORE_NOT_READY_OR_BACKUP_CHANGED")
        decrypted = subprocess.Popen(
            ["gpg", "--homedir", str(home), "--batch", "--pinentry-mode", "error", "--decrypt", str(backup)],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        try:
            restored = subprocess.run(
                [
                    "docker",
                    "--context",
                    common.CONTEXT,
                    "exec",
                    "-i",
                    container,
                    "pg_restore",
                    "-U",
                    "keycloak",
                    "-d",
                    "keycloak",
                    "--no-owner",
                    "--exit-on-error",
                ],
                stdin=decrypted.stdout,
                capture_output=True,
                timeout=180,
            )
            if decrypted.stdout is not None:
                decrypted.stdout.close()
            if restored.returncode or decrypted.wait(timeout=30):
                raise RuntimeError("IDENTITY_DATABASE_RESTORE_FAILED")
        finally:
            if decrypted.poll() is None:
                decrypted.kill()
                decrypted.wait()
        counts = common.docker(
            "exec",
            container,
            "psql",
            "-U",
            "keycloak",
            "-d",
            "keycloak",
            "-Atc",
            "SELECT (SELECT count(*) FROM realm),(SELECT count(*) FROM client),(SELECT count(*) FROM user_entity)",
        )
        return {
            "status": "DATABASE_RESTORED_APPLICATION_RECONCILIATION_REQUIRED",
            "project": project,
            "volume": volume,
            "backup_sha256_verified": verified,
            "counts": counts,
            "elapsed_seconds": round(time.monotonic() - start, 3),
            "network": "none",
            "public_ports": [],
            "public_cutover": False,
            "sessions_and_secrets_reconciled": False,
            "original_database_modified": False,
            "volume_retained": True,
        }
    finally:
        stop_restore_container(container)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backup", type=Path, required=True)
    parser.add_argument("--isolated-project", required=True)
    parser.add_argument("--gpg-home", type=Path, required=True)
    parser.add_argument("--signing-fingerprint", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if not args.apply:
        validate_restore_target(args.isolated_project, set())
        print('{"applied":false,"public_cutover":false}')
    else:
        print(json.dumps(restore_database(args.backup, args.isolated_project, args.gpg_home, args.signing_fingerprint)))


if __name__ == "__main__":
    main()
