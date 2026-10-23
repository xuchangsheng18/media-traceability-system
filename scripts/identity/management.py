"""Short-lived, MFA-proved operator sessions; no password grant or bootstrap fallback."""

import argparse
import base64
import hashlib
import json
import os
import re
import secrets
import shutil
import ssl
import subprocess
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qs, urlencode, urlsplit
from uuid import UUID, uuid4

import httpx
import yaml
from business_app.identity.config import private_file
from business_app.identity.tokens import unique_object

from . import common
from .handover import _master_protected
from .management_config import BASE, CLIENT_ID, REDIRECT_URI, setup, verify_configuration


def callback_code(target: str, *, state: str, issuer: str) -> str:
    try:
        parsed = urlsplit(target)
        if (
            parsed.scheme
            or parsed.netloc
            or parsed.path != "/identity-admin/callback"
            or parsed.fragment
            or len(target) > 8192
        ):
            raise ValueError()
        values = parse_qs(parsed.query, keep_blank_values=True, strict_parsing=True, max_num_fields=8)
        if not {"state", "code", "iss"} <= set(values) or set(values) - {"state", "code", "iss", "session_state"}:
            raise ValueError()
        if any(len(v) != 1 or not v[0] for v in values.values()):
            raise ValueError()
        if not secrets.compare_digest(values["state"][0], state) or values["iss"] != [issuer]:
            raise ValueError()
        code = values["code"][0]
        if len(code) > 4096 or any(ord(c) < 33 or ord(c) > 126 for c in code):
            raise ValueError()
        return code
    except (ValueError, TypeError, KeyError):
        raise RuntimeError("IDENTITY_MANAGEMENT_CALLBACK_INVALID") from None


def _node(executable: str | None = None) -> str:
    selected = executable or shutil.which("node")
    if not selected:
        raise RuntimeError("IDENTITY_MANAGEMENT_LOCKED_NODE_REQUIRED")
    expected = str(yaml.safe_load((common.ROOT / "config/versions.yaml").read_text())["frontend"]["node"])
    try:
        version = subprocess.run([selected, "--version"], capture_output=True, text=True, timeout=5)
        if version.returncode or version.stdout.strip() != "v" + expected:
            raise ValueError()
    except (OSError, ValueError, subprocess.SubprocessError):
        raise RuntimeError("IDENTITY_MANAGEMENT_LOCKED_NODE_REQUIRED") from None
    return selected


def _jwt_shape(token: str) -> None:
    if not isinstance(token, str) or len(token) > 16384:
        raise ValueError()
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError()
    for index, part in enumerate(parts):
        if not re.fullmatch(r"[A-Za-z0-9_-]+", part):
            raise ValueError()
        raw = base64.b64decode(part + "=" * (-len(part) % 4), altchars=b"-_", validate=True)
        if base64.urlsafe_b64encode(raw).decode().rstrip("=") != part:
            raise ValueError()
        if index < 2 and not isinstance(json.loads(raw, object_pairs_hook=unique_object), dict):
            raise ValueError()


