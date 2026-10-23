"""A client-specific required MFA flow; never change the master's browser default."""

from typing import Any
from uuid import UUID

import httpx

from .handover import HandoverAdministrator, _master_protected

CLIENT_ID = "media-trace-admin-tools"
FLOW_ALIAS = "media-trace-admin-tools-mfa"
REDIRECT_URI = "http://127.0.0.1:18765/identity-admin/callback"
BASE = "/admin/realms/master"


def client_definition(flow_id: str, *, enabled: bool) -> dict[str, Any]:
    return {
        "clientId": CLIENT_ID,
        "protocol": "openid-connect",
        "enabled": enabled,
        "publicClient": True,
        "standardFlowEnabled": True,
        "directAccessGrantsEnabled": False,
        "implicitFlowEnabled": False,
        "serviceAccountsEnabled": False,
        "consentRequired": False,
        "fullScopeAllowed": True,
        "redirectUris": [REDIRECT_URI],
        "webOrigins": [],
        "defaultClientScopes": ["basic", "roles"],
        "optionalClientScopes": [],
        "authenticationFlowBindingOverrides": {"browser": flow_id},
        "attributes": {
            "pkce.code.challenge.method": "S256",
            "access.token.lifespan": "300",
            "use.refresh.tokens": "false",
            "oauth2.device.authorization.grant.enabled": "false",
        },
        "protocolMappers": [
            {
                "name": "management-audience",
                "protocol": "openid-connect",
                "protocolMapper": "oidc-audience-mapper",
                "config": {
                    "included.client.audience": CLIENT_ID,
                    "access.token.claim": "true",
                    "id.token.claim": "false",
                    "userinfo.token.claim": "false",
                },
            },
            {
                "name": "management-mfa",
                "protocol": "openid-connect",
                "protocolMapper": "oidc-amr-mapper",
                "config": {"access.token.claim": "true", "id.token.claim": "true", "userinfo.token.claim": "false"},
            },
        ],
    }


def _uuid(value: Any) -> str:
    parsed = str(UUID(value))
    if value != parsed:
        raise ValueError("noncanonical id")
    return parsed


def verify_configuration(admin: HandoverAdministrator, *, enabled: bool = True) -> dict[str, str]:
    """Only reads; every existing object must match before it is reused."""
    try:
        realm = admin.request("GET", BASE).json()
        if realm.get("realm") != "master" or not _master_protected(realm):
            raise ValueError()
        flows = admin.request("GET", BASE + "/authentication/flows").json()
        matches = [f for f in flows if f.get("alias") == FLOW_ALIAS]
        if len(matches) != 1 or matches[0].get("providerId") != "basic-flow" or matches[0].get("builtIn") is not False:
            raise ValueError()
        flow_id = _uuid(matches[0]["id"])
        executions = admin.request("GET", BASE + "/authentication/flows/" + FLOW_ALIAS + "/executions").json()
        if len(executions) != 2:
            raise ValueError()
        for index, (provider, reference) in enumerate(
            (("auth-username-password-form", "pwd"), ("auth-otp-form", "otp"))
        ):
            execution = executions[index]
            if (
                execution.get("providerId") != provider
                or execution.get("requirement") != "REQUIRED"
                or execution.get("level") != 0
            ):
                raise ValueError()
            actual = admin.request("GET", BASE + "/authentication/executions/" + _uuid(execution["id"])).json()
            if actual.get("parentFlow") != flow_id or actual.get("authenticator") != provider:
                raise ValueError()
            config = admin.request(
                "GET", BASE + "/authentication/config/" + _uuid(actual["authenticatorConfig"])
            ).json()
            if config.get("config") != {"default.reference.value": reference, "default.reference.maxAge": "300"}:
                raise ValueError()
        clients = admin.request("GET", BASE + "/clients").json()
        exact = [c for c in clients if c.get("clientId") == CLIENT_ID]
        if len(exact) != 1:
            raise ValueError()
        client_id = _uuid(exact[0]["id"])
        full = admin.request("GET", BASE + "/clients/" + client_id).json()
        expected = client_definition(flow_id, enabled=enabled)
        for key, value in expected.items():
            if key == "attributes":
                if not all(full.get(key, {}).get(k) == v for k, v in value.items()):
                    raise ValueError()
            elif key == "protocolMappers":
                found = full.get(key, [])
                if len(found) != len(value):
                    raise ValueError()
                for mapper in value:
                    actual_mapper: dict[str, Any] = next((m for m in found if m.get("name") == mapper["name"]), {})
                    if any(actual_mapper.get(k) != v for k, v in mapper.items()):
                        raise ValueError()
            elif key in {"defaultClientScopes", "optionalClientScopes"}:
                if sorted(full.get(key, [])) != sorted(value):
                    raise ValueError()
            elif full.get(key) != value:
                raise ValueError()
        return {"client_uuid": client_id, "flow_uuid": flow_id}
    except (RuntimeError, ValueError, KeyError, TypeError, AttributeError):
        raise RuntimeError("IDENTITY_MANAGEMENT_CONFIGURATION_REVIEW_REQUIRED") from None


