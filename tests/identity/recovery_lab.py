"""Disposable real-service fixture. All lifecycle targets have random restore labels."""

import base64
import copy
import hashlib
import html
import json
import os
import re
import secrets
import socket
import ssl
import subprocess
import time
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlencode, urlsplit
from uuid import uuid4

import httpx
import psycopg
import pytest
import yaml
from business_app.db import Database
from business_app.errors import BusinessError
from business_app.identity.directory import IdentityDirectory
from business_app.identity.tokens import IntrospectionSettings, IntrospectionVerifier, MappedTokenAuthority
from psycopg import sql
from psycopg.conninfo import make_conninfo

from scripts.identity import backup, common, control, restore, volumes
from tools.identity_oidc_probe import PrivateValue


class LabAdmin:
    def __init__(self, lab):
        self.lab = lab

    def request(self, method, path, *, body=None, expected=(200,)):
        lab = self.lab
        with lab.http() as client:
            auth = client.post(
                lab.public_url + "/realms/master/protocol/openid-connect/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": "bootstrap-project-service",
                    "client_secret": lab.bootstrap_secret,
                },
            )
            if auth.status_code != 200:
                raise RuntimeError("RECOVERY_LAB_ADMIN_AUTH_FAILED")
            response = client.request(
                method,
                lab.admin_url + path,
                json=body,
                headers={"Authorization": "Bearer " + auth.json()["access_token"]},
            )
        if response.status_code not in expected:
            raise RuntimeError("RECOVERY_LAB_ADMIN_OPERATION_FAILED_" + str(response.status_code))
        return response