def verify_access(
    token: str,
    jwks: dict[str, Any],
    *,
    issuer: str,
    node_executable: str | None = None,
    id_token: str | None = None,
    nonce: str | None = None,
) -> dict[str, Any]:
    try:
        _jwt_shape(token)
        request: dict[str, Any] = {"token": token, "jwks": jwks, "expected": {"issuer": issuer}}
        if id_token is not None:
            _jwt_shape(id_token)
            if not isinstance(nonce, str) or not nonce:
                raise ValueError()
            request.update(id_token=id_token)
            request["expected"]["nonce"] = nonce
        run = subprocess.run(
            [_node(node_executable), str(common.ROOT / "tools/identity_admin_tokens.mjs")],
            input=json.dumps(request),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if run.returncode or len(run.stdout) > 1024:
            raise ValueError()
        result = json.loads(run.stdout, object_pairs_hook=unique_object)
        if set(result) != {"subject", "expires_at", "session_id"}:
            raise ValueError()
        UUID(result["subject"])
        if not isinstance(result["session_id"], str) or not re.fullmatch(r"[\x20-\x7e]{1,256}", result["session_id"]):
            raise ValueError()
        return result
    except (RuntimeError, OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError):
        raise RuntimeError("IDENTITY_MANAGEMENT_TOKEN_INVALID") from None


def _http() -> httpx.Client:
    runtime = common.private_runtime(common.RUNTIME)
    return httpx.Client(
        verify=ssl.create_default_context(cafile=str(runtime / "pki/ca.crt")),
        trust_env=False,
        follow_redirects=False,
        timeout=10,
    )


def _json(http: httpx.Client, method: str, url: str, **kwargs: Any) -> dict[str, Any]:
    try:
        with http.stream(method, url, **kwargs) as response:
            if response.status_code != 200:
                raise ValueError()
            raw = bytearray()
            for chunk in response.iter_bytes(1024):
                raw.extend(chunk)
                if len(raw) > 65536:
                    raise ValueError()
        result = json.loads(raw, object_pairs_hook=unique_object)
        if not isinstance(result, dict):
            raise ValueError()
        return result
    except (httpx.HTTPError, ValueError, TypeError):
        raise RuntimeError("IDENTITY_MANAGEMENT_PROVIDER_DENIED_OR_UNAVAILABLE") from None


def _sessions() -> Path:
    runtime = common.private_runtime(common.RUNTIME)
    directory = runtime / "admin-sessions"
    if directory.is_symlink():
        raise RuntimeError("IDENTITY_MANAGEMENT_SESSION_INVALID")
    directory.mkdir(mode=0o700, exist_ok=True)
    if directory.stat().st_uid != os.geteuid() or directory.stat().st_mode & 0o077:
        raise RuntimeError("IDENTITY_MANAGEMENT_SESSION_INVALID")
    return directory


def session_record(path: Path) -> dict[str, Any]:
    try:
        root = _sessions()
        if path.parent != root:
            raise ValueError()
        result = json.loads(private_file(path, root), object_pairs_hook=unique_object)
        if set(result) != {"version", "issuer", "client_id", "username", "access_token", "subject", "expires_at"}:
            raise ValueError()
        if (
            result["version"] != 1
            or result["issuer"] != common.PUBLIC_URL + "/realms/master"
            or result["client_id"] != CLIENT_ID
            or not isinstance(result["username"], str)
            or not re.fullmatch(r"[a-z][a-z0-9._-]{2,63}", result["username"])
        ):
            raise ValueError()
        if type(result["expires_at"]) is not int or result["expires_at"] <= time.time():
            raise ValueError()
        _jwt_shape(result["access_token"])
        UUID(result["subject"])
        return result
    except (RuntimeError, OSError, ValueError, TypeError, KeyError):
        raise RuntimeError("IDENTITY_MANAGEMENT_SESSION_INVALID_OR_EXPIRED") from None


class _Reader:
    def __init__(self, client: httpx.Client):
        self.client = client

    def request(
        self, method: str, path: str, *, body: Any = None, expected: tuple[int, ...] = (200,)
    ) -> httpx.Response:
        if (
            method != "GET"
            or body is not None
            or not re.fullmatch(r"/admin/[A-Za-z0-9/_:.-]+", path)
            or ".." in path
            or "//" in path
        ):
            raise RuntimeError("IDENTITY_MANAGEMENT_PATH_FORBIDDEN")
        try:
            response = self.client.get(common.ADMIN_URL + path)
            if response.status_code not in expected:
                raise ValueError()
            return response
        except (httpx.HTTPError, ValueError):
            raise RuntimeError("IDENTITY_MANAGEMENT_AUTHORIZATION_DENIED_OR_UNAVAILABLE") from None


class ManagedAdmin:
    """Same request port as AdminClient; only a selected signed short-lived session."""

    def __init__(self, path: Path):
        self.record = session_record(path)  # Before any legacy credential/TLS/network access.
        self.path = path
        self.client = _http()
        try:
            jwks = _json(self.client, "GET", common.PUBLIC_URL + "/realms/master/protocol/openid-connect/certs")
            self.verified = verify_access(self.record["access_token"], jwks, issuer=self.record["issuer"])
            if (
                self.verified["subject"] != self.record["subject"]
                or self.verified["expires_at"] != self.record["expires_at"]
            ):
                raise ValueError()
            self.client.headers["Authorization"] = "Bearer " + self.record["access_token"]
            self._reader = _Reader(self.client)
            self._authorize()
            verify_configuration(self._reader)
        except (RuntimeError, httpx.HTTPError, ValueError, KeyError, TypeError):
            self.close()
            raise RuntimeError("IDENTITY_MANAGEMENT_SESSION_NOT_AUTHORIZED") from None

    def _authorize(self) -> None:
        try:
            if self.record["expires_at"] <= time.time():
                raise ValueError()
            info = _json(self.client, "GET", common.PUBLIC_URL + "/realms/master/protocol/openid-connect/userinfo")
            if info.get("sub") != self.record["subject"]:
                raise ValueError()
            realm = self._reader.request("GET", BASE).json()
            user = self._reader.request("GET", BASE + "/users/" + self.record["subject"]).json()
            if (
                not _master_protected(realm)
                or user.get("id") != self.record["subject"]
                or user.get("username") != self.record["username"]
                or user.get("enabled") is not True
                or user.get("requiredActions") != []
            ):
                raise ValueError()
            credentials = self._reader.request("GET", BASE + "/users/" + self.record["subject"] + "/credentials").json()
            roles = self._reader.request(
                "GET", BASE + "/users/" + self.record["subject"] + "/role-mappings/realm/composite"
            ).json()
            if not any(c.get("type") == "otp" for c in credentials) or not any(r.get("name") == "admin" for r in roles):
                raise ValueError()
        except (RuntimeError, httpx.HTTPError, ValueError, KeyError, TypeError, AttributeError):
            raise RuntimeError("IDENTITY_MANAGEMENT_AUTHORIZATION_DENIED_OR_UNAVAILABLE") from None

    def request(
        self, method: str, path: str, *, body: Any = None, expected: tuple[int, ...] = (200,)
    ) -> httpx.Response:
        if (
            method not in {"GET", "POST", "PUT", "DELETE"}
            or not re.fullmatch(r"/admin/[A-Za-z0-9/_:.-]+", path)
            or ".." in path
            or "//" in path
        ):
            raise RuntimeError("IDENTITY_MANAGEMENT_PATH_FORBIDDEN")
        self._authorize()
        try:
            response = self.client.request(method, common.ADMIN_URL + path, json=body)
            if response.status_code in {401, 403} or response.status_code not in expected:
                raise ValueError()
            return response
        except (httpx.HTTPError, ValueError):
            raise RuntimeError("IDENTITY_MANAGEMENT_OPERATION_DENIED_OR_UNAVAILABLE") from None

    def close(self) -> None:
        self.client.headers.clear()
        self.client.close()


def login_session(*, username: str, announce: Callable[[str], None]) -> Path:
    """Only the browser sees the password/OTP; callback and token never go to logs."""
    if not re.fullmatch(r"[a-z][a-z0-9._-]{2,63}", username):
        raise RuntimeError("IDENTITY_MANAGEMENT_USERNAME_INVALID")
    _node()
    issuer = common.PUBLIC_URL + "/realms/master"
    state, nonce, verifier = secrets.token_urlsafe(32), secrets.token_urlsafe(32), secrets.token_urlsafe(48)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    received: list[str] = []

    class Callback(BaseHTTPRequestHandler):
        def setup(self) -> None:
            self.request.settimeout(2)
            super().setup()

        def log_message(self, format: str, *args: Any) -> None:
            pass  # Neither successful nor rejected request query strings are logged.

        def do_GET(self) -> None:
            try:
                if self.headers.get("Host") != "127.0.0.1:18765" or received:
                    raise RuntimeError()
                code = callback_code(self.path, state=state, issuer=issuer)
                received.append(code)
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Referrer-Policy", "no-referrer")
                self.end_headers()
                self.wfile.write(b"Callback received. Return to the operator terminal.")
            except RuntimeError:
                self.send_response(400)
                self.send_header("Cache-Control", "no-store")
                self.end_headers()

    try:
        with HTTPServer(("127.0.0.1", 18765), Callback) as server:
            server.timeout = 1
            announce(
                issuer
                + "/protocol/openid-connect/auth?"
                + urlencode(
                    {
                        "client_id": CLIENT_ID,
                        "redirect_uri": REDIRECT_URI,
                        "response_type": "code",
                        "scope": "openid",
                        "state": state,
                        "nonce": nonce,
                        "code_challenge": challenge,
                        "code_challenge_method": "S256",
                        "prompt": "login",
                        "max_age": "0",
                        "login_hint": username,
                    }
                )
            )
            deadline = time.monotonic() + 300
            while not received and time.monotonic() < deadline:
                server.handle_request()
        if not received:
            raise RuntimeError("IDENTITY_MANAGEMENT_LOGIN_NOT_COMPLETED")
        with _http() as http:
            values = _json(
                http,
                "POST",
                issuer + "/protocol/openid-connect/token",
                data={
                    "grant_type": "authorization_code",
                    "client_id": CLIENT_ID,
                    "redirect_uri": REDIRECT_URI,
                    "code": received[0],
                    "code_verifier": verifier,
                },
            )
            if "refresh_token" in values or values.get("token_type", "").lower() != "bearer":
                raise RuntimeError("IDENTITY_MANAGEMENT_UNEXPECTED_TOKEN_GRANT")
            jwks = _json(http, "GET", issuer + "/protocol/openid-connect/certs")
            verified = verify_access(
                values["access_token"], jwks, issuer=issuer, id_token=values["id_token"], nonce=nonce
            )
        record = {
            "version": 1,
            "issuer": issuer,
            "client_id": CLIENT_ID,
            "username": username,
            "access_token": values["access_token"],
            "subject": verified["subject"],
            "expires_at": verified["expires_at"],
        }
        path = _sessions() / (uuid4().hex + ".json")
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "w") as destination:
            json.dump(record, destination)
            destination.flush()
            os.fsync(destination.fileno())
        try:
            manager = ManagedAdmin(path)
            manager.close()
        except RuntimeError:
            path.unlink()
            raise
        return path
    except (RuntimeError, OSError, httpx.HTTPError, ValueError, KeyError, TypeError):
        raise RuntimeError("IDENTITY_MANAGEMENT_LOGIN_NOT_CONFIRMED") from None


