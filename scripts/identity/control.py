"""Explicit lifecycle for the identity project only; credentials stay in files."""

import argparse
import ipaddress
import json
import os
import secrets
import subprocess
from typing import Any

from . import common, preflight
from .certificates import prepare
from .volumes import install


def preview(action: str) -> dict[str, object]:
    if action not in {"up", "down", "status", "prepare", "build"}:
        raise ValueError("IDENTITY_ACTION_INVALID")
    return {"action": action, "project": common.PROJECT, "applied": False, "deletes_volumes": False}


def command(*args: str) -> list[str]:
    return [
        "docker",
        "--context",
        common.CONTEXT,
        "compose",
        "-p",
        common.PROJECT,
        "-f",
        str(common.ROOT / "deploy/identity/compose.yaml"),
        *args,
    ]


def status() -> dict[str, object]:
    result = common.run(command("ps", "--format", "json"))
    return {"project": common.PROJECT, "services": [json.loads(s) for s in result.splitlines()]}


def prepare_configuration() -> None:
    runtime = common.private_runtime(common.RUNTIME)
    prepare(runtime)
    secret_path = runtime / "credentials.json"
    if secret_path.exists():
        if secret_path.is_symlink() or secret_path.stat().st_mode & 0o077:
            raise RuntimeError("IDENTITY_CREDENTIAL_PERMISSION_INVALID")
        credentials = json.loads(secret_path.read_text())
    else:
        credentials = {k: secrets.token_hex(32) for k in ("db_admin", "db_keycloak", "bootstrap_admin")}
        fd = os.open(secret_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump(credentials, f)
    files = {
        "gateway.conf": (common.ROOT / "deploy/identity/nginx.conf").read_text(),
        "postgres.conf": (common.ROOT / "deploy/identity/postgres.conf").read_text(),
        "pg_hba.conf": (common.ROOT / "deploy/identity/pg_hba.conf").read_text(),
        "admin-password": credentials["db_admin"],
        "keycloak-password": credentials["db_keycloak"],
        "keycloak-v2.conf": "\n".join(
            [
                "db=postgres",
                "db-username=keycloak",
                "db-password=" + credentials["db_keycloak"],
                "db-url=jdbc:postgresql://identity-postgres:5432/keycloak?sslmode=verify-full&sslrootcert=/etc/identity/ca.crt",
                "hostname=https://172.16.58.179:18443",
                "hostname-admin=https://localhost:18444",
                "hostname-strict=true",
                "hostname-backchannel-dynamic=false",
                "http-enabled=false",
                "https-certificate-file=/etc/identity/tls.crt",
                "https-certificate-key-file=/etc/identity/tls.key",
                "proxy-headers=xforwarded",
                "proxy-trusted-addresses=172.31.240.2",
                "http-management-scheme=http",
                "log-level=WARN",
                "http-access-log-enabled=false",
                "bootstrap-admin-client-id=bootstrap-project-service",
                "bootstrap-admin-client-secret=" + credentials["bootstrap_admin"],
            ]
        )
        + "\n",
    }
    for name, data in files.items():
        path = runtime / name
        if path.exists():
            if path.is_symlink() or path.stat().st_mode & 0o077 or path.read_text() != data:
                raise RuntimeError("IDENTITY_PRIVATE_CONFIGURATION_DIFFERS")
        else:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(fd, "w") as f:
                f.write(data)
    install(runtime)


def check_networks() -> None:
    for network_id in common.docker("network", "ls", "-q").splitlines():
        value = json.loads(common.docker("network", "inspect", network_id))[0]
        if value.get("Labels", {}).get("com.docker.compose.project") == common.PROJECT:
            continue
        for item in value["IPAM"].get("Config", []) or []:
            existing = ipaddress.ip_network(item["Subnet"])
            if any(existing.overlaps(ipaddress.ip_network(s)) for s in ("172.31.240.0/28", "172.31.241.0/28")):
                raise RuntimeError("IDENTITY_NETWORK_COLLISION")


def check_image_admission(versions: dict[str, Any]) -> None:
    scan = versions.get("security_scan")
    if (
        not isinstance(scan, dict)
        or scan.get("status") != "PASS_NO_HIGH_OR_CRITICAL"
        or scan.get("high") != 0
        or scan.get("critical") != 0
        or set(versions.get("images", {})) != {"keycloak", "postgres", "nginx"}
        or scan.get("image_references") != {k: v["reference"] for k, v in versions.get("images", {}).items()}
    ):
        raise RuntimeError("IDENTITY_IMAGE_SCAN_NOT_PASSED")


def check_runtime_image_ids(expected: dict[str, str], actual: dict[str, str]) -> None:
    if set(expected) != {"keycloak", "postgres", "nginx"} or expected != actual:
        raise RuntimeError("IDENTITY_RUNTIME_IMAGE_DRIFT")


def owned_ports_from_inspect(containers: list[dict[str, Any]]) -> set[int]:
    expected = {
        "8443/tcp": [{"HostIp": "172.16.58.179", "HostPort": "18443"}],
        "8444/tcp": [{"HostIp": "127.0.0.1", "HostPort": "18444"}],
    }
    for container in containers:
        labels = container.get("Config", {}).get("Labels", {})
        if (
            labels.get("com.docker.compose.project") == common.PROJECT
            and labels.get("com.docker.compose.service") == "identity-gateway"
            and container.get("State", {}).get("Running") is True
            and container.get("NetworkSettings", {}).get("Ports") == expected
        ):
            return {18443, 18444}
    return set()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["prepare", "build", "up", "down", "status"])
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.action == "status":
        print(json.dumps(status()))
        return
    if not args.apply:
        print(json.dumps(preview(args.action)))
        return
    if args.action in {"up", "prepare", "build"}:
        snapshot = preflight.collect()
        ids = common.docker("ps", "-q", "--filter", "label=com.docker.compose.project=" + common.PROJECT).splitlines()
        owned = owned_ports_from_inspect([json.loads(common.docker("inspect", i))[0] for i in ids])
        occupied = snapshot.get("occupied_ports")
        if not isinstance(occupied, list) or any(type(port) is not int for port in occupied):
            raise RuntimeError("IDENTITY_PREFLIGHT_PORT_OBSERVATION_INVALID")
        snapshot["occupied_ports"] = [port for port in occupied if port not in owned]
        errors = preflight.validate(snapshot)
        if errors:
            raise RuntimeError("IDENTITY_PREFLIGHT_BLOCKED:" + ",".join(errors))
        check_networks()
        prepare_configuration()
        if args.action == "build":
            result = subprocess.run(command("build", "--pull=false"), capture_output=True, text=True, timeout=600)
            if result.returncode:
                raise RuntimeError("IDENTITY_BUILD_FAILED")
        if args.action == "up":
            versions = json.loads((common.ROOT / "config/identity/versions.json").read_text())
            check_image_admission(versions)
            references = {
                "keycloak": "media-trace-identity-keycloak:26.8.1-1",
                "postgres": "media-trace-identity-postgres:16.15-alpine-1",
                "nginx": common.image("nginx"),
            }
            actual = {k: common.docker("image", "inspect", v, "--format", "{{.Id}}") for k, v in references.items()}
            check_runtime_image_ids(versions["security_scan"]["runtime_image_ids"], actual)
            result = subprocess.run(
                command("up", "-d", "--no-build", "--pull", "never", "--wait", "--wait-timeout", "240"),
                capture_output=True,
                text=True,
                timeout=600,
            )
            if result.returncode:
                raise RuntimeError("IDENTITY_DEPLOYMENT_FAILED_PRIVATE_LOG_REQUIRED")
    else:
        common.run(command("down"), timeout=120)
    print(json.dumps({"project": common.PROJECT, "applied": True, "action": args.action, "deletes_volumes": False}))


if __name__ == "__main__":
    main()
