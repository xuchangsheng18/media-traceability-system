"""Real browser PKCE probe; credentials/tokens stay in memory or private temp files."""

import argparse
import base64
import hashlib
import json
import os
import secrets
import ssl
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import httpx
from business_app.identity.config import private_file
from business_app.identity.tokens import unique_object

ROOT = Path(__file__).resolve().parents[1]
REDIRECT = "https://localhost:18444/identity-test/callback"


class PrivateValue(str):
    def __repr__(self) -> str:
        return "<identity-probe-private-value>"


@dataclass(frozen=True)
class AuthorizationCode:
    code: PrivateValue = field(repr=False)
    verifier: PrivateValue = field(repr=False)
    nonce: PrivateValue = field(repr=False)


@dataclass(frozen=True)
class TokenBundle:
    access_token: PrivateValue = field(repr=False)
    refresh_token: PrivateValue = field(repr=False)
    id_token: PrivateValue = field(repr=False)
    authorization: AuthorizationCode = field(repr=False)
    subject: PrivateValue = field(repr=False)


def validate_probe_config(config: dict[str, Any]) -> None:
    try:
        assert config["public_url"] == "https://172.16.58.179:18443"
        assert config["admin_url"] == "https://localhost:18444"
        assert config["issuer"].startswith(config["public_url"] + "/realms/media-trace-acceptance-")
        assert config["client_id"] == "media-trace-probe"
        for name in ("ca_file", "node_executable", "certutil", "browser_cache", "private_test_root"):
            path = Path(config[name])
            assert path.is_absolute() and not any(p.is_symlink() for p in [path, *path.parents])
        private = Path(config["private_test_root"])
        assert private.is_dir() and private.stat().st_mode & 0o077 == 0 and private.stat().st_uid == os.geteuid()
    except (AssertionError, KeyError, TypeError, OSError, AttributeError):
        raise RuntimeError("IDENTITY_PROBE_CONFIGURATION_INVALID") from None


def private_json(path: Path, values: dict[str, Any]) -> None:
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w") as output:
        json.dump(values, output)


def node(config: dict[str, Any], path: Path) -> None:
    result = subprocess.run(
        [config["node_executable"], str(ROOT / "tools/identity_oidc_browser.mjs"), str(path)],
        env=dict(os.environ, PLAYWRIGHT_BROWSERS_PATH=config["browser_cache"]),
        capture_output=True,
        timeout=90,
    )
    if result.returncode:
        detail = next(
            (
                line
                for line in result.stderr.decode(errors="replace").splitlines()
                if line.startswith("IDENTITY_BROWSER_PROBE_FAILED:")
            ),
            "IDENTITY_BROWSER_PROBE_FAILED",
        )
        raise RuntimeError("IDENTITY_REAL_BROWSER_PROBE_FAILED:" + detail)


def obtain_code(config: dict[str, Any]) -> AuthorizationCode:
    validate_probe_config(config)
    verifier = secrets.token_urlsafe(48)
    nonce, state = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    with tempfile.TemporaryDirectory(prefix="browser-", dir=config["private_test_root"]) as name:
        root = Path(name)
        home = root / "home"
        db = home / ".pki/nssdb"
        db.mkdir(parents=True, mode=0o700)
        home.chmod(0o700)
        for args in (
            ["-N", "--empty-password"],
            ["-A", "-n", "media-trace-project-ca", "-t", "C,,", "-i", config["ca_file"]],
        ):
            result = subprocess.run(
                [config["certutil"], "-d", "sql:" + str(db), *args], capture_output=True, timeout=15
            )
            if result.returncode:
                raise RuntimeError("IDENTITY_ISOLATED_BROWSER_TRUST_FAILED")
        authorization = (
            config["issuer"]
            + "/protocol/openid-connect/auth?"
            + urlencode(
                {
                    "client_id": config["client_id"],
                    "redirect_uri": REDIRECT,
                    "response_type": "code",
                    "scope": "openid",
                    "state": state,
                    "nonce": nonce,
                    "code_challenge": challenge,
                    "code_challenge_method": "S256",
                }
            )
        )
        path = root / "browser.json"
        callback = root / "callback.json"
        private_json(
            path,
            {
                "action": "login",
                "authorization_url": authorization,
                "redirect_uri": REDIRECT,
                "browser_home": str(home),
                "callback_file": str(callback),
                "username": config["username"],
                "password": config["password"],
            },
        )
        node(config, path)
        received = json.loads(private_file(callback, root).decode(), object_pairs_hook=unique_object)
        if (
            set(received) != {"code", "state"}
            or not secrets.compare_digest(received["state"], state)
            or not received["code"]
        ):
            raise RuntimeError("IDENTITY_CALLBACK_STATE_INVALID")
        return AuthorizationCode(PrivateValue(received["code"]), PrivateValue(verifier), PrivateValue(nonce))