def main() -> int:
    parser = argparse.ArgumentParser(description="Explicit MFA operator management; no bootstrap retirement.")
    parser.add_argument("action", choices=["setup", "login", "inspect"])
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--username")
    parser.add_argument("--session-file", type=Path)
    args = parser.parse_args()
    if not args.apply and args.action != "inspect":
        print(
            json.dumps({"applied": False, "action": args.action, "bootstrap_deleted": False, "formal_accepted": False})
        )
        return 0
    if args.action in {"setup", "login"} and (not sys.stdin.isatty() or not sys.stderr.isatty()):
        print('{"status":"FAIL","error":"IDENTITY_MANAGEMENT_INTERACTIVE_TERMINAL_REQUIRED"}')
        return 1
    try:
        if args.action == "setup":
            from .provision import AdminClient

            admin = AdminClient(session_file=args.session_file)
            try:
                print(json.dumps(setup(admin)))
            finally:
                admin.close()
        elif args.action == "login":
            if args.username is None:
                parser.error("login requires --username")
            path = login_session(
                username=args.username, announce=lambda url: print("Open in your trusted browser:\n" + url, flush=True)
            )
            print(
                json.dumps(
                    {
                        "session_file": str(path),
                        "password_or_OTP_collected": False,
                        "refresh_token_persisted": False,
                        "formal_accepted": False,
                    }
                )
            )
        else:
            selected = args.session_file or os.environ.get("MT_IDENTITY_ADMIN_SESSION")
            if not selected:
                raise RuntimeError("IDENTITY_MANAGEMENT_SESSION_REQUIRED")
            admin_session = ManagedAdmin(Path(selected))
            try:
                clients = admin_session.request("GET", BASE + "/clients").json()
                print(
                    json.dumps(
                        {
                            "signed_mfa_management_session": True,
                            "bootstrap_present": any(c.get("clientId") == "bootstrap-project-service" for c in clients),
                            "formal_accepted": False,
                        }
                    )
                )
            finally:
                admin_session.close()
        return 0
    except (RuntimeError, OSError, ValueError, httpx.HTTPError):
        print(
            '{"status":"FAIL","error":"IDENTITY_MANAGEMENT_OPERATION_NOT_CONFIRMED","bootstrap_fallback":false,"formal_accepted":false}'
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
