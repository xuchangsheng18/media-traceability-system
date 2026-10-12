"""Collect selected non-secret host/runtime facts and development resource limits."""
import datetime
import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from poc_control import ROOT, compose, docker_env


def main():
    env = docker_env()

    def docker(*args):
        return subprocess.run(["docker", *args], env=env, text=True, capture_output=True, check=True).stdout

    info = json.loads(docker("info", "--format", "{{json .}}"))
    disks = {path: dict(zip(["total_bytes", "used_bytes", "free_bytes"], shutil.disk_usage(path))) for path in ["/workspace", "/opt"]}
    memory = {k: int(v.strip().split()[0])*1024 for k, v in (line.split(":", 1) for line in Path("/proc/meminfo").read_text().splitlines()) if k in {"MemTotal", "MemAvailable"}}
    ids = compose("ps", "-q", capture=True).stdout.split()
    services, images = [], []
    for identifier in ids:
        inspected = json.loads(docker("inspect", identifier))[0]
        service = inspected["Config"]["Labels"]["com.docker.compose.service"]
        host = inspected["HostConfig"]
        services.append({"service": service, "state": inspected["State"]["Status"],
                         "health": inspected["State"].get("Health", {}).get("Status", "not_configured"),
                         "image_id": inspected["Image"], "memory_limit_bytes": host["Memory"],
                         "cpu_limit": host["NanoCpus"]/1e9, "pids_limit": host["PidsLimit"],
                         "ports": inspected["NetworkSettings"]["Ports"]})
    image_names = ["media-trace-py310:1.0.0-dev", "media-trace-web:1.0.0-dev", "postgres:16", "rabbitmq:4.3.6-management", "chrislusf/seaweedfs:4.48", "node:22-alpine3.21", "nginx:1.31.4-alpine", "python:3.12-slim-bookworm"]
    for name in image_names:
        inspected = json.loads(docker("image", "inspect", name))[0]
        images.append({"name": name, "image_id": inspected["Id"], "repo_digests": inspected["RepoDigests"],
                       "platform": inspected["Os"]+"/"+inspected["Architecture"], "size_bytes": inspected["Size"]})
    archive = ROOT/"deploy/build/py310.tar.gz"
    report = {"observed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "host": "172.16.58.179", "user": "glwy", "os_release": Path("/etc/os-release").read_text(),
              "kernel": platform.release(), "cpu_logical": os.cpu_count(),
              "lscpu": json.loads(subprocess.run(["lscpu", "--json"], text=True, capture_output=True, check=True).stdout),
              "memory": memory, "host_disks": disks,
              "gpu_validation": "not_validated", "nvidia_smi_available": shutil.which("nvidia-smi") is not None,
              "python": sys.version, "python_executable": sys.executable,
              "miniforge_base": "/opt/apps/miniforge3", "conda_environment": "/opt/conda/glwy/envs/py310",
              "python_packages": {d.metadata["Name"]: d.version for d in importlib.metadata.distributions()},
              "docker_context": "desktop-linux", "docker": {k: info[k] for k in ["ServerVersion", "OperatingSystem", "NCPU", "MemTotal", "DockerRootDir"]},
              "daemon_disk_df": docker("run", "--rm", "--network", "none", "node:22-alpine3.21", "df", "-Pk", "/"),
              "development_services": services,
              "resource_snapshot": [json.loads(line) for line in docker("stats", "--no-stream", "--format", "{{json .}}", *ids).splitlines()],
              "resource_snapshot_is_peak": False,
              "runtime_archive_sha256": hashlib.file_digest(archive.open("rb"), "sha256").hexdigest() if hasattr(hashlib, "file_digest") else hashlib.sha256(archive.read_bytes()).hexdigest(),
              "production_resource_allocation_confirmed": False}
    destination = ROOT/"docs/00-project/validation"
    (destination/"environment-inventory.json").write_text(json.dumps(report, indent=2)+"\n")
    (ROOT/"config/locks/docker-images.json").write_text(json.dumps({"images": images}, indent=2)+"\n")
    experiment = docker("compose", "-f", str(ROOT/"deploy/docker-compose.yml"), "exec", "-T", "inference", "cat", "/runtime/experiment.json")
    (destination/"synthetic-training-experiment.json").write_text(experiment)
    print(json.dumps({"status": "RECORDED", "services": len(services), "python": platform.python_version()}))


if __name__ == "__main__":
    main()
