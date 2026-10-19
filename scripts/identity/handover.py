"""Explicit administrator preparation and read-only configuration observation.

Preparation requires a writer and explicit operator action. The separate inspection
uses only GET; neither operation certifies personal handover or formal acceptance.
"""

import argparse
import getpass
import json
import re
import sys
from typing import Any, Protocol, TypedDict
from uuid import UUID

import httpx


class HandoverReader(Protocol):
    def request(self, method: str, path: str, *, expected: tuple[int, ...] = (200,)) -> httpx.Response: ...


class HandoverAdministrator(Protocol):
    def request(
        self, method: str, path: str, *, body: Any = None, expected: tuple[int, ...] = (200,)
    ) -> httpx.Response: ...


class HandoverObservation(TypedDict):
    scope: str
    configuration_ready: bool
    checks: dict[str, bool]
    fresh_mfa_login_verified: bool
    old_bootstrap_credentials_rejected: bool
    actual_personal_handover_completed: bool
    formal_accepted: bool


def _minimum_password_length(realm: dict[str, Any]) -> int | None:
    policy = realm.get("passwordPolicy")
    if not isinstance(policy, str):
        return None
    lengths = []
    for item in policy.split(" and "):
        if "length(" in item:
            matched = re.fullmatch(r"length\(([1-9][0-9]{0,3})\)", item)
            if matched is None:
                return None
            lengths.append(int(matched[1]))
    # Ambiguous/duplicate length rules require manual policy review.
    return lengths[0] if len(lengths) == 1 and lengths[0] >= 14 else None


def _master_protected(realm: dict[str, Any]) -> bool:
    return (
        _minimum_password_length(realm) is not None
        and realm.get("bruteForceProtected") is True
        and realm.get("adminEventsEnabled") is True
        and realm.get("adminEventsDetailsEnabled") is False
        and all(
            type(realm.get(k)) is int and realm[k] > 0
            for k in ("failureFactor", "waitIncrementSeconds", "maxFailureWaitSeconds")
        )
    )


def establish_master_protection(admin: HandoverAdministrator, *, master_realm_id: str) -> None:
    """Separate explicit operator action; never replace an existing weak/unknown policy."""
    base = "/admin/realms/master"
    try:
        current = admin.request("GET", base).json()
        if current.get("realm") != "master" or current.get("id") != master_realm_id:
            raise ValueError()
    except (RuntimeError, httpx.HTTPError, ValueError, TypeError, AttributeError):
        raise RuntimeError("IDENTITY_HANDOVER_PREFLIGHT_FAILED") from None
    policy = current.get("passwordPolicy")
    if policy not in (None, "") and _minimum_password_length(current) is None:
        raise RuntimeError("IDENTITY_HANDOVER_MASTER_POLICY_REVIEW_REQUIRED")
    candidate = {
        **current,
        "passwordPolicy": policy or "length(14)",
        "bruteForceProtected": True,
        "adminEventsEnabled": True,
        "adminEventsDetailsEnabled": False,
    }
    if not _master_protected(candidate):
        raise RuntimeError("IDENTITY_HANDOVER_MASTER_PROTECTION_REQUIRED")
    if _master_protected(current):
        return
    try:
        admin.request(
            "PUT",
            base,
            body={
                "passwordPolicy": candidate["passwordPolicy"],
                "bruteForceProtected": True,
                "adminEventsEnabled": True,
                "adminEventsDetailsEnabled": False,
            },
            expected=(204,),
        )
        observed = admin.request("GET", base).json()
        if (
            observed.get("id") != master_realm_id
            or observed.get("realm") != "master"
            or not _master_protected(observed)
        ):
            raise ValueError()
    except (RuntimeError, httpx.HTTPError, ValueError, TypeError, AttributeError):
        raise RuntimeError("IDENTITY_HANDOVER_MASTER_POLICY_STATE_UNCONFIRMED") from None


