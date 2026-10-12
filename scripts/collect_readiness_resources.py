"""Read host/own-development-volume facts; do not allocate resources or restart."""
import datetime
import json
import os
import shutil
import subprocess
import sys

from poc_control import ROOT, compose


def main():
    host_disks = []
    for path in ["/workspace", "/opt"]:
        usage = shutil.disk_usage(path)
        host_disks.append({"path": path, "total_bytes": usage.total, "free_bytes": usage.free,
                           "project_exclusive_quota_asserted": False})
    volume = compose("exec", "-T", "postgres", "df", "-Pk", "/var/lib/postgresql/data", capture=True)
    parts = volume.stdout.strip().splitlines()[-1].split()
    total, used, available = [int(v) * 1024 for v in parts[1:4]]
    gpu = {"probe": "nvidia-smi", "tool_available": bool(shutil.which("nvidia-smi")),
           "device_absence_asserted": False, "project_allocation_or_PyTorch_GPU_compatibility_asserted": False}
    if gpu["tool_available"]:
        probe = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
                               capture_output=True, text=True, timeout=15)
        gpu.update(query_success=probe.returncode == 0,
                   observed_devices=probe.stdout.strip().splitlines() if probe.returncode == 0 else [],
                   query_error_type=None if probe.returncode == 0 else "QUERY_FAILED_NO_DEVICE_ABSENCE_INFERENCE")
    services = [json.loads(line) for line in compose("ps", "--format", "json", capture=True).stdout.splitlines()]
    report = {"status": "OBSERVED_PROJECT_QUOTAS_UNCONFIRMED", "observed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "scope": "host_and_own_postgres_volume_capacity_snapshot_not_exclusive_quota_peak_or_acceptance",
              "python": sys.version.split()[0], "logical_cpu_count": os.cpu_count(),
              "host_memory_total_bytes": os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES"),
              "host_disks": host_disks,
              "development_postgres_volume_filesystem": {"mount": parts[-1], "total_bytes": total, "used_bytes": used,
                                                        "available_bytes": available, "used_percent_observed": parts[4],
                                                        "all_project_storage_quota_asserted": False},
              "gpu": gpu, "services": [{"service": s["Service"], "state": s["State"], "health": s.get("Health")} for s in services],
              "services_restarted": False, "database_rows_read_or_changed": False,
              "storage_expanded_or_other_projects_cleaned": False, "actual_team_and_exclusive_quotas": None}
    destination = ROOT / "docs/00-project/validation/resource-readiness-snapshot.json"
    destination.write_bytes((json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode())
    print(json.dumps({"status": report["status"], "volume_available_GiB": round(available / 1024**3, 2),
                      "volume_used_percent": parts[4], "gpu_probe": gpu, "service_count": len(services)}))


if __name__ == "__main__":
    main()
