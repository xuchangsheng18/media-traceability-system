"""Management selection and retirement preparation must never revive bootstrap."""

import importlib
import json
import os
from pathlib import Path

import pytest


@pytest.mark.parametrize("failure_at", ["enable", "verify", "rollback"])
def test_setup_transport_failure_disables_only_confirmed_new_client(monkeypatch, failure_at):
    from uuid import uuid4

    import httpx

    from scripts.identity import management_config as module

    flow_id, client_id = str(uuid4()), str(uuid4())

    class Administrator:
        def __init__(self):
            self.flow_created = False
            self.executions = {}
            self.enable_calls = []

        def request(self, method, path, *, body=None, expected=(200,)):
            if method == "GET" and path == module.BASE:
                return httpx.Response(200, json={"realm": "master"})
            if method == "GET" and path == module.BASE + "/clients":
                return httpx.Response(200, json=[])
            if path == module.BASE + "/authentication/flows":
                if method == "POST":
                    self.flow_created = True
                    return httpx.Response(201)
                return httpx.Response(
                    200,
                    json=[dict(id=flow_id, alias=module.FLOW_ALIAS, providerId="basic-flow", builtIn=False)]
                    if self.flow_created
                    else [],
                )
            if method == "POST" and path == module.BASE + "/authentication/executions":
                execution_id = str(uuid4())
                self.executions[execution_id] = dict(body)
                return httpx.Response(
                    201, headers={"location": module.BASE + "/authentication/executions/" + execution_id}
                )
            if method == "GET" and path.rsplit("/", 1)[-1] in self.executions:
                return httpx.Response(200, json=self.executions[path.rsplit("/", 1)[-1]])
            if method == "POST" and path.endswith("/config"):
                return httpx.Response(201)
            if method == "POST" and path == module.BASE + "/clients":
                return httpx.Response(201, headers={"location": module.BASE + "/clients/" + client_id})
            if path == module.BASE + "/clients/" + client_id:
                if method == "GET":
                    return httpx.Response(200, json={"clientId": module.CLIENT_ID, "enabled": False})
                if "enabled" in body:
                    self.enable_calls.append(body["enabled"])
                    if body["enabled"] is True and failure_at == "enable":
                        raise httpx.ReadTimeout("self-owned lost enable response")
                    if body["enabled"] is False and failure_at == "rollback":
                        raise httpx.ConnectError("self-owned unavailable rollback")
                return httpx.Response(204)
            raise AssertionError("unexpected management target")

    verification_calls = []

    def verify(admin, *, enabled=True):
        verification_calls.append(enabled)
        if enabled:
            raise httpx.ReadTimeout("self-owned failed final read")
        return {"client_uuid": client_id, "flow_uuid": flow_id}

    monkeypatch.setattr(module, "_master_protected", lambda realm: True)
    monkeypatch.setattr(module, "verify_configuration", verify)
    admin = Administrator()
    expected = "STATE_UNCERTAIN" if failure_at == "rollback" else "INCOMPLETE_REVIEW_REQUIRED"
    with pytest.raises(RuntimeError, match=expected):
        module.setup(admin)
    assert admin.enable_calls == [True, False]
    assert verification_calls == ([False] if failure_at == "enable" else [False, True])


def management():
    assert importlib.util.find_spec("scripts.identity.management") is not None, "PERSONAL_MANAGEMENT_MISSING"
    return importlib.import_module("scripts.identity.management")


def retirement():
    assert importlib.util.find_spec("scripts.identity.retirement") is not None, "RETIREMENT_PREPARATION_MISSING"
    return importlib.import_module("scripts.identity.retirement")


def test_callback_accepts_only_exact_state_issuer_and_one_code():
    module = management()
    assert (
        module.callback_code(
            "/identity-admin/callback?state=expected-state&code=self-owned-code&iss=https%3A%2F%2Fidentity.test%2Frealms%2Fmaster",
            state="expected-state",
            issuer="https://identity.test/realms/master",
        )
        == "self-owned-code"
    )