def prepare_administrator(
    admin: HandoverAdministrator, *, master_realm_id: str, username: str, temporary_password: str
) -> UUID:
    """Explicit operator action; prepare a new account without overwriting any user.

    Password and OTP enrolment remain mandatory before the first authorization code.
    A partial grant is disabled on failure; uncertain state requires manual review.
    """
    if (
        not re.fullmatch(r"[a-z][a-z0-9._-]{2,63}", username)
        or username.startswith(("service-account-", "bootstrap-"))
        or not 14 <= len(temporary_password) <= 128
    ):
        raise RuntimeError("IDENTITY_HANDOVER_INPUT_INVALID")
    base = "/admin/realms/master"
    try:
        realm = admin.request("GET", base).json()
        if realm.get("realm") != "master" or realm.get("id") != master_realm_id:
            raise ValueError()
        role = admin.request("GET", base + "/roles/admin").json()
        clients = admin.request("GET", base + "/clients").json()
        if not isinstance(clients, list) or not role.get("id") or role.get("name") != "admin":
            raise ValueError()
    except (RuntimeError, httpx.HTTPError, ValueError, TypeError, AttributeError):
        raise RuntimeError("IDENTITY_HANDOVER_PREFLIGHT_FAILED") from None
    if not _master_protected(realm):
        raise RuntimeError("IDENTITY_HANDOVER_MASTER_PROTECTION_REQUIRED")
    if not any(c.get("clientId") == "admin-cli" and c.get("directAccessGrantsEnabled") is False for c in clients):
        raise RuntimeError("IDENTITY_HANDOVER_PASSWORD_GRANT_ENABLED")
    try:
        response = admin.request(
            "POST",
            base + "/users",
            expected=(201, 409),
            body={
                "username": username,
                "enabled": False,
                "requiredActions": ["UPDATE_PASSWORD", "CONFIGURE_TOTP"],
                "credentials": [{"type": "password", "value": temporary_password, "temporary": True}],
            },
        )
    except (RuntimeError, httpx.HTTPError):
        raise RuntimeError("IDENTITY_HANDOVER_CREATION_UNCONFIRMED_MANUAL_REVIEW_REQUIRED") from None
    # Provider-enforced atomic uniqueness avoids a query/creation race, and retains
    # the existing AdminClient rule prohibiting arbitrary query strings in paths.
    if response.status_code == 409:
        raise RuntimeError("IDENTITY_HANDOVER_ACCOUNT_ALREADY_EXISTS")
    if response.status_code != 201:
        raise RuntimeError("IDENTITY_HANDOVER_CREATION_UNCONFIRMED_MANUAL_REVIEW_REQUIRED")
    subject = None
    try:
        candidate = UUID(response.headers["location"].rstrip("/").rsplit("/", 1)[1])
        path = base + "/users/" + str(candidate)
        created = admin.request("GET", path).json()
        if (
            created.get("id") != str(candidate)
            or created.get("username") != username
            or created.get("enabled") is not False
            or not {"UPDATE_PASSWORD", "CONFIGURE_TOTP"} <= set(created.get("requiredActions", []))
        ):
            raise ValueError()
        # Never grant, enable or disable a Location target until it is confirmed
        # to be the new disabled user; an uncertain response requires human review.
        subject = candidate
        admin.request("POST", path + "/role-mappings/realm", body=[role], expected=(204,))
        admin.request("PUT", path, body={"enabled": True}, expected=(204,))
        current = admin.request("GET", path).json()
        if (
            current.get("id") != str(subject)
            or current.get("username") != username
            or current.get("enabled") is not True
            or not {"UPDATE_PASSWORD", "CONFIGURE_TOTP"} <= set(current.get("requiredActions", []))
        ):
            raise ValueError()
        return subject
    except (RuntimeError, httpx.HTTPError, ValueError, TypeError, KeyError, AttributeError):
        if subject is not None:
            try:
                path = base + "/users/" + str(subject)
                admin.request("PUT", path, body={"enabled": False}, expected=(204,))
                if admin.request("GET", path).json().get("enabled") is not False:
                    raise ValueError()
            except (RuntimeError, httpx.HTTPError, ValueError, TypeError, AttributeError):
                raise RuntimeError("IDENTITY_HANDOVER_STATE_UNCERTAIN_MANUAL_REVIEW_REQUIRED") from None
            raise RuntimeError("IDENTITY_HANDOVER_PREPARATION_FAILED_DISABLED") from None
        raise RuntimeError("IDENTITY_HANDOVER_CREATION_UNCONFIRMED_MANUAL_REVIEW_REQUIRED") from None


