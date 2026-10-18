"""Development stack lifecycle. Credentials stay in an external private runtime directory."""
import argparse
import hashlib
import json
import os
import secrets
import subprocess
import time
from pathlib import Path
from typing import TYPE_CHECKING

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = Path(os.environ.get("MT_RUNTIME_DIR", "/workspace/glwy/runtime/media-traceability-system"))
PY310 = Path("/opt/conda/glwy/envs/py310/bin/python")


def docker_env():
    context = os.environ.get("MT_DOCKER_CONTEXT", "desktop-linux")
    inspected = subprocess.run(["docker", "context", "inspect", context, "--format", "{{.Endpoints.docker.Host}}"],
                               text=True, capture_output=True)
    if inspected.returncode:
        context = subprocess.run(["docker", "context", "show"], text=True, capture_output=True, check=True).stdout.strip()
        inspected = subprocess.run(["docker", "context", "inspect", context, "--format", "{{.Endpoints.docker.Host}}"],
                                   text=True, capture_output=True, check=True)
    endpoint = os.environ.get("DOCKER_HOST") or inspected.stdout.strip()
    client = Path.home()/".cache/media-trace-docker-client"
    client.mkdir(parents=True, exist_ok=True, mode=0o700)
    config = client/"config.json"
    if not config.exists():
        config.write_text('{"auths":{}}\n')
    config.chmod(0o600)
    return dict(os.environ, DOCKER_HOST=endpoint, DOCKER_CONFIG=str(client), MT_RUNTIME_DIR=str(RUNTIME))


def compose(*args, capture=False):
    return subprocess.run(["docker", "compose", "-f", str(ROOT/"deploy/docker-compose.yml"), *args],
                          env=docker_env(), cwd=ROOT, text=True, capture_output=capture, check=True)


def prepare():
    RUNTIME.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = RUNTIME/"credentials.json"
    if not path.exists():
        path.write_text(json.dumps({k: secrets.token_hex(24) for k in ["admin", "app", "rabbit", "s3_access", "s3_secret", "api_token", "internal_token"]}))
        path.chmod(0o600)
    c = json.loads(path.read_text())
    files = {
        "postgres.env": f"POSTGRES_USER=mt_admin\nPOSTGRES_PASSWORD={c['admin']}\nPOSTGRES_DB=media_trace_poc\n",
        "rabbitmq.env": f"RABBITMQ_DEFAULT_USER=mt_poc\nRABBITMQ_DEFAULT_PASS={c['rabbit']}\nRABBITMQ_DEFAULT_VHOST=media-trace-poc\n",
        "poc.env": f"DATABASE_URL=postgresql+psycopg://poc_app:{c['app']}@postgres:5432/media_trace_poc\nBROKER_URL=amqp://mt_poc:{c['rabbit']}@rabbitmq:5672/media-trace-poc\nS3_ENDPOINT=http://s3:8333\nS3_ACCESS_KEY={c['s3_access']}\nS3_SECRET_KEY={c['s3_secret']}\nPOC_API_TOKEN={c['api_token']}\nINTERNAL_TOKEN={c['internal_token']}\nINFERENCE_URL=http://inference:8001\n",
        "s3.json": json.dumps({"identities": [{"name": "mt_poc", "credentials": [{"accessKey": c["s3_access"], "secretKey": c["s3_secret"]}], "actions": ["Admin", "Read", "Write", "List", "Tagging"]}]}),
    }
    for name, contents in files.items():
        p = RUNTIME/name
        p.write_text(contents)
        p.chmod(0o600 if name != "s3.json" else 0o644)
    # Only the serving account can traverse the private host runtime directory.
    return c