@pytest.mark.parametrize(
    "query",
    [
        "state=wrong&code=one&iss=https%3A%2F%2Fidentity.test%2Frealms%2Fmaster",
        "state=expected-state&code=one&code=two&iss=https%3A%2F%2Fidentity.test%2Frealms%2Fmaster",
        "state=expected-state&state=expected-state&code=one&iss=https%3A%2F%2Fidentity.test%2Frealms%2Fmaster",
        "state=expected-state&code=one&iss=https%3A%2F%2Fother.test%2Frealms%2Fmaster",
        "state=expected-state&code=one",
        "state=expected-state&error=access_denied&iss=https%3A%2F%2Fidentity.test%2Frealms%2Fmaster",
        "state=expected-state&code=&iss=https%3A%2F%2Fidentity.test%2Frealms%2Fmaster",
    ],
)
def test_mixed_duplicate_or_error_callbacks_never_yield_a_code(query):
    module = management()
    with pytest.raises(RuntimeError, match="CALLBACK"):
        module.callback_code(
            "/identity-admin/callback?" + query, state="expected-state", issuer="https://identity.test/realms/master"
        )


@pytest.mark.parametrize("selected_by_environment", [False, True])
def test_invalid_selected_personal_session_never_attempts_bootstrap(tmp_path, monkeypatch, selected_by_environment):
    from scripts.identity import common
    from scripts.identity.provision import AdminClient

    root = tmp_path / "identity"
    root.mkdir(mode=0o700)
    monkeypatch.setattr(common, "RUNTIME", root)
    (root / "credentials.json").write_text(json.dumps({"bootstrap_admin": "self-owned-existing-bootstrap"}))
    selected = root / "admin-sessions" / "missing.json"
    if selected_by_environment:
        monkeypatch.setenv("MT_IDENTITY_ADMIN_SESSION", str(selected))
    else:
        monkeypatch.delenv("MT_IDENTITY_ADMIN_SESSION", raising=False)
    with pytest.raises(RuntimeError, match="MANAGEMENT_SESSION"):
        AdminClient(**({} if selected_by_environment else {"session_file": selected}))


def test_retirement_candidates_preserve_database_and_original_inputs():
    module = retirement()
    credentials = {
        "db_admin": "self-owned-db-a",
        "db_keycloak": "self-owned-db-k",
        "bootstrap_admin": "self-owned-bootstrap",
    }
    config = "db=postgres\ndb-password=self-owned-db-k\nbootstrap-admin-client-id=bootstrap-project-service\nbootstrap-admin-client-secret=self-owned-bootstrap\nhttps-certificate-file=/etc/identity/tls.crt\n"
    candidate = module.candidate_contents(config, credentials)
    assert candidate["credentials"] == {"db_admin": "self-owned-db-a", "db_keycloak": "self-owned-db-k"}
    assert (
        candidate["configuration"]
        == "db=postgres\ndb-password=self-owned-db-k\nhttps-certificate-file=/etc/identity/tls.crt\n"
    )
    assert credentials["bootstrap_admin"] == "self-owned-bootstrap"
    assert "bootstrap-admin-client-secret=" in config


@pytest.mark.parametrize("change", ["duplicate", "wrong_secret", "wrong_client", "partial"])
def test_inconsistent_retirement_sources_require_review(change):
    module = retirement()
    credentials = {
        "db_admin": "self-owned-db-a",
        "db_keycloak": "self-owned-db-k",
        "bootstrap_admin": "self-owned-bootstrap",
    }
    config = "db=postgres\nbootstrap-admin-client-id=bootstrap-project-service\nbootstrap-admin-client-secret=self-owned-bootstrap\n"
    if change == "duplicate":
        config += "bootstrap-admin-client-secret=self-owned-bootstrap\n"
    elif change == "wrong_secret":
        credentials["bootstrap_admin"] = "self-owned-mismatched"
    elif change == "wrong_client":
        config = config.replace("bootstrap-project-service", "unrelated-client")
    else:
        credentials.pop("bootstrap_admin")
    with pytest.raises(RuntimeError, match="RETIREMENT_SOURCE"):
        module.candidate_contents(config, credentials)


