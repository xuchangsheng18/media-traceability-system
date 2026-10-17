"""Install only allowlisted files into dedicated, content-verified secret volumes."""

import hashlib
import io
import subprocess
import tarfile
from pathlib import Path

from . import common


def verify_volume_contents(actual: dict[str, str], expected: dict[str, str]) -> None:
    if not expected or actual != expected:
        raise RuntimeError("IDENTITY_SECRET_VOLUME_CONTENT_MISMATCH")


def install(runtime: Path) -> dict[str, object]:
    runtime = common.private_runtime(runtime)
    result: dict[str, object] = {}
    for service, uid in (("gateway", 101), ("keycloak", 1000), ("postgres", 70)):
        volume = common.PROJECT + "_" + service + "-secrets" + ("-v2" if service in {"keycloak", "postgres"} else "")
        files = {
            "ca.crt": runtime / "pki/ca.crt",
            "tls.crt": runtime / f"pki/{service}.crt",
            "tls.key": runtime / f"pki/{service}.key",
        }
        conf = runtime / ("keycloak-v2.conf" if service == "keycloak" else service + ".conf")
        files[service + ".conf"] = conf
        if service == "postgres":
            for name in ("pg_hba.conf", "admin-password", "keycloak-password"):
                files[name] = runtime / name
        for path in files.values():
            if path.is_symlink() or not path.is_file() or path.stat().st_mode & 0o077:
                raise RuntimeError("IDENTITY_PRIVATE_FILE_UNSAFE")
        expected = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in files.items()}
        common.docker("volume", "create", "--label", "com.docker.compose.project=" + common.PROJECT, volume)
        base = [
            "docker",
            "--context",
            common.CONTEXT,
            "run",
            "--rm",
            "--network",
            "none",
            "--user",
            "0",
            "-i",
            "-v",
            volume + ":/target",
            common.image("postgres"),
            "sh",
            "-ec",
        ]
        # Existing content is never replaced, even if installation was interrupted.
        listing = subprocess.run(
            [*base, "find /target -mindepth 1 -maxdepth 1 -type f -exec sha256sum {} +"],
            capture_output=True,
            timeout=60,
            check=True,
        ).stdout.decode()
        if not listing.strip():
            buffer = io.BytesIO()
            with tarfile.open(fileobj=buffer, mode="w") as archive:
                for name, path in files.items():
                    item = tarfile.TarInfo(name)
                    data = path.read_bytes()
                    item.size, item.uid, item.gid, item.mode = len(data), uid, uid, 0o400
                    archive.addfile(item, io.BytesIO(data))
            subprocess.run(
                [
                    *base,
                    f'test -z "$(ls -A /target)"; tar -xf - -C /target; chown {uid}:{uid} /target; chmod 500 /target',
                ],
                input=buffer.getvalue(),
                capture_output=True,
                timeout=60,
                check=True,
            )
            listing = subprocess.run(
                [*base, "find /target -mindepth 1 -maxdepth 1 -type f -exec sha256sum {} +"],
                capture_output=True,
                timeout=60,
                check=True,
            ).stdout.decode()
        actual = {line.split()[1].removeprefix("/target/"): line.split()[0] for line in listing.splitlines()}
        verify_volume_contents(actual, expected)
        result[service] = {"volume": volume, "files_verified": len(expected), "uid": uid}
    return result
