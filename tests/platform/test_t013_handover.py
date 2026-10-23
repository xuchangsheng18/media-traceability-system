"""A credential row or a person's name must never certify an actual handover."""

import copy
import json
import subprocess
import sys
from pathlib import Path
from typing import Any
from uuid import UUID

import httpx
import pytest

SUBJECT = "5dc976ba-734d-4626-b536-1b67845a16e8"


class Observation:
    def __init__(self):
        self.values: dict[str, Any] = {
            "/admin/realms/master": {
                "id": "self-owned-master",
                "realm": "master",
                "passwordPolicy": "length(14)",
                "bruteForceProtected": True,
                "failureFactor": 5,
                "waitIncrementSeconds": 60,
                "maxFailureWaitSeconds": 900,
                "adminEventsEnabled": True,
                "adminEventsDetailsEnabled": False,
            },
            f"/admin/realms/master/users/{SUBJECT}": {"id": SUBJECT, "enabled": True, "requiredActions": []},
            f"/admin/realms/master/users/{SUBJECT}/credentials": [{"type": "otp", "id": "self-owned-credential"}],
            f"/admin/realms/master/users/{SUBJECT}/role-mappings/realm/composite": [{"name": "admin"}],
            "/admin/realms/master/clients": [{"clientId": "admin-cli", "directAccessGrantsEnabled": False}],
        }
        self.methods = []

    def request(self, method, path, *, expected=(200,)):
        self.methods.append(method)
        return httpx.Response(200, json=copy.deepcopy(self.values[path]))


def inspect(observation):
    from scripts.identity.handover import inspect_handover

    return inspect_handover(observation, administrator_id=UUID(SUBJECT), master_realm_id="self-owned-master")


def test_configuration_evidence_never_certifies_personal_handover():
    observation = Observation()
    report = inspect(observation)
    assert report["configuration_ready"] is True
    assert report["fresh_mfa_login_verified"] is False
    assert report["old_bootstrap_credentials_rejected"] is False
    assert report["actual_personal_handover_completed"] is False
    assert report["formal_accepted"] is False
    assert set(observation.methods) == {"GET"}
    assert SUBJECT not in json.dumps(report)


@pytest.mark.parametrize("missing", ["otp", "role", "enabled", "required_action", "bootstrap", "password_grant"])
def test_incomplete_configuration_never_reports_ready(missing):
    observation = Observation()
    user = observation.values[f"/admin/realms/master/users/{SUBJECT}"]
    if missing == "otp":
        observation.values[f"/admin/realms/master/users/{SUBJECT}/credentials"] = []
    elif missing == "role":
        observation.values[f"/admin/realms/master/users/{SUBJECT}/role-mappings/realm/composite"] = []
    elif missing == "enabled":
        user["enabled"] = False
    elif missing == "required_action":
        user["requiredActions"] = ["CONFIGURE_TOTP"]
    elif missing == "bootstrap":
        observation.values["/admin/realms/master/clients"].append(
            {"clientId": "bootstrap-project-service", "enabled": False}
        )
    else:
        observation.values["/admin/realms/master/clients"][0]["directAccessGrantsEnabled"] = True
    assert inspect(observation)["configuration_ready"] is False


def test_wrong_realm_cannot_be_used_as_master_evidence():
    observation = Observation()
    observation.values["/admin/realms/master"]["id"] = "another-master"
    with pytest.raises(RuntimeError, match="IDENTITY_HANDOVER_TARGET_MISMATCH"):
        inspect(observation)


def test_observation_failure_has_no_secret_details():
    class Unavailable:
        def request(self, *args, **kwargs):
            raise RuntimeError("private-provider-detail-must-not-escape")

    with pytest.raises(RuntimeError) as caught:
        inspect(Unavailable())
    assert str(caught.value) == "IDENTITY_HANDOVER_OBSERVATION_FAILED"


class Preparation(Observation):
    def __init__(self, fail_grant=False):
        super().__init__()
        self.fail_grant = fail_grant
        self.existing = False
        self.created: dict[str, Any] | None = None
        self.operations = []
        self.values["/admin/realms/master/roles/admin"] = {"id": "self-owned-role", "name": "admin"}

    def request(self, method, path, *, body=None, expected=(200,)):
        self.operations.append((method, path))
        if method == "POST" and path == "/admin/realms/master/users":
            if self.existing:
                return httpx.Response(409)
            self.created = copy.deepcopy(body)
            self.values[f"/admin/realms/master/users/{SUBJECT}"] = {**self.created, "id": SUBJECT}
            return httpx.Response(201, headers={"location": "https://localhost/admin/realms/master/users/" + SUBJECT})
        if method == "POST" and path.endswith("/role-mappings/realm"):
            if self.fail_grant:
                raise RuntimeError("private-grant-failure-detail")
            return httpx.Response(204)
        if method == "PUT":
            self.values[path].update(body)
            return httpx.Response(204)
        return super().request(method, path, expected=expected)


def prepare(admin):
    from scripts.identity.handover import prepare_administrator

    return prepare_administrator(
        admin,
        master_realm_id="self-owned-master",
        username="synthetic-admin",
        temporary_password="self-owned-test-password-only",
    )


def test_new_administrator_requires_personal_password_and_mfa_before_first_login():
    admin = Preparation()
    result = prepare(admin)
    assert result == UUID(SUBJECT)
    assert admin.created is not None
    assert admin.created["enabled"] is False
    assert set(admin.created["requiredActions"]) == {"UPDATE_PASSWORD", "CONFIGURE_TOTP"}
    assert admin.created["credentials"][0]["temporary"] is True
    assert admin.values[f"/admin/realms/master/users/{SUBJECT}"]["enabled"] is True