def test_private_candidates_do_not_change_existing_runtime(tmp_path, monkeypatch):
    from scripts.identity import common

    module = retirement()
    runtime = tmp_path / "identity"
    runtime.mkdir(mode=0o700)
    monkeypatch.setattr(common, "RUNTIME", runtime)
    files = {
        "credentials.json": json.dumps(
            {"db_admin": "self-owned-db-a", "db_keycloak": "self-owned-db-k", "bootstrap_admin": "self-owned-bootstrap"}
        ),
        "keycloak-v2.conf": "db=postgres\nbootstrap-admin-client-id=bootstrap-project-service\nbootstrap-admin-client-secret=self-owned-bootstrap\n",
    }
    for name, content in files.items():
        p = runtime / name
        p.write_text(content)
        p.chmod(0o600)
    target = tmp_path / "identity-retirement" / "self-owned-candidate"
    result = module.prepare_files(target)
    assert result["status"] == "PREPARED_PRIVATE_CANDIDATES_NOT_ADOPTED"
    assert result["bootstrap_deleted"] is False and result["shared_configuration_replaced"] is False
    assert result["formal_accepted"] is False
    for name, content in files.items():
        assert (runtime / name).read_text() == content
    assert json.loads((target / "credentials.json").read_text()) == {
        "db_admin": "self-owned-db-a",
        "db_keycloak": "self-owned-db-k",
    }
    assert (target / "credentials.json").stat().st_mode & 0o077 == 0
    assert "self-owned-bootstrap" not in json.dumps(result)
    with pytest.raises(RuntimeError, match="EXISTS"):
        module.prepare_files(target)


def test_configuration_preparation_cannot_recreate_retired_bootstrap(tmp_path, monkeypatch):
    from scripts.identity import common, control

    runtime = tmp_path / "identity"
    runtime.mkdir(mode=0o700)
    monkeypatch.setattr(common, "RUNTIME", runtime)
    monkeypatch.setattr(control, "prepare", lambda runtime: None)
    monkeypatch.setattr(control, "install", lambda runtime: None)
    credentials = runtime / "credentials.json"
    credentials.write_text(json.dumps({"db_admin": "self-owned-db-a", "db_keycloak": "self-owned-db-k"}))
    os.chmod(credentials, 0o600)
    control.prepare_configuration()
    assert "bootstrap" not in (runtime / "keycloak-v2.conf").read_text()
    assert json.loads(credentials.read_text()) == {"db_admin": "self-owned-db-a", "db_keycloak": "self-owned-db-k"}


def test_management_preview_never_reads_private_credentials_or_prompts(tmp_path):
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "scripts.identity.management", "setup"], capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0, "MANAGEMENT_PREVIEW_MUST_NOT_ACCESS_AN_IDENTITY_TARGET"
    value = json.loads(result.stdout)
    assert value["applied"] is False and value["bootstrap_deleted"] is False


@pytest.mark.parametrize(
    "change",
    [
        "valid",
        "opaque_session",
        "empty_session",
        "oversized_session",
        "control_session",
        "nonstring_session",
        "signature",
        "id_token",
        "expired",
        "future",
        "no_otp",
        "no_password",
        "issuer",
        "audience",
        "client",
        "long_lived",
        "ambiguous_key",
    ],
)
def test_management_verifier_requires_signature_mfa_client_and_short_expiry(change):
    import shutil
    import subprocess

    module = management()
    assert hasattr(module, "verify_access"), "SIGNED_MANAGEMENT_VERIFIER_MISSING"
    node = shutil.which("node")
    assert node is not None, "EXISTING_LOCKED_NODE_REQUIRED"
    program = r"""
const {generateKeyPairSync,sign}=require('node:crypto');
const {privateKey,publicKey}=generateKeyPairSync('rsa',{modulusLength:2048});
const now=Math.floor(Date.now()/1000);
const claims={iss:'https://identity.test/realms/master',aud:'media-trace-admin-tools',azp:'media-trace-admin-tools',sub:'5dc976ba-734d-4626-b536-1b67845a16e8',sid:'123b06d8-3af3-4e7c-a5dc-6f93fb545d65',typ:'Bearer',iat:now,auth_time:now,exp:now+300,amr:['pwd','otp']};
const change=process.argv[1];
if(change==='opaque_session')claims.sid='self-owned-opaque-sid-24';
if(change==='empty_session')claims.sid='';
if(change==='oversized_session')claims.sid='A'.repeat(257);
if(change==='control_session')claims.sid='self-owned\nsession';
if(change==='nonstring_session')claims.sid=42;
if(change==='id_token')claims.typ='ID';
if(change==='expired')claims.exp=now-1;
if(change==='future')claims.iat=now+60;
if(change==='no_otp')claims.amr=['pwd'];
if(change==='no_password')claims.amr=['otp'];
if(change==='issuer')claims.iss='https://other.test/realms/master';
if(change==='audience')claims.aud='different-client';
if(change==='client')claims.azp='different-client';
if(change==='long_lived')claims.exp=now+3600;
const enc=x=>Buffer.from(JSON.stringify(x)).toString('base64url');
const raw=enc({alg:'RS256',kid:'self-owned-unit-key'})+'.'+enc(claims);
let token=raw+'.'+sign('RSA-SHA256',Buffer.from(raw),privateKey).toString('base64url');
if(change==='signature')token=token.slice(0,token.lastIndexOf('.')+1)+'A'.repeat(342);
const jwk={...publicKey.export({format:'jwk'}),kid:'self-owned-unit-key',use:'sig',alg:'RS256'};
process.stdout.write(JSON.stringify({token,jwks:{keys:change==='ambiguous_key'?[jwk,jwk]:[jwk]}}));
"""
    made = subprocess.run([node, "-e", program, change], capture_output=True, text=True, timeout=10)
    assert made.returncode == 0, "SELF_OWNED_CRYPTO_FIXTURE_FAILED"
    fixture = json.loads(made.stdout)
    if change in {"valid", "opaque_session"}:
        verified = module.verify_access(
            fixture["token"], fixture["jwks"], issuer="https://identity.test/realms/master", node_executable=node
        )
        assert verified["subject"] == "5dc976ba-734d-4626-b536-1b67845a16e8"
        if change == "opaque_session":
            assert verified["session_id"] == "self-owned-opaque-sid-24"
    else:
        with pytest.raises(RuntimeError, match="MANAGEMENT_TOKEN"):
            module.verify_access(
                fixture["token"], fixture["jwks"], issuer="https://identity.test/realms/master", node_executable=node
            )