def initialize(c):
    import boto3
    import psycopg
    from botocore.config import Config
    from psycopg import sql
    with psycopg.connect(host="127.0.0.1", port=14432, user="mt_admin", password=c["admin"], dbname="media_trace_poc") as conn:
        import sys
        sys.path.insert(0,str(ROOT/"backend"))
        from app.migrations import configure_application_grants, run_migrations
        run_migrations(conn)
        if not conn.execute("SELECT 1 FROM pg_roles WHERE rolname='poc_app'").fetchone():
            conn.execute(sql.SQL("CREATE ROLE poc_app LOGIN PASSWORD {} NOSUPERUSER NOBYPASSRLS").format(sql.Literal(c["app"])))
        configure_application_grants(conn)
    s3 = boto3.client("s3", endpoint_url="http://127.0.0.1:14833", aws_access_key_id=c["s3_access"],
                     aws_secret_access_key=c["s3_secret"], region_name="us-east-1",
                     config=Config(signature_version="s3v4", s3={"addressing_style": "path"}))
    for _ in range(40):
        try:
            s3.list_buckets()
            break
        except Exception:
            time.sleep(1)
    else:
        raise RuntimeError("S3_NOT_READY")
    if "mt-poc-assets" not in {x["Name"] for x in s3.list_buckets().get("Buckets", [])}:
        s3.create_bucket(Bucket="mt-poc-assets")
    s3.put_bucket_versioning(Bucket="mt-poc-assets", VersioningConfiguration={"Status": "Enabled"})
    if s3.get_bucket_versioning(Bucket="mt-poc-assets").get("Status") != "Enabled":
        raise RuntimeError("VERSIONING_NOT_ENABLED")


def prepare_secret_volume():
    env = docker_env()
    volume = "media-trace-py310_secrets-data"
    subprocess.run(["docker", "volume", "create", "--label", "com.docker.compose.project=media-trace-py310",
                    "--label", "com.docker.compose.volume=secrets-data", volume], env=env, check=True, capture_output=True)
    name = "mt-poc-secret-init"
    subprocess.run(["docker", "run", "--rm", "--network", "none", "-i", "--name", name, "-v", volume+":/etc/mt",
                    "node:22-alpine3.21", "sh", "-c", "umask 022; cat > /etc/mt/s3.json"],
                   input=(RUNTIME/"s3.json").read_text(), text=True, env=env, check=True, capture_output=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["prepare", "pack", "build", "up", "down", "status", "token"])
    args = parser.parse_args()
    c = prepare()
    if args.action == "prepare":
        print("Private runtime configuration ready; credentials not printed")
    elif args.action == "pack":
        if TYPE_CHECKING:
            from scripts.verify_runtime_lock import main as verify_lock
        else:
            from verify_runtime_lock import main as verify_lock
        lock_report = verify_lock()
        target = ROOT/"deploy/build/py310.tar.gz"
        target.parent.mkdir(exist_ok=True)
        manifest_path = ROOT/"config/locks/runtime-archive.json"
        manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
        if (target.exists() and manifest.get("requirements_lock_sha256") == lock_report["lock_sha256"]
                and hashlib.sha256(target.read_bytes()).hexdigest() == manifest.get("archive_sha256")):
            print("Verified existing packed py310 runtime")
        else:
            subprocess.run([str(PY310.parent/"conda-pack"), "-p", str(PY310.parent.parent), "-o", str(target), "--force", "--ignore-editable-packages"], check=True)
            manifest = {"profile": "miniforge-py310-linux-x86_64-cpu", "python": lock_report["python"],
                        "source_environment": str(PY310.parent.parent), "requirements_lock_sha256": lock_report["lock_sha256"],
                        "archive_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                        "archive_repository_path": "deploy/build/py310.tar.gz", "archive_committed": False}
            manifest_path.write_text(json.dumps(manifest, indent=2)+"\n")
    elif args.action == "build":
        compose("config", "--quiet")
        compose("build", "api", "web")
    elif args.action == "up":
        prepare_secret_volume()
        compose("up", "-d", "--wait", "postgres", "rabbitmq", "s3")
        initialize(c)
        compose("up", "-d", "--wait")
    elif args.action == "down":
        compose("down")  # Never removes named data volumes.
    elif args.action == "status":
        compose("ps")
    elif args.action == "token":
        print(c["api_token"])  # Explicit local operator action; never called by CI.


if __name__ == "__main__":
    main()
