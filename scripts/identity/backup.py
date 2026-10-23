"""Stream signed/encrypted identity backups; never stage plaintext database dumps."""

import argparse
import datetime
import hashlib
import io
import json
import os
import re
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import BinaryIO, cast
from uuid import uuid4

from . import common
from .control import command


def private_home(home: Path) -> None:
    if (
        not home.is_absolute()
        or not home.is_dir()
        or home.stat().st_mode & 0o077
        or home.stat().st_uid != os.geteuid()
        or any(p.is_symlink() for p in [home, *home.parents])
    ):
        raise RuntimeError("IDENTITY_RECOVERY_KEY_HOME_UNSAFE")


def fingerprint(home: Path, public_key: Path) -> str:
    if public_key.is_symlink() or not public_key.is_file() or public_key.stat().st_size > 65536:
        raise RuntimeError("IDENTITY_RECIPIENT_INVALID")
    result = subprocess.run(
        ["gpg", "--homedir", str(home), "--batch", "--with-colons", "--show-keys", str(public_key)],
        capture_output=True,
        text=True,
        timeout=20,
    )
    rows = result.stdout.splitlines()
    if result.returncode or sum(r.startswith("pub:") for r in rows) != 1 or any(r.startswith("sec:") for r in rows):
        raise RuntimeError("IDENTITY_RECIPIENT_INVALID")
    value = next((r.split(":")[9] for r in rows if r.startswith("fpr:")), "")
    if re.fullmatch(r"[A-Fa-f0-9]{40}(?:[A-Fa-f0-9]{24})?", value) is None:
        raise RuntimeError("IDENTITY_RECIPIENT_FINGERPRINT_INVALID")
    return value


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def encrypt_stream(
    source: BinaryIO,
    destination: Path,
    recipient: Path,
    gpg_home: Path,
    signing_fingerprint: str,
    *,
    postcheck: Callable[[], bool] | None = None,
) -> dict[str, object]:
    private_home(gpg_home)
    if (
        not destination.is_absolute()
        or destination.suffix != ".gpg"
        or destination.exists()
        or any(p.is_symlink() for p in [destination, *destination.parents])
        or re.fullmatch(r"[A-Fa-f0-9]{40}(?:[A-Fa-f0-9]{24})?", signing_fingerprint) is None
    ):
        raise RuntimeError("IDENTITY_BACKUP_TARGET_INVALID")
    recipient_id = fingerprint(gpg_home, recipient)
    imported = subprocess.run(
        ["gpg", "--homedir", str(gpg_home), "--batch", "--import", str(recipient)], capture_output=True, timeout=20
    )
    if imported.returncode:
        raise RuntimeError("IDENTITY_BACKUP_RECIPIENT_IMPORT_FAILED")
    partial = destination.with_name(destination.name + ".partial")
    process = None
    try:
        fd = os.open(partial, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, "wb") as encrypted:
            process = subprocess.Popen(
                [
                    "gpg",
                    "--homedir",
                    str(gpg_home),
                    "--batch",
                    "--pinentry-mode",
                    "error",
                    "--trust-model",
                    "always",
                    "--recipient",
                    recipient_id,
                    "--local-user",
                    signing_fingerprint,
                    "--output",
                    "-",
                    "--encrypt",
                    "--sign",
                ],
                stdin=subprocess.PIPE,
                stdout=encrypted,
                stderr=subprocess.PIPE,
            )
            if process.stdin is None:
                raise RuntimeError("IDENTITY_ENCRYPTION_PIPE_UNAVAILABLE")
            for chunk in iter(lambda: source.read(65536), b""):
                process.stdin.write(chunk)
            process.stdin.close()
            process.stdin = None
            process.communicate(timeout=120)
            if process.returncode or (postcheck is not None and not postcheck()):
                raise RuntimeError("IDENTITY_BACKUP_ENCRYPTION_OR_SOURCE_FAILED")
            encrypted.flush()
            os.fsync(encrypted.fileno())
        os.link(partial, destination)  # Atomic commit without replacing an existing backup.
        return {
            "encrypted": True,
            "signed": True,
            "sha256": digest(destination),
            "recipient_fingerprint": recipient_id,
            "signing_fingerprint": signing_fingerprint.upper(),
            "size_bytes": destination.stat().st_size,
        }
    except (OSError, subprocess.SubprocessError):
        raise RuntimeError("IDENTITY_BACKUP_ENCRYPTION_FAILED") from None
    finally:
        if process is not None and process.poll() is None:
            process.kill()
            process.wait()
        if partial.exists():
            partial.unlink()


def run_backup(recipient: Path, output: Path, gpg_home: Path, signer: str) -> dict[str, object]:
    runtime = common.private_runtime(common.RUNTIME)
    if output.absolute() != runtime.parent / "identity-backups" or output.is_symlink():
        raise RuntimeError("EXPLICIT_IDENTITY_HOST_BACKUP_DIRECTORY_REQUIRED")
    output.mkdir(mode=0o700, exist_ok=True)
    if output.stat().st_mode & 0o077:
        raise RuntimeError("IDENTITY_BACKUP_DIRECTORY_PERMISSION_INVALID")
    identity = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    dump_path = output / (identity + ".database.gpg")
    dump = subprocess.Popen(
        command("exec", "-T", "identity-postgres", "pg_dump", "-U", "identity_admin", "-d", "keycloak", "-Fc"),
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    try:
        if dump.stdout is None:
            raise RuntimeError("IDENTITY_DUMP_PIPE_UNAVAILABLE")
        database = encrypt_stream(
            cast(BinaryIO, dump.stdout),
            dump_path,
            recipient,
            gpg_home,
            signer,
            postcheck=lambda: dump.wait(timeout=30) == 0,
        )
    finally:
        if dump.stdout is not None:
            dump.stdout.close()
        if dump.poll() is None:
            dump.kill()
            dump.wait()
    names = [
        "credentials.json",
        "api-client-secret",
        "keycloak-v2.conf",
        "postgres.conf",
        "pg_hba.conf",
        "gateway.conf",
    ]
    names += ["pki/" + p.name for p in (runtime / "pki").iterdir() if p.is_file() and p.name != "ca.key"]
    import base64

    configuration = {n: base64.b64encode((runtime / n).read_bytes()).decode() for n in names}
    configuration["versions.json"] = base64.b64encode(
        (common.ROOT / "config/identity/versions.json").read_bytes()
    ).decode()
    config = encrypt_stream(
        io.BytesIO(json.dumps(configuration).encode()),
        output / (identity + ".configuration.gpg"),
        recipient,
        gpg_home,
        signer,
    )
    ca = encrypt_stream(
        io.BytesIO((runtime / "pki/ca.key").read_bytes()),
        output / (identity + ".ca-recovery.gpg"),
        recipient,
        gpg_home,
        signer,
    )
    return {
        "status": "PASS",
        "backup_id": identity,
        "database_backup": str(dump_path),
        "database": database,
        "configuration": config,
        "ca_recovery": ca,
        "plaintext_dump_written": False,
        "business_database_included": False,
        "host_backup_not_docker_volume": True,
        "offsite_recovery_verified": False,
        "formal_accepted": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--recipient", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--gpg-home", type=Path, required=True)
    parser.add_argument("--signing-fingerprint", required=True)
    args = parser.parse_args()
    print(json.dumps(run_backup(args.recipient, args.output, args.gpg_home, args.signing_fingerprint)))


if __name__ == "__main__":
    main()
