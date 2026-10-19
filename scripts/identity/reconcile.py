"""Reconcile a disposable restored realm; no shared-realm or cutover entry point."""

import re
import time
from dataclasses import dataclass, field
from typing import Any, Protocol

import httpx


class RecoveryAdmin(Protocol):
    def request(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | list[dict[str, Any]] | None = None,
        expected: tuple[int, ...] = (200,),
    ) -> httpx.Response: ...


@dataclass(frozen=True)
class Reconciliation:
    client_secret: str = field(repr=False)
    not_before: int
    retired_signing_providers: int

    def public_report(self) -> dict[str, object]:
        return dict(
            sessions_cleared=True,
            not_before=self.not_before,
            retired_signing_providers=self.retired_signing_providers,
            client_secret_rotated=True,
            public_cutover=False,
            formal_accepted=False,
        )


def reconcile(admin: RecoveryAdmin, *, realm: str, expected_realm_id: str, client_id: str) -> Reconciliation:
    if re.fullmatch(r"media-trace-acceptance-[a-f0-9]{32}", realm) is None or client_id != "media-trace-api":
        raise RuntimeError("IDENTITY_RECONCILIATION_ISOLATED_REALM_REQUIRED")
    path = "/admin/realms/" + realm
    actual = admin.request("GET", path).json()
    if actual.get("id") != expected_realm_id or actual.get("realm") != realm:
        raise RuntimeError("IDENTITY_RECONCILIATION_REALM_IDENTITY_MISMATCH")
    # Quarantine verified restored state before any further discovery can fail.
    admin.request("PUT", path, body={"enabled": False}, expected=(204,))
    clients = admin.request("GET", path + "/clients").json()
    matches = [c for c in clients if c.get("clientId") == client_id]
    if len(matches) != 1 or re.fullmatch(r"[a-f0-9-]{36}", matches[0].get("id", "")) is None:
        raise RuntimeError("IDENTITY_RECONCILIATION_CLIENT_IDENTITY_MISMATCH")
    client_path = path + "/clients/" + matches[0]["id"]
    # A failed operation leaves this disposable realm disabled, never partly re-enabled.
    logout = admin.request("POST", path + "/logout-all", expected=(200,)).json()
    if not isinstance(logout, dict) or logout.get("failedRequests"):
        raise RuntimeError("IDENTITY_RECONCILIATION_LOGOUT_NOT_CONFIRMED")
    cutoff = int(time.time())
    admin.request("PUT", path, body={"notBefore": cutoff}, expected=(204,))
    old_keys = admin.request("GET", path + "/keys").json()["keys"]
    providers = {k["providerId"] for k in old_keys if str(k.get("use", "")).upper() == "SIG"}
    if not providers or any(re.fullmatch(r"[a-f0-9-]{36}", p) is None for p in providers):
        raise RuntimeError("IDENTITY_RECONCILIATION_SIGNING_METADATA_INVALID")
    admin.request(
        "POST",
        path + "/components",
        expected=(201,),
        body={
            "name": "restored-realm-new-signing-key",
            "parentId": expected_realm_id,
            "providerType": "org.keycloak.keys.KeyProvider",
            "providerId": "rsa-generated",
            "config": {"priority": ["100000"], "enabled": ["true"], "active": ["true"], "keySize": ["2048"]},
        },
    )
    for provider in sorted(providers):
        admin.request("DELETE", path + "/components/" + provider, expected=(204,))
    value = admin.request("POST", client_path + "/client-secret").json().get("value")
    if not isinstance(value, str) or len(value) < 16:
        raise RuntimeError("IDENTITY_RECONCILIATION_NEW_SECRET_INVALID")
    final = admin.request("GET", path).json()
    final_keys = admin.request("GET", path + "/keys").json()["keys"]
    remaining = {k["providerId"] for k in final_keys if str(k.get("use", "")).upper() == "SIG"}
    if final.get("notBefore") != cutoff or not remaining or remaining.intersection(providers):
        raise RuntimeError("IDENTITY_RECONCILIATION_STATE_NOT_CONFIRMED")
    admin.request("PUT", path, body={"enabled": True}, expected=(204,))
    return Reconciliation(value, cutoff, len(providers))