class RecoveryLab:
    def __init__(self, root, business_context):
        self.root, self.business_context = root, business_context
        self.root.mkdir(mode=0o700)
        self.original = "media-trace-identity-restore-" + uuid4().hex[:8]
        self.project = self.original
        self.restored = "media-trace-identity-restore-" + uuid4().hex[:8]
        self.runtime = root / "identity"
        self.realm = "media-trace-acceptance-" + uuid4().hex
        self.admin_path = "/admin/realms/" + self.realm
        self.user_id = self.realm_id = ""
        self.api_secret = PrivateValue(secrets.token_hex(32))
        self.password = PrivateValue(secrets.token_hex(24))
        self.username = "synthetic-" + uuid4().hex
        self.private_values = [self.api_secret, self.password]
        self.events = []
        self.mapping_id = None
        self.lookup_role = None
        self.lookup_dsn = None
        self.compose_files = {}
        self.admin = LabAdmin(self)
        self.public_port, self.admin_port = self.free_port(), self.free_port()
        if self.public_port == self.admin_port:
            raise RuntimeError("RECOVERY_LAB_PORT_COLLISION")
        self.public_url = "https://127.0.0.1:" + str(self.public_port)
        self.admin_url = "https://localhost:" + str(self.admin_port)
        self.issuer = self.public_url + "/realms/" + self.realm
        self.redirect = self.admin_url + "/identity-test/callback"
        self.subnets = self.free_subnets()

    @staticmethod
    def free_port():
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            return listener.getsockname()[1]

    @staticmethod
    def docker(*args, data=None, timeout=180):
        process = subprocess.run(
            ["docker", "--context", common.CONTEXT, *args], input=data, capture_output=True, timeout=timeout
        )
        if process.returncode:
            raise RuntimeError("RECOVERY_LAB_DOCKER_OPERATION_FAILED")
        return process.stdout

    def free_subnets(self):
        import ipaddress

        ids = self.docker("network", "ls", "-q").decode().splitlines()
        occupied: list[ipaddress.IPv4Network] = []
        if ids:
            for network in json.loads(self.docker("network", "inspect", *ids)):
                for config in network["IPAM"].get("Config") or []:
                    if config.get("Subnet"):
                        existing = ipaddress.ip_network(config["Subnet"])
                        if isinstance(existing, ipaddress.IPv4Network):
                            occupied.append(existing)
        for number in range(200, 250, 2):
            values = [f"172.30.{number}.0/28", f"172.30.{number + 1}.0/28"]
            if all(not ipaddress.IPv4Network(v).overlaps(o) for v in values for o in occupied):
                return values
        raise RuntimeError("RECOVERY_LAB_NO_ISOLATED_SUBNET")

    def compose(self, *args):
        assert re.fullmatch(r"media-trace-identity-restore-[a-f0-9]{8}", self.project)
        return self.docker(
            "compose", "-p", self.project, "-f", str(self.compose_files[self.project]), *args, timeout=300
        )

    def prepare(self):
        original_install = volumes.install

        def install_private(runtime):
            for name in ["gateway.conf", "keycloak-v2.conf", "pg_hba.conf"]:
                path = runtime / name
                value = path.read_text().replace("172.16.58.179", "127.0.0.1")
                value = value.replace("18443", str(self.public_port)).replace("18444", str(self.admin_port))
                value = value.replace("172.31.240.2", self.subnets[0].split("/")[0][:-1] + "2")
                value = value.replace("172.31.241.0/28", self.subnets[1])
                path.write_text(value)
            return original_install(runtime)

        with (
            patch.object(common, "RUNTIME", self.runtime),
            patch.object(common, "PROJECT", self.original),
            patch.object(control, "install", install_private),
        ):
            control.prepare_configuration()
        credentials = json.loads((self.runtime / "credentials.json").read_text())
        self.bootstrap_secret = PrivateValue(credentials["bootstrap_admin"])
        self.private_values.extend(credentials.values())
        self.candidate_image = "media-trace-identity-recovery-keycloak:" + self.original.rsplit("-", 1)[1]
        # Candidate image only: the shared tag, running service and version lock are untouched.
        build = subprocess.run(
            [
                "docker",
                "--context",
                common.CONTEXT,
                "build",
                "--pull=false",
                "-t",
                self.candidate_image,
                "-f",
                str(common.ROOT / "deploy/identity/Dockerfile.keycloak"),
                str(common.ROOT / "deploy/identity"),
            ],
            capture_output=True,
            timeout=600,
        )
        (self.root / "build.private.log").write_bytes(build.stdout + build.stderr)
        if build.returncode:
            raise RuntimeError("RECOVERY_LAB_CANDIDATE_BUILD_FAILED")
        self.write_compose(self.original)
        self.compose("up", "-d", "--no-build", "--pull", "never")
        self.wait_ready()

    def write_compose(self, project):
        doc = yaml.safe_load((common.ROOT / "deploy/identity/compose.yaml").read_text())
        doc["name"] = project
        for service in doc["services"].values():
            service.pop("build", None)
        keycloak = doc["services"]["keycloak"]
        keycloak["image"] = self.candidate_image
        keycloak["networks"]["application"]["ipv4_address"] = self.subnets[0].split("/")[0][:-1] + "3"
        gateway = doc["services"]["identity-gateway"]
        gateway["networks"]["application"]["ipv4_address"] = self.subnets[0].split("/")[0][:-1] + "2"
        gateway["ports"] = [f"127.0.0.1:{self.public_port}:8443", f"127.0.0.1:{self.admin_port}:8444"]
        for name, subnet in zip(["application", "database"], self.subnets):
            doc["networks"][name]["ipam"]["config"] = [{"subnet": subnet}]
        for service in ["gateway", "keycloak", "postgres"]:
            suffix = "-v2" if service != "gateway" else ""
            doc["volumes"][service + "-secrets"]["name"] = self.original + "_" + service + "-secrets" + suffix
        if project == self.restored:
            doc["volumes"]["identity-data"] = {"external": True, "name": project + "_identity-data"}
        path = self.root / (project + ".yaml")
        path.write_text(yaml.safe_dump(doc))
        self.compose_files[project] = path

    @property
    def data_volume(self):
        return self.project + "_identity-data"

    def http(self):
        return httpx.Client(
            verify=ssl.create_default_context(cafile=str(self.runtime / "pki/ca.crt")),
            timeout=5,
            trust_env=False,
            follow_redirects=False,
        )

    def readiness(self):
        cid = self.compose("ps", "-q", "keycloak").decode().strip()
        raw = self.docker(
            "exec",
            cid,
            "bash",
            "-ec",
            "exec 3<>/dev/tcp/127.0.0.1/9000; printf 'GET /health/ready HTTP/1.0\\r\\nHost: localhost\\r\\n\\r\\n' >&3; cat <&3",
        )
        _, separator, body = raw.partition(b"\r\n\r\n")
        if not separator:
            raise RuntimeError("RECOVERY_LAB_HEALTH_RESPONSE_NOT_READY")
        result = json.loads(body)
        if not isinstance(result, dict) or result.get("status") not in {"UP", "DOWN"}:
            raise RuntimeError("RECOVERY_LAB_HEALTH_RESPONSE_NOT_READY")
        return result

    def wait_ready(self):
        deadline = time.monotonic() + 180
        while time.monotonic() < deadline:
            try:
                if self.readiness()["status"] == "UP":
                    with self.http() as client:
                        if (
                            client.get(self.public_url + "/realms/master/.well-known/openid-configuration").status_code
                            == 200
                        ):
                            return
            except (RuntimeError, ValueError, httpx.HTTPError):
                pass
            time.sleep(1)
        raise RuntimeError("RECOVERY_LAB_READINESS_TIMEOUT")

    def wait_dependency_down(self):
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            try:
                if self.readiness()["status"] == "DOWN":
                    return
            except (RuntimeError, ValueError):
                pass
            time.sleep(1)
        raise AssertionError("KEYCLOAK_READINESS_DID_NOT_DETECT_DATABASE_FAILURE")

    def seed(self):
        value = copy.deepcopy(json.loads((common.ROOT / "config/identity/realm.template.json").read_text()))
        value["realm"] = self.realm
        value["clients"][0]["secret"] = self.api_secret
        value["clients"][1].update(
            clientId="media-trace-probe", enabled=True, redirectUris=[self.redirect], webOrigins=[self.admin_url]
        )
        self.admin.request("POST", "/admin/realms", body=value, expected=(201,))
        self.realm_id = self.admin.request("GET", self.admin_path).json()["id"]
        response = self.admin.request(
            "POST",
            self.admin_path + "/users",
            expected=(201,),
            body={
                "username": self.username,
                "enabled": True,
                "firstName": "Synthetic",
                "lastName": "Recovery",
                "email": self.username + "@example.invalid",
                "emailVerified": True,
                "credentials": [{"type": "password", "value": self.password, "temporary": False}],
            },
        )
        self.user_id = response.headers["location"].rsplit("/", 1)[1]
        (self.runtime / "api-client-secret").write_text(self.api_secret)
        clients = self.admin.request("GET", self.admin_path + "/clients").json()
        self.api_id = next(c["id"] for c in clients if c["clientId"] == "media-trace-api")

    def snapshot(self):
        realm = self.admin.request("GET", self.admin_path).json()
        user = self.admin.request("GET", self.admin_path + "/users/" + self.user_id).json()
        with self.http() as client:
            keys = client.get(self.issuer + "/protocol/openid-connect/certs").json()["keys"]
        return dict(
            realm_id=realm["id"],
            user_id=user["id"],
            user_enabled=user["enabled"],
            clients=sorted(c["id"] for c in self.admin.request("GET", self.admin_path + "/clients").json()),
            signing_kids=sorted(k["kid"] for k in keys if k.get("use") == "sig"),
            not_before=realm.get("notBefore", 0),
        )

    def login(self):
        verifier, state = secrets.token_urlsafe(48), secrets.token_urlsafe(24)
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
        with self.http() as client:
            page = client.get(
                self.issuer
                + "/protocol/openid-connect/auth?"
                + urlencode(
                    dict(
                        client_id="media-trace-probe",
                        redirect_uri=self.redirect,
                        response_type="code",
                        scope="openid",
                        state=state,
                        nonce=secrets.token_urlsafe(24),
                        code_challenge=challenge,
                        code_challenge_method="S256",
                    )
                )
            )
            match = re.search(r'<form[^>]*\baction="([^"]+)"', page.text)
            if page.status_code != 200 or match is None:
                raise RuntimeError("RECOVERY_LAB_REAL_LOGIN_FORM_MISSING")
            action = html.unescape(match.group(1))
            if not action.startswith(self.public_url + "/realms/" + self.realm + "/login-actions/"):
                raise RuntimeError("RECOVERY_LAB_LOGIN_FORM_ORIGIN_MISMATCH")
            response = client.post(action, data={"username": self.username, "password": self.password})
            callback = urlsplit(response.headers.get("location", ""))
            values = parse_qs(callback.query)
            if (
                response.status_code != 302
                or callback._replace(query="", fragment="").geturl() != self.redirect
                or values.get("state") != [state]
            ):
                raise RuntimeError("RECOVERY_LAB_REAL_LOGIN_CALLBACK_FAILED")
            token = client.post(
                self.issuer + "/protocol/openid-connect/token",
                data=dict(
                    grant_type="authorization_code",
                    client_id="media-trace-probe",
                    redirect_uri=self.redirect,
                    code=values["code"][0],
                    code_verifier=verifier,
                ),
            )
            if token.status_code != 200:
                raise RuntimeError("RECOVERY_LAB_REAL_CODE_EXCHANGE_FAILED")
        result = {key: PrivateValue(value) if isinstance(value, str) else value for key, value in token.json().items()}
        self.private_values.extend([*values["code"], *[v for k, v in result.items() if k.endswith("token")]])
        return result

    def introspect_status(self, token, secret):
        with self.http() as client:
            return client.post(
                self.issuer + "/protocol/openid-connect/token/introspect",
                auth=httpx.BasicAuth("media-trace-api", secret),
                data={"token": token},
            ).status_code

    def introspect(self, token):
        with self.http() as client:
            response = client.post(
                self.issuer + "/protocol/openid-connect/token/introspect",
                auth=httpx.BasicAuth("media-trace-api", self.api_secret),
                data={"token": token},
            )
        if response.status_code != 200:
            raise RuntimeError("RECOVERY_LAB_INTROSPECTION_FAILED")
        return response.json()

    def verify(self, token):
        settings = IntrospectionSettings(
            self.issuer + "/protocol/openid-connect/token/introspect",
            self.issuer,
            "media-trace-api",
            "media-trace-api",
            self.api_secret,
            2,
            65536,
            16384,
        )
        checker = IntrospectionVerifier(
            settings, ssl_context=ssl.create_default_context(cafile=str(self.runtime / "pki/ca.crt"))
        )
        try:
            return checker.verify(token)
        finally:
            checker.close()

    def refresh_status(self, token):
        with self.http() as client:
            return client.post(
                self.issuer + "/protocol/openid-connect/token",
                data=dict(grant_type="refresh_token", refresh_token=token, client_id="media-trace-probe"),
            ).status_code

    def revoke_sessions(self):
        self.admin.request("POST", self.admin_path + "/users/" + self.user_id + "/logout", expected=(204,))

    def rotate_secret(self):
        value = self.admin.request("POST", self.admin_path + "/clients/" + self.api_id + "/client-secret").json()[
            "value"
        ]
        self.api_secret = PrivateValue(value)
        self.private_values.append(self.api_secret)
        return self.api_secret

    def restart(self):
        self.compose("restart", "identity-postgres", "keycloak", "identity-gateway")
        self.wait_ready()

    def backup(self, recovery_key):
        home, public, signer = recovery_key
        with patch.object(common, "RUNTIME", self.runtime), patch.object(common, "PROJECT", self.original):
            report = backup.run_backup(public, self.root / "identity-backups", home, signer)
        database, target = report["database"], report["database_backup"]
        assert isinstance(database, dict) and isinstance(target, str)
        self.record("signed_encrypted_backup", database_sha256=database["sha256"], plaintext_dump_written=False)
        return Path(target)

    def restore(self, encrypted, recovery_key):
        home, _, signer = recovery_key
        self.compose("down")
        with patch.object(common, "PROJECT", self.original):
            report = restore.restore_database(encrypted, self.restored, home, signer)
        assert report["sessions_and_secrets_reconciled"] is False
        self.docker("rm", self.restored + "-postgres")  # Stopped container only, its new data volume is retained.
        self.project = self.restored
        self.write_compose(self.restored)
        self.compose("up", "-d", "--no-build", "--pull", "never")
        self.wait_ready()

    def rollback(self):
        from scripts.identity.reconcile import reconcile

        self.audit_project_logs()
        self.compose("down")
        self.project = self.original
        self.compose("up", "-d", "--no-build", "--pull", "never")
        self.wait_ready()
        result = reconcile(self.admin, realm=self.realm, expected_realm_id=self.realm_id, client_id="media-trace-api")
        self.api_secret = PrivateValue(result.client_secret)
        self.private_values.append(self.api_secret)
        return result

    def assert_exact_business_mapping(self, token):
        context = self.business_context
        database = Database(context["admin_dsn"])
        if self.lookup_dsn is None:
            self.lookup_role = "mt_recovery_lookup_" + uuid4().hex
            password = PrivateValue(secrets.token_hex(32))
            self.private_values.append(password)
            with psycopg.connect(context["admin_dsn"]) as admin:
                admin.execute(
                    sql.SQL("CREATE ROLE {} LOGIN NOSUPERUSER NOBYPASSRLS PASSWORD {}").format(
                        sql.Identifier(self.lookup_role), sql.Literal(password)
                    )
                )
                admin.execute(sql.SQL("GRANT mt_identity_lookup TO {}").format(sql.Identifier(self.lookup_role)))
            self.lookup_dsn = PrivateValue(
                make_conninfo(context["admin_dsn"], user=self.lookup_role, password=password)
            )
        lookup = Database(self.lookup_dsn)
        settings = IntrospectionSettings(
            self.issuer + "/protocol/openid-connect/token/introspect",
            self.issuer,
            "media-trace-api",
            "media-trace-api",
            self.api_secret,
            2,
            65536,
            16384,
        )
        checker = IntrospectionVerifier(
            settings, ssl_context=ssl.create_default_context(cafile=str(self.runtime / "pki/ca.crt"))
        )
        try:
            with database.engine.begin() as connection:
                directory = IdentityDirectory(connection)
                if self.mapping_id is None:
                    self.mapping_id = directory.bind_identity(
                        user_id=context["actor"].user_id,
                        org_id=context["actor"].org_id,
                        issuer=self.issuer,
                        subject=self.user_id,
                        mapping_version="synthetic-recovery-v1",
                        enabled=True,
                    )
                resolved = directory.resolve(self.issuer, self.user_id)
                assert resolved.identity_id == self.mapping_id
                assert resolved.user_id == context["actor"].user_id and resolved.org_id == context["actor"].org_id
            authority = MappedTokenAuthority(checker, lookup)
            assert authority.authenticate(token) == context["actor"]
            with pytest.raises(BusinessError):
                authority.authorize_case(context["actor"], context["case_id"], "asset:read")
        finally:
            checker.close()
            lookup.close()
            database.close()

    def record(self, name, **values):
        image = self.docker("image", "inspect", self.candidate_image, "--format", "{{.Id}}").decode().strip()
        self.events.append({"name": name, "status": "PASS", "candidate_keycloak_image_id": image, **values})

    def audit_project_logs(self):
        from scripts.identity.privacy import scan_bytes

        logs = self.compose("logs", "--no-color")
        (self.root / (self.project + ".runtime.private.log")).write_bytes(logs)
        values = tuple(str(value).encode() for value in self.private_values)
        findings = scan_bytes(logs, values)
        if findings:
            raise AssertionError("RECOVERY_LAB_RUNTIME_CREDENTIAL_LEAK")

    def close(self):
        try:
            if self.project in self.compose_files:
                try:
                    self.audit_project_logs()
                finally:
                    self.compose("down")
        finally:
            if self.lookup_role is not None:
                with psycopg.connect(self.business_context["admin_dsn"]) as admin:
                    admin.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(self.lookup_role)))
                    admin.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(self.lookup_role)))
        (self.root / "safe-events.json").write_text(
            json.dumps(
                {
                    "events": self.events,
                    "public_cutover": False,
                    "shared_services_restarted": False,
                    "data_volumes_retained": True,
                    "formal_accepted": False,
                },
                indent=2,
            )
            + "\n"
        )


@pytest.fixture
def recovery_lab(identity_config, business_context):
    root = Path(identity_config["private_test_root"]).parent / ("recovery-" + uuid4().hex)
    if root.is_symlink() or any(p.is_symlink() for p in root.parents):
        raise RuntimeError("RECOVERY_LAB_PRIVATE_ROOT_REQUIRED")
    old_mask = os.umask(0o077)
    lab = RecoveryLab(root, business_context)
    try:
        lab.prepare()
        yield lab
    finally:
        try:
            lab.close()
        finally:
            os.umask(old_mask)
