"""Idempotent realm initialization with a temporary master service client."""

import argparse
import copy
import json
import os
import secrets
import ssl
from pathlib import Path
from typing import Any

import httpx

from . import common


def validate_existing(actual: dict[str, Any], expected: dict[str, Any]) -> None:
    for key, value in expected.items():
        if isinstance(value, dict) and isinstance(actual.get(key), dict):
            validate_existing(actual[key], value)
        elif actual.get(key) != value:
            raise RuntimeError("IDENTITY_EXISTING_CONFIGURATION_DIFFERS")


class AdminClient:
    def __init__(self, *, session_file: Path | None = None) -> None:
        self.management = None
        selected = session_file if session_file is not None else os.environ.get("MT_IDENTITY_ADMIN_SESSION")
        if selected is not None:
            from .management import ManagedAdmin

            self.management = ManagedAdmin(Path(selected))
            self.client = self.management.client
            return  # A selected session can never fall back to bootstrap.
        runtime = common.private_runtime(common.RUNTIME)
        creds = json.loads((runtime / "credentials.json").read_text())
        if "bootstrap_admin" not in creds or (runtime / "bootstrap-retired.json").exists():
            raise RuntimeError("IDENTITY_MANAGEMENT_SESSION_REQUIRED")
        context = ssl.create_default_context(cafile=str(runtime / "pki/ca.crt"))
        self.client = httpx.Client(verify=context, trust_env=False, follow_redirects=False, timeout=10)
        try:
            response = self.client.post(
                common.PUBLIC_URL + "/realms/master/protocol/openid-connect/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": "bootstrap-project-service",
                    "client_secret": creds["bootstrap_admin"],
                },
            )
            if response.status_code != 200:
                raise RuntimeError("IDENTITY_BOOTSTRAP_AUTHENTICATION_FAILED")
            self.client.headers["Authorization"] = "Bearer " + response.json()["access_token"]
        except Exception:
            self.client.close()
            raise RuntimeError("IDENTITY_BOOTSTRAP_AUTHENTICATION_FAILED") from None

    def request(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | list[dict[str, Any]] | None = None,
        expected: tuple[int, ...] = (200,),
    ) -> httpx.Response:
        if not path.startswith("/admin/") or ".." in path or "?" in path:
            raise RuntimeError("IDENTITY_ADMIN_PATH_FORBIDDEN")
        if self.management is not None:
            return self.management.request(method, path, body=body, expected=expected)
        response = self.client.request(method, common.ADMIN_URL + path, json=body)
        if response.status_code not in expected:
            raise RuntimeError("IDENTITY_ADMIN_OPERATION_FAILED")
        return response

    def close(self) -> None:
        self.client.close()


def apply() -> dict[str, object]:
    runtime = common.private_runtime(common.RUNTIME)
    private = runtime / "api-client-secret"
    if not private.exists():
        fd = os.open(private, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as output:
            output.write(secrets.token_hex(32))
    if private.is_symlink() or private.stat().st_mode & 0o077:
        raise RuntimeError("IDENTITY_CLIENT_SECRET_PERMISSION_INVALID")
    realm = json.loads((common.ROOT / "config/identity/realm.template.json").read_text())
    desired = copy.deepcopy(realm)
    desired["clients"][0]["secret"] = private.read_text()
    admin = AdminClient()
    try:
        response = admin.request("GET", "/admin/realms/media-trace", expected=(200, 404))
        if response.status_code == 404:
            admin.request("POST", "/admin/realms", body=desired, expected=(201,))
        actual = admin.request("GET", "/admin/realms/media-trace").json()
        validate_existing(
            actual, {k: v for k, v in realm.items() if k not in {"clients", "defaultOptionalClientScopes"}}
        )
        clients = admin.request("GET", "/admin/realms/media-trace/clients").json()
        for wanted in realm["clients"]:
            current = next(c for c in clients if c["clientId"] == wanted["clientId"])
            full = admin.request("GET", "/admin/realms/media-trace/clients/" + current["id"]).json()
            if (
                wanted["clientId"] == "media-trace-web"
                and wanted["enabled"] is False
                and wanted["defaultClientScopes"] == ["basic"]
                and full.get("defaultClientScopes") == []
            ):
                if admin.request("GET", "/admin/realms/media-trace/users/count").json() != 0:
                    raise RuntimeError("IDENTITY_EXISTING_CONFIGURATION_DIFFERS")
                scopes = admin.request("GET", "/admin/realms/media-trace/client-scopes").json()
                basic = next(s for s in scopes if s["name"] == "basic")
                admin.request(
                    "PUT",
                    "/admin/realms/media-trace/clients/" + current["id"] + "/default-client-scopes/" + basic["id"],
                    expected=(204,),
                )
                full = admin.request("GET", "/admin/realms/media-trace/clients/" + current["id"]).json()
            validate_existing(full, {k: v for k, v in wanted.items() if k != "protocolMappers"})
            attributes = full.get("attributes") or {}
            expected_attributes = wanted.get("attributes") or {}
            permitted_defaults = {"realm_client": "false", "post.logout.redirect.uris": "+"}
            for key, value in attributes.items():
                if key not in expected_attributes and permitted_defaults.get(key) != value:
                    raise RuntimeError("IDENTITY_CLIENT_DEFAULT_ATTRIBUTE_DIFFERS")
            actual_mappers = {m["name"]: m for m in full.get("protocolMappers", [])}
            expected_mappers = {m["name"]: m for m in wanted.get("protocolMappers", [])}
            if set(actual_mappers) != set(expected_mappers):
                raise RuntimeError("IDENTITY_CLIENT_MAPPER_DIFFERS")
            for name, mapper in expected_mappers.items():
                validate_existing(actual_mappers[name], mapper)
            if wanted["clientId"] == "media-trace-api":
                secret = admin.request(
                    "GET", "/admin/realms/media-trace/clients/" + current["id"] + "/client-secret"
                ).json()["value"]
                if secret != private.read_text():
                    raise RuntimeError("IDENTITY_CLIENT_SECRET_DIFFERS")
        scopes = admin.request("GET", "/admin/realms/media-trace/client-scopes").json()
        for scope in scopes:
            if scope["name"] == "offline_access":
                admin.request("DELETE", "/admin/realms/media-trace/client-scopes/" + scope["id"], expected=(204,))
        # A machine bootstrap avoids enabling password grant for human admin accounts.
        master = admin.request("GET", "/admin/realms/master/clients").json()
        cli = next(c for c in master if c["clientId"] == "admin-cli")
        admin.request(
            "PUT",
            "/admin/realms/master/clients/" + cli["id"],
            body={"directAccessGrantsEnabled": False},
            expected=(204,),
        )
        return {
            "realm": "media-trace",
            "configured": True,
            "business_permissions_seeded": False,
            "real_admin_handover": "NOT_COMPLETED_NO_CONFIRMED_ACCOUNT",
        }
    finally:
        admin.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    print(json.dumps(apply() if args.apply else {"applied": False, "operation": "configure_media_trace_realm"}))


if __name__ == "__main__":
    main()