def inspect_handover(admin: HandoverReader, *, administrator_id: UUID, master_realm_id: str) -> HandoverObservation:
    base = "/admin/realms/master"
    try:
        realm = admin.request("GET", base).json()
        if realm.get("id") != master_realm_id or realm.get("realm") != "master":
            raise ValueError("target")
        path = base + "/users/" + str(administrator_id)
        user = admin.request("GET", path).json()
        if user.get("id") != str(administrator_id):
            raise ValueError("target")
        credentials = admin.request("GET", path + "/credentials").json()
        roles = admin.request("GET", path + "/role-mappings/realm/composite").json()
        clients = admin.request("GET", base + "/clients").json()
        checks = {
            "master_password_and_brute_force_protection": _master_protected(realm),
            "administrator_enabled": user.get("enabled") is True,
            "otp_credential_present": any(c.get("type") == "otp" for c in credentials),
            "required_actions_completed": user.get("requiredActions") == [],
            "master_administration_role_present": any(r.get("name") == "admin" for r in roles),
            # A disabled bootstrap client still leaves recoverable credentials behind.
            "bootstrap_client_removed": not any(c.get("clientId") == "bootstrap-project-service" for c in clients),
            "admin_password_grant_disabled": any(
                c.get("clientId") == "admin-cli" and c.get("directAccessGrantsEnabled") is False for c in clients
            ),
        }
    except ValueError as error:
        if str(error) == "target":
            raise RuntimeError("IDENTITY_HANDOVER_TARGET_MISMATCH") from None
        raise RuntimeError("IDENTITY_HANDOVER_OBSERVATION_FAILED") from None
    except (RuntimeError, httpx.HTTPError, KeyError, TypeError, AttributeError):
        raise RuntimeError("IDENTITY_HANDOVER_OBSERVATION_FAILED") from None
    return {
        "scope": "read_only_configuration_observation_not_personal_handover",
        "configuration_ready": all(checks.values()),
        "checks": checks,
        "fresh_mfa_login_verified": False,
        "old_bootstrap_credentials_rejected": False,
        "actual_personal_handover_completed": False,
        "formal_accepted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare a named administrator; personal handover stays pending.")
    parser.add_argument("action", choices=["prepare", "master-protection"])
    parser.add_argument("--username")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.action == "prepare" and args.username is None:
        parser.error("prepare requires --username")
    if not args.apply:
        print(
            json.dumps(
                {
                    "applied": False,
                    "operation": "prepare_new_master_administrator"
                    if args.action == "prepare"
                    else "establish_master_password_protection",
                    "bootstrap_removed": False,
                }
            )
        )
        return 0
    if not sys.stdin.isatty() or not sys.stderr.isatty():
        print('{"status":"FAIL","error":"IDENTITY_HANDOVER_INTERACTIVE_TERMINAL_REQUIRED","formal_accepted":false}')
        return 1
    try:
        password = ""
        if args.action == "prepare":
            password = getpass.getpass("Temporary password (14-128 characters; never send to chat): ")
            if password != getpass.getpass("Confirm temporary password: "):
                raise RuntimeError("IDENTITY_HANDOVER_INPUT_INVALID")
        from .provision import AdminClient

        admin = AdminClient()
        try:
            realm = admin.request("GET", "/admin/realms/master").json()
            if args.action == "master-protection":
                establish_master_protection(admin, master_realm_id=realm["id"])
            else:
                prepare_administrator(
                    admin, master_realm_id=realm["id"], username=args.username, temporary_password=password
                )
        finally:
            admin.close()
        print(
            json.dumps(
                {
                    "account_prepared": args.action == "prepare",
                    "master_protection_checked": True,
                    "personal_password_and_MFA_pending": True,
                    "bootstrap_removed": False,
                    "formal_accepted": False,
                }
            )
        )
        return 0
    except (RuntimeError, OSError, httpx.HTTPError, ValueError, KeyError, EOFError) as error:
        safe_codes = {
            "IDENTITY_HANDOVER_INPUT_INVALID",
            "IDENTITY_HANDOVER_MASTER_PROTECTION_REQUIRED",
            "IDENTITY_HANDOVER_MASTER_POLICY_REVIEW_REQUIRED",
            "IDENTITY_HANDOVER_MASTER_POLICY_STATE_UNCONFIRMED",
            "IDENTITY_HANDOVER_PREFLIGHT_FAILED",
            "IDENTITY_HANDOVER_ACCOUNT_ALREADY_EXISTS",
            "IDENTITY_HANDOVER_PASSWORD_GRANT_ENABLED",
            "IDENTITY_HANDOVER_CREATION_UNCONFIRMED_MANUAL_REVIEW_REQUIRED",
            "IDENTITY_HANDOVER_STATE_UNCERTAIN_MANUAL_REVIEW_REQUIRED",
            "IDENTITY_HANDOVER_PREPARATION_FAILED_DISABLED",
        }
        code = (
            str(error)
            if isinstance(error, RuntimeError) and str(error) in safe_codes
            else "IDENTITY_HANDOVER_PREPARATION_NOT_CONFIRMED"
        )
        print(json.dumps({"status": "FAIL", "error": code, "formal_accepted": False}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
