"""Synthetic handover rehearsal; never creates or signs for the named human."""

import secrets
import time
from uuid import UUID, uuid4

from scripts.identity.handover import establish_master_protection, inspect_handover, prepare_administrator
from tests.identity import recovery_lab as recovery_support
from tests.identity.handover_lab import HumanAdmin, HumanLogin, otp
from tools.identity_oidc_probe import PrivateValue

handover_lab = recovery_support.recovery_lab


def test_real_master_mfa_bootstrap_removal_and_restart(handover_lab):
    lab = handover_lab
    username = "synthetic-admin-" + uuid4().hex
    password = PrivateValue(secrets.token_hex(24))
    lab.private_values.append(password)
    base = "/admin/realms/master"
    master_id = lab.admin.request("GET", base).json()["id"]
    establish_master_protection(lab.admin, master_realm_id=master_id)
    master = lab.admin.request("GET", base).json()
    quick_ms = master.get("quickLoginCheckMilliSeconds")
    if type(quick_ms) is not int or not 0 <= quick_ms <= 5000:
        raise RuntimeError("IDENTITY_HANDOVER_TEST_QUICK_LOGIN_WINDOW_UNSUPPORTED")
    # These are separate negative scenarios, not a burst/lockout test. Respect
    # the server's existing window; do not disable protection or clear failures.
    negative_spacing = quick_ms / 1000 + 0.25
    clients = lab.admin.request("GET", base + "/clients").json()
    bootstrap_id = next(c["id"] for c in clients if c["clientId"] == "bootstrap-project-service")
    cli_id = next(c["id"] for c in clients if c["clientId"] == "admin-cli")
    lab.admin.request("PUT", base + "/clients/" + cli_id, body={"directAccessGrantsEnabled": False}, expected=(204,))
    subject = str(
        prepare_administrator(lab.admin, master_realm_id=master_id, username=username, temporary_password=password)
    )
    lab.admin.request(
        "PUT",
        base + "/users/" + subject,
        body=dict(
            firstName="Synthetic", lastName="Administrator", email=username + "@example.invalid", emailVerified=True
        ),
        expected=(204,),
    )
    personal_password = PrivateValue(secrets.token_hex(24))
    lab.private_values.append(personal_password)
    client_id = "synthetic-handover-" + uuid4().hex
    lab.admin.request(
        "POST",
        base + "/clients",
        body=dict(
            clientId=client_id,
            enabled=True,
            publicClient=True,
            protocol="openid-connect",
            standardFlowEnabled=True,
            directAccessGrantsEnabled=False,
            implicitFlowEnabled=False,
            serviceAccountsEnabled=False,
            redirectUris=[lab.redirect],
            attributes={"pkce.code.challenge.method": "S256"},
        ),
        expected=(201,),
    )
    with lab.http() as http:
        response = http.post(
            lab.public_url + "/realms/master/protocol/openid-connect/token",
            data=dict(
                grant_type="client_credentials",
                client_id="bootstrap-project-service",
                client_secret=lab.bootstrap_secret,
            ),
        )
    assert response.status_code == 200
    old_bootstrap = PrivateValue(response.json()["access_token"])
    lab.private_values.append(old_bootstrap)
    first = HumanLogin(lab, client_id, username, password)
    try:
        first.password_step()
        completed = set()
        for _ in range(2):
            assert first.callback_ready() is False, "BOTH_PERSONAL_ACTIONS_REQUIRED_BEFORE_CODE"
            if first.requires_otp() and 'name="totpSecret"' in first.page.text:
                assert "otp" not in completed
                secret = first.otp_secret()
                code, counter = otp(secret)
                first.post_form(dict(totp=code, totpSecret=secret, userLabel="self-owned-test-device"))
                completed.add("otp")
            else:
                assert first.page.status_code == 200 and 'name="password-new"' in first.page.text
                assert "password" not in completed
                short = PrivateValue("synthetic-123")
                lab.private_values.append(short)
                first.post_form({"password-new": short, "password-confirm": short, "logout-sessions": "on"})
                assert not first.callback_ready(), "SUB_14_CHARACTER_PERSONAL_PASSWORD_MUST_FAIL"
                assert first.page.status_code == 200 and 'name="password-new"' in first.page.text
                first.post_form(
                    {"password-new": personal_password, "password-confirm": personal_password, "logout-sessions": "on"}
                )
                completed.add("password")
        assert completed == {"otp", "password"}
        token = first.exchange()
    finally:
        first.close()
    human = HumanAdmin(lab, token)
    events = human.request("GET", base + "/admin-events").json()
    assert any(e.get("operationType") == "CREATE" and e.get("resourcePath") == "users/" + subject for e in events)
    assert all(not e.get("representation") for e in events), "ADMIN_AUDIT_MUST_EXCLUDE_REQUEST_PAYLOADS"
    before = inspect_handover(human, administrator_id=UUID(subject), master_realm_id=master_id)
    assert before["configuration_ready"] is False
    assert before["checks"]["bootstrap_client_removed"] is False
    human.request("DELETE", base + "/clients/" + bootstrap_id, expected=(204,))
    with lab.http() as http:
        rejected_secret = http.post(
            lab.public_url + "/realms/master/protocol/openid-connect/token",
            data=dict(
                grant_type="client_credentials",
                client_id="bootstrap-project-service",
                client_secret=lab.bootstrap_secret,
            ),
        )
        rejected_token = http.get(lab.admin_url + "/admin/realms", headers={"Authorization": "Bearer " + old_bootstrap})
    assert rejected_secret.status_code in (400, 401)
    assert rejected_token.status_code in (401, 403)
    old_password = HumanLogin(lab, client_id, username, password)
    try:
        old_password.password_step()
        assert not old_password.callback_ready()
        assert not old_password.requires_otp()
    finally:
        old_password.close()
    time.sleep(negative_spacing)
    bad = HumanLogin(lab, client_id, username, personal_password)
    try:
        bad.password_step()
        assert bad.requires_otp()
        bad.post_form(dict(otp="not-an-otp"))
        assert bad.requires_otp()
    finally:
        bad.close()
    time.sleep(negative_spacing)
    good = HumanLogin(lab, client_id, username, personal_password)
    try:
        good.password_step()
        assert good.requires_otp()
        code, counter = otp(secret, after_counter=counter)
        good.post_form(dict(otp=code))
        fresh = good.exchange()
    finally:
        good.close()
    replay = HumanLogin(lab, client_id, username, personal_password)
    try:
        replay.password_step()
        replay.post_form(dict(otp=code))
        assert replay.requires_otp(), "REUSED_OTP_MUST_NOT_AUTHENTICATE"
    finally:
        replay.close()
    assert (
        inspect_handover(HumanAdmin(lab, fresh), administrator_id=UUID(subject), master_realm_id=master_id)[
            "configuration_ready"
        ]
        is True
    )
    lab.restart()
    last = HumanLogin(lab, client_id, username, personal_password)
    try:
        last.password_step()
        assert last.requires_otp()
        code, counter = otp(secret, after_counter=counter)
        last.post_form(dict(otp=code))
        restarted = last.exchange()
    finally:
        last.close()
    final = inspect_handover(HumanAdmin(lab, restarted), administrator_id=UUID(subject), master_realm_id=master_id)
    assert final["configuration_ready"] is True
    assert final["actual_personal_handover_completed"] is False
    lab.record(
        "synthetic_admin_mfa_handover_rehearsal",
        real_http_tls=True,
        master_password_policy_and_brute_force_checked=True,
        short_personal_password_rejected=True,
        administrator_creation_audited_without_request_payload=True,
        negative_scenarios_spaced_from_configured_quick_login_window=True,
        quick_login_window_ms=quick_ms,
        otp_wrong_and_reuse_denied=True,
        bootstrap_client_removed=True,
        old_bootstrap_token_and_secret_rejected=True,
        restart_preserves_handover=True,
        actual_personal_handover_completed=False,
    )