def test_failed_role_preparation_keeps_partial_account_disabled():
    admin = Preparation(fail_grant=True)
    with pytest.raises(RuntimeError, match="IDENTITY_HANDOVER_PREPARATION_FAILED_DISABLED"):
        prepare(admin)
    assert admin.values[f"/admin/realms/master/users/{SUBJECT}"]["enabled"] is False


def test_existing_account_is_never_repurposed_or_overwritten():
    admin = Preparation()
    admin.existing = True
    with pytest.raises(RuntimeError, match="IDENTITY_HANDOVER_ACCOUNT_ALREADY_EXISTS"):
        prepare(admin)
    assert admin.created is None
    assert all(
        method == "GET" or (method == "POST" and path == "/admin/realms/master/users")
        for method, path in admin.operations
    )


def test_apply_refuses_redirected_input_before_requesting_password():
    result = subprocess.run(
        [sys.executable, "-m", "scripts.identity.handover", "prepare", "--username", "synthetic-admin", "--apply"],
        cwd=Path(__file__).resolve().parents[2],
        input="",
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 1
    assert "Temporary password" not in result.stderr
    assert json.loads(result.stdout)["error"] == "IDENTITY_HANDOVER_INTERACTIVE_TERMINAL_REQUIRED"


def test_preview_does_not_attempt_private_configuration_or_account_access():
    result = subprocess.run(
        [sys.executable, "-m", "scripts.identity.handover", "prepare", "--username", "synthetic-admin"],
        cwd=Path(__file__).resolve().parents[2],
        input="",
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["applied"] is False
    assert result.stderr == ""


def test_preparation_uses_existing_admin_path_safety_boundary():
    class Guarded(Preparation):
        def request(self, method, path, **kwargs):
            if "?" in path or ".." in path:
                raise RuntimeError("IDENTITY_ADMIN_PATH_FORBIDDEN")
            return super().request(method, path, **kwargs)

    assert prepare(Guarded()) == UUID(SUBJECT)


def test_unconfirmed_location_cannot_grant_or_disable_an_unrelated_account():
    foreign_id = "1e3883c8-0733-40f1-bb9d-147647b83f68"
    foreign_path = "/admin/realms/master/users/" + foreign_id

    class Misdirected(Preparation):
        def request(self, method, path, **kwargs):
            response = super().request(method, path, **kwargs)
            if method == "POST" and path == "/admin/realms/master/users":
                return httpx.Response(201, headers={"location": "https://localhost" + foreign_path})
            return response

    admin = Misdirected()
    admin.values[foreign_path] = {
        "id": foreign_id,
        "username": "unrelated-user",
        "enabled": True,
        "requiredActions": [],
    }
    with pytest.raises(RuntimeError):
        prepare(admin)
    assert admin.values[foreign_path]["enabled"] is True
    assert not any(
        method in {"POST", "PUT", "DELETE"} and path.startswith(foreign_path) for method, path in admin.operations
    )


@pytest.mark.parametrize(
    "values",
    [
        {"passwordPolicy": ""},
        {"passwordPolicy": "length(8)"},
        {"passwordPolicy": "length(14) and length(8)"},
        {"bruteForceProtected": False},
        {"failureFactor": 0},
        {"waitIncrementSeconds": 0},
        {"adminEventsEnabled": False},
        {"adminEventsDetailsEnabled": True},
    ],
)
def test_missing_master_protection_blocks_creation_and_readiness(values):
    admin = Preparation()
    admin.values["/admin/realms/master"].update(values)
    with pytest.raises(RuntimeError, match="IDENTITY_HANDOVER_MASTER_PROTECTION_REQUIRED"):
        prepare(admin)
    assert admin.created is None
    assert inspect(admin)["configuration_ready"] is False


def test_controlled_master_setup_preserves_existing_stronger_policy():
    from scripts.identity.handover import establish_master_protection

    admin = Preparation()
    admin.values["/admin/realms/master"].update(passwordPolicy="length(20) and notUsername", bruteForceProtected=False)
    establish_master_protection(admin, master_realm_id="self-owned-master")
    assert admin.values["/admin/realms/master"]["passwordPolicy"] == "length(20) and notUsername"
    assert admin.values["/admin/realms/master"]["bruteForceProtected"] is True
    assert admin.created is None


def test_controlled_master_setup_never_overwrites_an_existing_weak_or_ambiguous_policy():
    from scripts.identity.handover import establish_master_protection

    admin = Preparation()
    admin.values["/admin/realms/master"]["passwordPolicy"] = "length(8) and notUsername"
    with pytest.raises(RuntimeError, match="IDENTITY_HANDOVER_MASTER_POLICY_REVIEW_REQUIRED"):
        establish_master_protection(admin, master_realm_id="self-owned-master")
    assert all(method == "GET" for method, path in admin.operations)


def test_controlled_master_setup_establishes_missing_policy_and_protection_only():
    from scripts.identity.handover import establish_master_protection

    admin = Preparation()
    admin.values["/admin/realms/master"].update(passwordPolicy="", bruteForceProtected=False)
    establish_master_protection(admin, master_realm_id="self-owned-master")
    assert admin.values["/admin/realms/master"]["passwordPolicy"] == "length(14)"
    assert admin.values["/admin/realms/master"]["bruteForceProtected"] is True
    assert not any(method == "POST" for method, path in admin.operations)
