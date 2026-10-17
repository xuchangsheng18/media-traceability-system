"""Read-only, fail-closed observations; never starts or pulls containers."""

import argparse
import datetime
import json
import os
import platform
import shutil
import sys
from pathlib import Path
from typing import Any

from .common import CONTEXT, MINIMUM_FREE, SERVICES, docker, run


def collect() -> dict[str, object]:
    result: dict[str, object] = {
        "observed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "platform": sys.platform,
        "architecture": platform.machine(),
        "python": platform.python_version(),
        "docker_context": CONTEXT,
        "source_commit": run(["git", "rev-parse", "HEAD"]),
        "host_available_bytes": shutil.disk_usage("/workspace").free,
        "services": {},
        "occupied_ports": [],
    }
    try:
        result["docker_server_version"] = docker("version", "--format", "{{.Server.Version}}")
        records = [
            json.loads(line)
            for line in docker(
                "ps", "--filter", "label=com.docker.compose.project=media-trace-py310", "--format", "{{json .}}"
            ).splitlines()
        ]
        containers = [json.loads(docker("inspect", row["ID"]))[0] for row in records]
        result["services"] = {
            c["Config"]["Labels"]["com.docker.compose.service"]: c["State"].get("Health", {}).get("Status", "unknown")
            for c in containers
            if c["State"]["Running"]
        }
        pg = next(c["Id"] for c in containers if c["Config"]["Labels"]["com.docker.compose.service"] == "postgres")
        result["vm_available_bytes"] = int(
            docker("exec", pg, "df", "-P", "-B1", "/var/lib/postgresql/data").splitlines()[-1].split()[3]
        )
        occupied = []
        for port in (18443, 18444):
            if run(["ss", "-H", "-ltn", f"sport = :{port}"]):
                occupied.append(port)
        result["occupied_ports"] = occupied
        result["time_synchronized"] = run(["timedatectl", "show", "-p", "NTPSynchronized", "--value"]) == "yes"
    except (RuntimeError, OSError, ValueError, KeyError, StopIteration):
        result["observation_failed"] = True
    return result


def validate(snapshot: dict[str, Any]) -> list[str]:
    errors = []
    for field, expected in (("platform", "linux"), ("architecture", "x86_64"), ("docker_context", CONTEXT)):
        if snapshot.get(field) != expected:
            errors.append("UNSUPPORTED_" + field.upper())
    if not str(snapshot.get("python", "")).startswith("3.10."):
        errors.append("PY310_REQUIRED")
    if not snapshot.get("docker_server_version"):
        errors.append("DOCKER_OBSERVATION_MISSING")
    for field, code in (
        ("host_available_bytes", "HOST_CAPACITY_INSUFFICIENT"),
        ("vm_available_bytes", "VM_CAPACITY_INSUFFICIENT"),
    ):
        size = snapshot.get(field)
        if type(size) is not int or size <= MINIMUM_FREE:
            errors.append(code)
    ports = snapshot.get("occupied_ports")
    if not isinstance(ports, list) or ports:
        errors.append("IDENTITY_PORT_IN_USE" if isinstance(ports, list) else "PORT_OBSERVATION_MISSING")
    services = snapshot.get("services")
    if not isinstance(services, dict) or set(services) != SERVICES or any(s != "healthy" for s in services.values()):
        errors.append("ORIGINAL_SERVICES_NOT_HEALTHY")
    if snapshot.get("time_synchronized") is not True:
        errors.append("TIME_SYNCHRONIZATION_REQUIRED")
    if snapshot.get("observation_failed"):
        errors.append("OBSERVATION_INCOMPLETE")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    snapshot = collect()
    errors = validate(snapshot)
    report = {
        "status": "BLOCKED" if errors else "PASS",
        "scope": "read_only_predeployment",
        "observations": snapshot,
        "blocking_reasons": errors,
        "services_started": False,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(args.report, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as output:
        json.dump(report, output, indent=2)
        output.write("\n")
    print(json.dumps(report))
    raise SystemExit(bool(errors))


if __name__ == "__main__":
    main()
