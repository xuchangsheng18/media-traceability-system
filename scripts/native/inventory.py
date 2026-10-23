"""Read-only native preparation inventory; never returns raw process environments."""

import datetime
import hashlib
import json
import platform
import subprocess
from typing import Any

PROJECTS = {"media-trace-py310", "media-trace-identity"}
EXPECTED_NAMES = {
    *(
        "media-trace-py310-" + name + "-1"
        for name in ["api", "inference", "postgres", "rabbitmq", "s3", "web", "worker"]
    ),
    *("media-trace-identity-" + name + "-1" for name in ["identity-postgres", "keycloak", "identity-gateway"]),
}


def collect_inventory() -> dict[str, Any]:
    blockers: list[str] = []
    commands: dict[str, dict[str, Any]] = {}
    selected: list[dict[str, str]] = []
    neighbors: list[str] = []
    probes = {
        "containers": [
            "docker",
            "--context",
            "desktop-linux",
            "ps",
            "--no-trunc",
            "--format",
            '{{.ID}}\t{{.Names}}\t{{.Label "com.docker.compose.project"}}',
        ],
        "native_business_postgres": [
            "/workspace/glwy/runtime/media-traceability-system/business-postgres-tools/bin/postgres",
            "--version",
        ],
        "python": ["/opt/conda/glwy/envs/py311/bin/python", "--version"],
        "ports": ["ss", "-H", "-ltn"],
    }
    for key, command in probes.items():
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=20, check=False)
            commands[key] = {"exit_code": result.returncode, "status": "PASS" if result.returncode == 0 else "FAIL"}
            if result.returncode:
                blockers.append(key + ":PROBE_FAILED")
                continue
            if key == "containers":
                for line in result.stdout.splitlines():
                    fields = line.split("\t")
                    if len(fields) != 3:
                        blockers.append("containers:MALFORMED_ROW")
                        continue
                    identifier, name, project = fields
                    if name in EXPECTED_NAMES and project in PROJECTS:
                        selected.append({"container_id": identifier, "name": name, "project": project})
                    else:
                        neighbors.append(identifier + ":" + name)
            elif key in {"python", "native_business_postgres"}:
                # Accept only version syntax; never echo arbitrary failed command output.
                import re

                found = re.search(r"\b\d+\.\d+(?:\.\d+)?\b", result.stdout)
                if found:
                    commands[key]["version"] = found.group()
                else:
                    blockers.append(key + ":VERSION_UNRECOGNIZED")
            elif key == "ports":
                occupied = []
                for port in [24432, 24672, 24833, 24200, 24201, 24180, 28443, 28444, 45432]:
                    if any(
                        line.split()[3].endswith(":" + str(port))
                        for line in result.stdout.splitlines()
                        if len(line.split()) >= 4
                    ):
                        occupied.append(port)
                commands[key]["occupied_staging_ports"] = occupied
                if occupied:
                    blockers.append("ports:STAGING_PORT_OCCUPIED")
        except (OSError, subprocess.TimeoutExpired):
            commands[key] = {"status": "FAIL"}
            blockers.append(key + ":PROBE_UNAVAILABLE")
    if {row["name"] for row in selected} != EXPECTED_NAMES:
        blockers.append("containers:PROJECT_SET_INCOMPLETE")
    return {
        "schema_version": 1,
        "observed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "scope": "readonly_native_preflight_not_complete_data_ownership_or_artifact_admission",
        "status": "FAIL" if blockers else "PASS",
        "blockers": blockers,
        "architecture": platform.machine(),
        "project_containers": sorted(selected, key=lambda row: row["name"]),
        "neighbor_container_count": len(neighbors),
        "neighbor_set_sha256": hashlib.sha256("\n".join(sorted(neighbors)).encode()).hexdigest(),
        "probes": commands,
        "services_changed": False,
        "complete_data_inventory_asserted": False,
    }


if __name__ == "__main__":
    report = collect_inventory()
    print(json.dumps(report))
    raise SystemExit(int(report["status"] != "PASS"))