def test_slow_loopback_connection_cannot_block_a_later_valid_callback():
    import subprocess
    import sys

    program = r"""
import json,socket,threading,urllib.parse,httpx
from scripts.identity import management
management._node=lambda executable=None: 'external-crypto-probe-not-used-by-this-transport-test'
reached=[];connections=[];workers=[]
def stop_before_external_network():
    reached.append(True)
    raise RuntimeError('SELF_OWNED_TRANSPORT_TEST_STOPS_BEFORE_TOKEN_EXCHANGE')
management._http=stop_before_external_network
def announce(url):
    slow=socket.create_connection(('127.0.0.1',18765));connections.append(slow)
    slow.sendall(b'GET /unfinished')
    values=urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
    target='http://127.0.0.1:18765/identity-admin/callback?'+urllib.parse.urlencode({'state':values['state'][0],'iss':'https://172.16.58.179:18443/realms/master','code':'self-owned-code'})
    def finish():
        with httpx.Client(trust_env=False,timeout=4) as http:
            response=http.get(target)
            assert response.status_code==200
    worker=threading.Thread(target=finish,daemon=True);workers.append(worker);worker.start()
try:
    management.login_session(username='synthetic-transport-admin',announce=announce)
except RuntimeError:
    assert reached, 'A_LOCAL_SLOW_CONNECTION_MUST_NOT_PIN_THE_CALLBACK_SERVER'
finally:
    for connection in connections:connection.close()
    for worker in workers:worker.join(timeout=1)
print(json.dumps({'transition_to_exchange':bool(reached)}))
"""
    root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, "-c", program],
        capture_output=True,
        text=True,
        timeout=8,
        env={**os.environ, "PYTHONPATH": os.pathsep.join([str(root / "backend"), str(root)])},
    )
    assert result.returncode == 0, "VALID_CALLBACK_MUST_PROGRESS_AFTER_A_SLOW_LOCAL_PEER"
    assert json.loads(result.stdout) == {"transition_to_exchange": True}


def test_retirement_handles_property_whitespace_without_retaining_bootstrap():
    module = retirement()
    config = "db=postgres\n bootstrap-admin-client-id =bootstrap-project-service\n bootstrap-admin-client-secret =self-owned-bootstrap\n"
    result = module.candidate_contents(
        config,
        {"db_admin": "self-owned-db-a", "db_keycloak": "self-owned-db-k", "bootstrap_admin": "self-owned-bootstrap"},
    )
    assert result["configuration"] == "db=postgres\n"


def test_retirement_refuses_a_retained_copy_of_the_temporary_secret():
    module = retirement()
    config = "db=postgres\nbootstrap-admin-client-id=bootstrap-project-service\nbootstrap-admin-client-secret=self-owned-bootstrap\n"
    credentials = {
        "db_admin": "self-owned-db-a",
        "db_keycloak": "self-owned-db-k",
        "bootstrap_admin": "self-owned-bootstrap",
        "future_metadata": {"retained": "self-owned-bootstrap"},
    }
    with pytest.raises(RuntimeError, match="RETIREMENT_SOURCE"):
        module.candidate_contents(config, credentials)