def client(config: dict[str, Any]) -> httpx.Client:
    return httpx.Client(
        verify=ssl.create_default_context(cafile=config["ca_file"]), trust_env=False, follow_redirects=False, timeout=10
    )


def json_request(http: httpx.Client, method: str, url: str, **kwargs: Any) -> dict[str, Any]:
    try:
        with http.stream(method, url, **kwargs) as response:
            if response.status_code != 200:
                raise RuntimeError("IDENTITY_PROTOCOL_OPERATION_FAILED")
            body = bytearray()
            for chunk in response.iter_bytes(4096):
                body.extend(chunk)
                if len(body) > 65536:
                    raise RuntimeError("IDENTITY_PROTOCOL_RESPONSE_TOO_LARGE")
        values = json.loads(body.decode(), object_pairs_hook=unique_object)
        if not isinstance(values, dict):
            raise ValueError()
        return values
    except (httpx.HTTPError, ValueError, UnicodeError):
        raise RuntimeError("IDENTITY_PROTOCOL_OPERATION_FAILED") from None


def introspect(config: dict[str, Any], token: str) -> dict[str, Any]:
    with client(config) as http:
        return json_request(
            http,
            "POST",
            config["issuer"] + "/protocol/openid-connect/token/introspect",
            auth=httpx.BasicAuth("media-trace-api", config["api_secret"]),
            data={"token": token, "token_type_hint": "access_token"},
        )


def exchange(config: dict[str, Any], code: AuthorizationCode, *, verifier_override: str | None = None) -> TokenBundle:
    with client(config) as http:
        values = json_request(
            http,
            "POST",
            config["issuer"] + "/protocol/openid-connect/token",
            data={
                "grant_type": "authorization_code",
                "client_id": config["client_id"],
                "redirect_uri": REDIRECT,
                "code": code.code,
                "code_verifier": verifier_override if verifier_override is not None else code.verifier,
            },
        )
        claims = introspect(config, values["access_token"])
        if claims.get("active") is not True or claims.get("iss") != config["issuer"]:
            raise RuntimeError("IDENTITY_LIVE_ACCESS_TOKEN_INVALID")
        jwks = json_request(http, "GET", config["issuer"] + "/protocol/openid-connect/certs")
        with tempfile.TemporaryDirectory(prefix="verify-", dir=config["private_test_root"]) as name:
            path = Path(name) / "verify.json"
            private_json(
                path,
                {
                    "action": "verify",
                    "token": values["id_token"],
                    "jwks": jwks,
                    "expected": {
                        "issuer": config["issuer"],
                        "audience": config["client_id"],
                        "nonce": code.nonce,
                        "subject": claims["sub"],
                    },
                },
            )
            node(config, path)
        return TokenBundle(
            PrivateValue(values["access_token"]),
            PrivateValue(values["refresh_token"]),
            PrivateValue(values["id_token"]),
            code,
            PrivateValue(claims["sub"]),
        )


def authorization_code_login(config: dict[str, Any]) -> TokenBundle:
    return exchange(config, obtain_code(config))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    config = json.loads(private_file(args.config, args.config.parent).decode(), object_pairs_hook=unique_object)
    start = time.monotonic()
    authorization_code_login(config)
    private_json(
        args.report,
        {
            "status": "PASS",
            "flow": "real_browser_authorization_code_pkce",
            "tls_verified": True,
            "id_token_signature_and_nonce_verified": True,
            "elapsed_seconds": round(time.monotonic() - start, 3),
            "formal_accepted": False,
        },
    )
    print('{"status":"PASS","tokens_printed":false}')


if __name__ == "__main__":
    main()
