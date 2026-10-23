"""Create project certificates once; incomplete state needs explicit recovery."""

import hashlib
import json
import os
import subprocess
from pathlib import Path

from . import common


def openssl(*args: str) -> str:
    result = subprocess.run(["openssl", *args], capture_output=True, text=True, timeout=60)
    if result.returncode:
        raise RuntimeError("IDENTITY_CERTIFICATE_OPERATION_FAILED")
    return result.stdout.strip()


def prepare(runtime: Path) -> dict[str, str]:
    runtime = common.private_runtime(runtime)
    pki = runtime / "pki"
    names = {"ca.crt", "ca.key", "manifest.json"} | {
        f"{s}.{ext}" for s in ("gateway", "keycloak", "postgres") for ext in ("crt", "key")
    }
    if pki.is_symlink():
        raise RuntimeError("IDENTITY_RUNTIME_SYMLINK_FORBIDDEN")
    if pki.exists():
        if not pki.is_dir() or {p.name for p in pki.iterdir()} != names:
            raise RuntimeError("IDENTITY_PKI_INCOMPLETE_NO_AUTOMATIC_OVERWRITE")
        if pki.stat().st_mode & 0o077 or any(p.is_symlink() or p.stat().st_mode & 0o077 for p in pki.iterdir()):
            raise RuntimeError("IDENTITY_PKI_PERMISSION_INVALID")
        manifest = json.loads((pki / "manifest.json").read_text())
        for service in ("gateway", "keycloak", "postgres"):
            crt, key = pki / f"{service}.crt", pki / f"{service}.key"
            openssl("verify", "-CAfile", str(pki / "ca.crt"), str(crt))
            openssl("x509", "-checkend", "2592000", "-noout", "-in", str(crt))
            if openssl("x509", "-in", str(crt), "-pubkey", "-noout") != openssl("pkey", "-in", str(key), "-pubout"):
                raise RuntimeError("IDENTITY_CERTIFICATE_KEY_MISMATCH")
        actual = {n: hashlib.sha256((pki / n).read_bytes()).hexdigest() for n in names if n.endswith(".crt")}
        if actual != manifest:
            raise RuntimeError("IDENTITY_CERTIFICATE_MANIFEST_MISMATCH")
        return actual
    pki.mkdir(mode=0o700)
    old_mask = os.umask(0o077)
    try:
        openssl(
            "req",
            "-x509",
            "-newkey",
            "rsa:3072",
            "-nodes",
            "-sha256",
            "-days",
            "3650",
            "-subj",
            "/CN=Media Trace Project Identity CA",
            "-addext",
            "basicConstraints=critical,CA:TRUE,pathlen:0",
            "-addext",
            "keyUsage=critical,keyCertSign,cRLSign",
            "-keyout",
            str(pki / "ca.key"),
            "-out",
            str(pki / "ca.crt"),
        )
        for service, san in (
            ("gateway", "IP:172.16.58.179,DNS:localhost,IP:127.0.0.1"),
            ("keycloak", "DNS:keycloak"),
            ("postgres", "DNS:identity-postgres"),
        ):
            csr, ext = pki / f"{service}.csr", pki / f"{service}.ext"
            ext.write_text(
                "basicConstraints=critical,CA:FALSE\nkeyUsage=critical,digitalSignature,keyEncipherment\nextendedKeyUsage=serverAuth\nsubjectAltName="
                + san
                + "\n"
            )
            openssl(
                "req",
                "-new",
                "-newkey",
                "rsa:3072",
                "-nodes",
                "-subj",
                f"/CN={service}",
                "-keyout",
                str(pki / f"{service}.key"),
                "-out",
                str(csr),
            )
            import secrets

            openssl(
                "x509",
                "-req",
                "-in",
                str(csr),
                "-CA",
                str(pki / "ca.crt"),
                "-CAkey",
                str(pki / "ca.key"),
                "-set_serial",
                str(secrets.randbits(128)),
                "-days",
                "90",
                "-sha256",
                "-extfile",
                str(ext),
                "-out",
                str(pki / f"{service}.crt"),
            )
            csr.unlink()
            ext.unlink()
        result = {n: hashlib.sha256((pki / n).read_bytes()).hexdigest() for n in names if n.endswith(".crt")}
        (pki / "manifest.json").write_text(json.dumps(result, indent=2) + "\n")
        for path in pki.iterdir():
            path.chmod(0o600)
        return result
    finally:
        os.umask(old_mask)