def setup(admin: HandoverAdministrator) -> dict[str, Any]:
    realm = admin.request("GET", BASE).json()
    if realm.get("realm") != "master" or not _master_protected(realm):
        raise RuntimeError("IDENTITY_MANAGEMENT_MASTER_PROTECTION_REQUIRED")
    clients = admin.request("GET", BASE + "/clients").json()
    if any(c.get("clientId") == CLIENT_ID for c in clients):
        verify_configuration(admin)
        return {"configured": True, "changed": False, "bootstrap_deleted": False, "formal_accepted": False}
    flows = admin.request("GET", BASE + "/authentication/flows").json()
    if any(f.get("alias") == FLOW_ALIAS for f in flows):
        raise RuntimeError("IDENTITY_MANAGEMENT_PARTIAL_FLOW_REVIEW_REQUIRED")
    confirmed_client = None
    try:
        admin.request(
            "POST",
            BASE + "/authentication/flows",
            body={
                "alias": FLOW_ALIAS,
                "description": "Project management only: password and OTP required",
                "providerId": "basic-flow",
                "topLevel": True,
                "builtIn": False,
            },
            expected=(201,),
        )
        matches = [
            f for f in admin.request("GET", BASE + "/authentication/flows").json() if f.get("alias") == FLOW_ALIAS
        ]
        if len(matches) != 1 or matches[0].get("providerId") != "basic-flow" or matches[0].get("builtIn") is not False:
            raise ValueError()
        flow_id = _uuid(matches[0]["id"])
        for priority, (provider, reference) in enumerate(
            (("auth-username-password-form", "pwd"), ("auth-otp-form", "otp")), 1
        ):
            response = admin.request(
                "POST",
                BASE + "/authentication/executions",
                body={
                    "parentFlow": flow_id,
                    "authenticator": provider,
                    "authenticatorFlow": False,
                    "requirement": "REQUIRED",
                    "priority": priority * 10,
                },
                expected=(201,),
            )
            execution_id = _uuid(response.headers["location"].rstrip("/").rsplit("/", 1)[1])
            execution = admin.request("GET", BASE + "/authentication/executions/" + execution_id).json()
            if execution.get("parentFlow") != flow_id or execution.get("authenticator") != provider:
                raise ValueError()
            admin.request(
                "POST",
                BASE + "/authentication/executions/" + execution_id + "/config",
                body={
                    "alias": FLOW_ALIAS + "-" + reference,
                    "config": {"default.reference.value": reference, "default.reference.maxAge": "300"},
                },
                expected=(201,),
            )
        created = admin.request(
            "POST", BASE + "/clients", body=client_definition(flow_id, enabled=False), expected=(201,)
        )
        created_id = _uuid(created.headers["location"].rstrip("/").rsplit("/", 1)[1])
        created_client = admin.request("GET", BASE + "/clients/" + created_id).json()
        if created_client.get("clientId") != CLIENT_ID or created_client.get("enabled") is not False:
            raise ValueError()
        confirmed_client = created_id
        # Creation can infer web origins from redirects. Clear only our new disabled client.
        admin.request("PUT", BASE + "/clients/" + confirmed_client, body={"webOrigins": []}, expected=(204,))
        verify_configuration(admin, enabled=False)
        admin.request(
            "PUT", BASE + "/clients/" + confirmed_client, body={"enabled": True, "webOrigins": []}, expected=(204,)
        )
        verify_configuration(admin)
    except (RuntimeError, ValueError, KeyError, TypeError, AttributeError, httpx.HTTPError):
        if confirmed_client is not None:
            try:
                admin.request("PUT", BASE + "/clients/" + confirmed_client, body={"enabled": False}, expected=(204,))
                if admin.request("GET", BASE + "/clients/" + confirmed_client).json().get("enabled") is not False:
                    raise ValueError()
            except (RuntimeError, ValueError, KeyError, TypeError, AttributeError, httpx.HTTPError):
                raise RuntimeError("IDENTITY_MANAGEMENT_SETUP_STATE_UNCERTAIN") from None
        raise RuntimeError("IDENTITY_MANAGEMENT_SETUP_INCOMPLETE_REVIEW_REQUIRED") from None
    return {"configured": True, "changed": True, "bootstrap_deleted": False, "formal_accepted": False}
