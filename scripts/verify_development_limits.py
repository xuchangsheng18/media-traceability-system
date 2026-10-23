"""Read only: compare Compose candidate limits with Docker and the actual cgroup v2."""

import datetime
import hashlib
import json
import re
import subprocess
from fractions import Fraction
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

ROOT = Path(__file__).resolve().parents[1]


def memory_bytes(value: Any) -> int:
    match = re.fullmatch(r"([0-9]+)([kmg]?)", str(value).lower())
    if match is None:
        raise ValueError("UNSUPPORTED_MEMORY_LIMIT")
    return int(match[1]) * 1024 ** {"": 0, "k": 1, "m": 2, "g": 3}[match[2]]


def check_limits(declared: dict[str, Any], inspected: dict[str, int], kernel: str) -> bool:
    try:
        expected = (memory_bytes(declared["mem_limit"]), Fraction(str(declared["cpus"])), int(declared["pids_limit"]))
        lines = kernel.splitlines()
        if len(lines) != 3:
            return False
        cpu = lines[1].split()
        if len(cpu) != 2:
            return False
        actual = (int(lines[0]), Fraction(int(cpu[0]), int(cpu[1])), int(lines[2]))
        configured = (inspected["memory"], Fraction(inspected["nano_cpus"], 10**9), inspected["pids"])
        return all(value > 0 for value in expected) and expected == actual == configured
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return False


def main() -> int:
    if TYPE_CHECKING:
        from scripts.poc_control import compose, docker_env
    else:
        from poc_control import compose, docker_env

    definition = ROOT / "deploy/docker-compose.yml"
    services = yaml.safe_load(definition.read_text(encoding="utf-8"))["services"]
    environment = docker_env()
    observations = []
    for service, declared in sorted(services.items()):
        try:
            identifiers = compose("ps", "-q", service, capture=True).stdout.split()
            if len(identifiers) != 1:
                raise ValueError("ONE_RUNNING_CONTAINER_REQUIRED")
            identifier = identifiers[0]
            template = (
                '{"memory":{{.HostConfig.Memory}},"nano_cpus":{{.HostConfig.NanoCpus}},'
                '"pids":{{.HostConfig.PidsLimit}}}'
            )
            inspect = subprocess.run(
                ["docker", "inspect", "--format", template, identifier],
                env=environment,
                capture_output=True,
                text=True,
                check=True,
            )
            inspected = json.loads(inspect.stdout)
            kernel = subprocess.run(
                [
                    "docker",
                    "exec",
                    identifier,
                    "cat",
                    "/sys/fs/cgroup/memory.max",
                    "/sys/fs/cgroup/cpu.max",
                    "/sys/fs/cgroup/pids.max",
                ],
                env=environment,
                capture_output=True,
                text=True,
                check=True,
            ).stdout
            valid = check_limits(declared, inspected, kernel)
            observations.append(
                {
                    "service": service,
                    "status": "PASS" if valid else "FAIL",
                    "docker_limits": inspected,
                    "cgroup_v2_limits": kernel.splitlines(),
                }
            )
        except (subprocess.SubprocessError, ValueError, KeyError, TypeError, OSError):
            # Never include raw Docker errors: endpoints and private paths are not needed in this report.
            observations.append(
                {"service": service, "status": "FAIL", "reason": "LIMITS_UNREADABLE_OR_SERVICE_MISSING"}
            )
    passed = bool(services) and all(row["status"] == "PASS" for row in observations)
    report = {
        "status": "PASS" if passed else "FAIL",
        "observed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "scope": "configured_development_limits_match_actual_cgroup_v2_only",
        "python_profile": "py311",
        "compose_sha256": hashlib.sha256(definition.read_bytes()).hexdigest(),
        "services": observations,
        "services_restarted": False,
        "limits_changed": False,
        "resource_exhaustion_tested": False,
        "temporary_disk_limit_verified": False,
        "formal_project_quotas_approved": False,
        "production_or_HA_acceptance": False,
    }
    (ROOT / "docs/00-project/validation/development-container-limits-report.json").write_bytes(
        (json.dumps(report, indent=2) + "\n").encode("utf-8")
    )
    print(
        json.dumps(
            {key: report[key] for key in ["status", "scope", "services_restarted", "formal_project_quotas_approved"]}
        )
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
