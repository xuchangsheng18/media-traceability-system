"""Disposable genuine MFA management continues after the bootstrap is removed."""

import base64
import json
import re
import secrets
import threading
import time
from typing import Any
from urllib.parse import urlsplit
from uuid import uuid4

import httpx
import pytest

from scripts.identity import common, management, management_config, provision, retirement
from scripts.identity.handover import establish_master_protection, prepare_administrator
from tests.identity import recovery_lab as fixtures
from tests.identity.handover_lab import HumanLogin, otp
from tools.identity_oidc_probe import PrivateValue

management_lab = fixtures.recovery_lab


def enroll(lab):
    base = "/admin/realms/master"
    master_id = lab.admin.request("GET", base).json()["id"]
    establish_master_protection(lab.admin, master_realm_id=master_id)
    clients = lab.admin.request("GET", base + "/clients").json()
    cli = next(c["id"] for c in clients if c["clientId"] == "admin-cli")
    lab.admin.request("PUT", base + "/clients/" + cli, body={"directAccessGrantsEnabled": False}, expected=(204,))
    username = "synthetic-admin-" + uuid4().hex
    temporary, password = PrivateValue(secrets.token_hex(24)), PrivateValue(secrets.token_hex(24))
    lab.private_values.extend([temporary, password])
    subject = str(
        prepare_administrator(lab.admin, master_realm_id=master_id, username=username, temporary_password=temporary)
    )
    lab.admin.request(
        "PUT",
        base + "/users/" + subject,
        body={
            "firstName": "Synthetic",
            "lastName": "Management",
            "email": username + "@example.invalid",
            "emailVerified": True,
        },
        expected=(204,),
    )
    client_id = "synthetic-enrollment-" + uuid4().hex
    lab.admin.request(
        "POST",
        base + "/clients",
        body={
            "clientId": client_id,
            "enabled": True,
            "publicClient": True,
            "protocol": "openid-connect",
            "standardFlowEnabled": True,
            "directAccessGrantsEnabled": False,
            "implicitFlowEnabled": False,
            "serviceAccountsEnabled": False,
            "redirectUris": [lab.redirect],
            "attributes": {"pkce.code.challenge.method": "S256"},
        },
        expected=(201,),
    )
    first = HumanLogin(lab, client_id, username, temporary)
    secret = None
    counter = None
    done = set()
    try:
        first.password_step()
        for _ in range(2):
            assert not first.callback_ready()
            if first.requires_otp() and 'name="totpSecret"' in first.page.text:
                secret = first.otp_secret()
                code, counter = otp(secret)
                first.post_form(dict(totp=code, totpSecret=secret, userLabel="self-owned-management-device"))
                done.add("otp")
            else:
                first.post_form({"password-new": password, "password-confirm": password, "logout-sessions": "on"})
                done.add("password")
        assert done == {"otp", "password"} and first.callback_ready()
        assert secret is not None and counter is not None
    finally:
        first.close()
    return username, password, subject, secret, counter


def test_personal_mfa_tools_and_private_retirement_candidates_without_bootstrap(management_lab, monkeypatch):
    lab = management_lab
    username, password, subject, secret, counter = enroll(lab)
    base = "/admin/realms/master"
    try:
        management_config.setup(lab.admin)
    except RuntimeError as error:
        diagnostic: dict[str, Any] = {"exception_frames": []}
        current_error: BaseException | None = error
        while current_error is not None:
            tb = current_error.__traceback__
            frames = []
            while tb is not None:
                frames.append(
                    {"function": tb.tb_frame.f_code.co_name, "line": tb.tb_lineno, "type": type(current_error).__name__}
                )
                tb = tb.tb_next
            diagnostic["exception_frames"].extend(frames)
            current_error = current_error.__context__
        try:
            flows = lab.admin.request("GET", base + "/authentication/flows").json()
            diagnostic["flows"] = [f for f in flows if f.get("alias") == management_config.FLOW_ALIAS]
            executions = lab.admin.request(
                "GET", base + "/authentication/flows/" + management_config.FLOW_ALIAS + "/executions"
            ).json()
            diagnostic["executions"] = executions
            diagnostic["execution_models"] = [
                lab.admin.request("GET", base + "/authentication/executions/" + e["id"]).json() for e in executions
            ]
            diagnostic["execution_configurations"] = [
                lab.admin.request("GET", base + "/authentication/config/" + e["authenticatorConfig"]).json()
                for e in diagnostic["execution_models"]
                if e.get("authenticatorConfig")
            ]
            clients = lab.admin.request("GET", base + "/clients").json()
            full = [
                lab.admin.request("GET", base + "/clients/" + c["id"]).json()
                for c in clients
                if c.get("clientId") == management_config.CLIENT_ID
            ]
            public_keys = {
                "id",
                "clientId",
                "enabled",
                "publicClient",
                "standardFlowEnabled",
                "directAccessGrantsEnabled",
                "implicitFlowEnabled",
                "serviceAccountsEnabled",
                "fullScopeAllowed",
                "redirectUris",
                "webOrigins",
                "defaultClientScopes",
                "optionalClientScopes",
                "authenticationFlowBindingOverrides",
                "consentRequired",
            }
            diagnostic["clients"] = [{k: v for k, v in c.items() if k in public_keys} for c in full]
            diagnostic["client_attributes"] = [
                {
                    k: v
                    for k, v in c.get("attributes", {}).items()
                    if k
                    in {
                        "pkce.code.challenge.method",
                        "access.token.lifespan",
                        "use.refresh.tokens",
                        "oauth2.device.authorization.grant.enabled",
                    }
                }
                for c in full
            ]
            diagnostic["client_mappers"] = [
                {
                    "name": m.get("name"),
                    "protocolMapper": m.get("protocolMapper"),
                    "config": {
                        k: v
                        for k, v in m.get("config", {}).items()
                        if k in {"included.client.audience", "access.token.claim", "id.token.claim"}
                    },
                }
                for c in full
                for m in c.get("protocolMappers", [])
            ]
        except RuntimeError:
            diagnostic["inspection_unavailable"] = True
        (lab.root / "management-setup-diagnostic.private.json").write_text(json.dumps(diagnostic, indent=2) + "\n")
        raise
    assert management_config.setup(lab.admin)["changed"] is False
    bootstrap_id = next(
        c["id"]
        for c in lab.admin.request("GET", base + "/clients").json()
        if c["clientId"] == "bootstrap-project-service"
    )
    with lab.http() as http:
        old_response = http.post(
            lab.public_url + "/realms/master/protocol/openid-connect/token",
            data={
                "grant_type": "client_credentials",
                "client_id": "bootstrap-project-service",
                "client_secret": lab.bootstrap_secret,
            },
        )
    assert old_response.status_code == 200
    old_token = PrivateValue(old_response.json()["access_token"])
    lab.private_values.append(old_token)
    monkeypatch.setattr(common, "RUNTIME", lab.runtime)
    monkeypatch.setattr(common, "PUBLIC_URL", lab.public_url)
    monkeypatch.setattr(common, "ADMIN_URL", lab.admin_url)
    monkeypatch.delenv("MT_IDENTITY_ADMIN_SESSION", raising=False)
    lab.redirect = management_config.REDIRECT_URI
    counters = [counter]
    original_verify_access = management.verify_access

    def diagnosed_verify_access(token, jwks, **kwargs):
        try:
            return original_verify_access(token, jwks, **kwargs)
        except RuntimeError:
            claims = json.loads(base64.urlsafe_b64decode(token.split(".")[1] + "=="))
            diagnostics = {
                "issuer_matches": claims.get("iss") == kwargs["issuer"],
                "client_matches": claims.get("azp") == management_config.CLIENT_ID,
                "audience_matches": management_config.CLIENT_ID
                in ([claims.get("aud")] if isinstance(claims.get("aud"), str) else claims.get("aud", [])),
                "bearer_type": claims.get("typ") == "Bearer",
                "auth_time_present": isinstance(claims.get("auth_time"), int),
                "subject_present": isinstance(claims.get("sub"), str),
                "session_present": isinstance(claims.get("sid"), str),
                "pwd_present": "pwd" in claims.get("amr", []),
                "otp_present": "otp" in claims.get("amr", []),
                "id_token_supplied": "id_token" in kwargs,
                "subject_is_uuid": bool(
                    re.fullmatch(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", claims.get("sub", ""))
                ),
                "session_is_uuid": bool(
                    re.fullmatch(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", claims.get("sid", ""))
                ),
                "iat_not_future": claims.get("iat", time.time() + 1) <= time.time(),
                "exp_not_expired": claims.get("exp", 0) > time.time(),
                "lifetime_within_300": 0 < claims.get("exp", 0) - claims.get("iat", 0) <= 300,
                "auth_time_within_300": 0 <= time.time() - claims.get("auth_time", 0) <= 300,
            }
            if "id_token" in kwargs:
                identity = json.loads(base64.urlsafe_b64decode(kwargs["id_token"].split(".")[1] + "=="))
                diagnostics.update(
                    id_nonce_matches=identity.get("nonce") == kwargs.get("nonce"),
                    id_subject_matches=identity.get("sub") == claims.get("sub"),
                )
            (lab.root / "management-token-diagnostic.private.json").write_text(json.dumps(diagnostics) + "\n")
            raise

    monkeypatch.setattr(management, "verify_access", diagnosed_verify_access)

    def fresh_session():
        errors = []
        threads = []

        def announce(url):
            def visit():
                browser = HumanLogin(lab, management_config.CLIENT_ID, username, password)
                try:
                    browser.password_step(authorization_url=url)
                    assert browser.requires_otp()
                    code, new_counter = otp(secret, after_counter=counters[-1])
                    counters.append(new_counter)
                    browser.post_form({"otp": code})
                    assert browser.callback_ready()
                    target = browser.page.headers["location"]
                    assert urlsplit(target)._replace(query="", fragment="").geturl() == management_config.REDIRECT_URI
                    with httpx.Client(trust_env=False, timeout=10) as local:
                        assert local.get(target).status_code == 200
                except Exception as error:
                    errors.append(type(error).__name__)
                finally:
                    browser.close()

            thread = threading.Thread(target=visit, daemon=True)
            threads.append(thread)
            thread.start()

        try:
            path = management.login_session(username=username, announce=announce)
        except RuntimeError as error:
            frames = []
            current_error: BaseException | None = error
            while current_error is not None:
                tb = current_error.__traceback__
                while tb is not None:
                    frames.append(
                        {
                            "function": tb.tb_frame.f_code.co_name,
                            "line": tb.tb_lineno,
                            "type": type(current_error).__name__,
                        }
                    )
                    tb = tb.tb_next
                current_error = current_error.__context__
            (lab.root / "management-login-diagnostic.private.json").write_text(
                json.dumps({"exception_frames": frames, "browser_error_types": errors}) + "\n"
            )
            raise
        for thread in threads:
            thread.join(timeout=10)
        assert not errors and all(not t.is_alive() for t in threads), "REAL_MFA_OPERATOR_BROWSER_DID_NOT_FINISH"
        record = json.loads(path.read_text())
        lab.private_values.append(PrivateValue(record["access_token"]))
        assert set(record) == {"version", "issuer", "client_id", "username", "access_token", "subject", "expires_at"}
        assert path.stat().st_mode & 0o077 == 0
        return path

    first_path = fresh_session()
    manager = management.ManagedAdmin(first_path)
    assert manager.request("GET", base).json()["realm"] == "master"
    executions = manager.request(
        "GET", base + "/authentication/flows/" + management_config.FLOW_ALIAS + "/executions"
    ).json()
    otp_execution = next(e for e in executions if e["providerId"] == "auth-otp-form")
    manager.request(
        "PUT",
        base + "/authentication/flows/" + management_config.FLOW_ALIAS + "/executions",
        body={"id": otp_execution["id"], "priority": otp_execution["priority"], "requirement": "DISABLED"},
        expected=(204,),
    )
    with pytest.raises(RuntimeError, match="MANAGEMENT_SESSION"):
        management.ManagedAdmin(first_path)
    with pytest.raises(RuntimeError, match="CONFIGURATION"):
        management_config.setup(manager)
    assert (
        manager.request("GET", base + "/authentication/flows/" + management_config.FLOW_ALIAS + "/executions").json()[
            1
        ]["requirement"]
        == "DISABLED"
    )
    manager.request(
        "PUT",
        base + "/authentication/flows/" + management_config.FLOW_ALIAS + "/executions",
        body={"id": otp_execution["id"], "priority": otp_execution["priority"], "requirement": "REQUIRED"},
        expected=(204,),
    )
    manager.request("POST", base + "/users/" + subject + "/logout", expected=(204,))
    with pytest.raises(RuntimeError, match="MANAGEMENT"):
        manager.request("GET", base)
    manager.close()
    with pytest.raises(RuntimeError, match="MANAGEMENT_SESSION"):
        management.ManagedAdmin(first_path)

    path = fresh_session()
    monkeypatch.setenv("MT_IDENTITY_ADMIN_SESSION", str(path))
    admin = provision.AdminClient()
    try:
        admin.request("DELETE", base + "/clients/" + bootstrap_id, expected=(204,))
        assert provision.apply()["configured"] is True, "REAL_PROVISION_MUST_WORK_WITHOUT_BOOTSTRAP"
        assert provision.apply()["configured"] is True
        candidate = lab.runtime.parent / "identity-retirement" / "self-owned-real-candidate"
        prepared = retirement.prepare_files(candidate)
        assert prepared["database_credentials_preserved"] is True and prepared["bootstrap_deleted"] is False
        assert "bootstrap_admin" not in json.loads((candidate / "credentials.json").read_text())
        assert "bootstrap-admin-client" not in (candidate / "keycloak-v2.conf").read_text()
        with lab.http() as http:
            denied_secret = http.post(
                lab.public_url + "/realms/master/protocol/openid-connect/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": "bootstrap-project-service",
                    "client_secret": lab.bootstrap_secret,
                },
            )
            denied_token = http.get(lab.admin_url + "/admin/realms", headers={"Authorization": "Bearer " + old_token})
        assert denied_secret.status_code in {400, 401} and denied_token.status_code in {401, 403}

        def authenticate_after_restart():
            nonlocal admin
            renewed_path = fresh_session()
            monkeypatch.setenv("MT_IDENTITY_ADMIN_SESSION", str(renewed_path))
            renewed = provision.AdminClient()
            admin.close()
            admin = renewed
            return admin

        lab.restart(administrator_factory=authenticate_after_restart)
        assert admin.request("GET", base).json()["realm"] == "master"
        assert not any(
            c["clientId"] == "bootstrap-project-service" for c in admin.request("GET", base + "/clients").json()
        )
        admin.request("PUT", base + "/users/" + subject, body={"enabled": False}, expected=(204,))
        with pytest.raises(RuntimeError, match="MANAGEMENT"):
            admin.request("GET", base)
        with pytest.raises(RuntimeError, match="MANAGEMENT"):
            provision.AdminClient()
        lab.record(
            "personal_mfa_management_after_bootstrap_retirement",
            old_bootstrap_denied=True,
            real_provision_succeeded=True,
            restart_persistent=True,
            revoked_session_denied=True,
            disabled_administrator_denied=True,
            shared_runtime_changed=False,
        )
    finally:
        admin.close()
