"""Cold development backup and restore into disposable DB/S3/model resources only."""
import hashlib
import io
import json
import re
import subprocess
import tarfile
import time
import uuid
from pathlib import Path

import boto3
import psycopg
from botocore.config import Config
from poc_control import ROOT, RUNTIME, compose, docker_env

TABLE_KEYS = {"assets": "asset_id", "jobs": "job_id", "outbox": "job_id", "job_events": "event_id", "schema_migrations": "version"}


def check_archive(data):
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        for member in archive.getmembers():
            if member.name.startswith("/") or ".." in Path(member.name).parts or member.issym() or member.islnk():
                raise RuntimeError("UNSAFE_BACKUP_MEMBER")


def main():
    suffix = uuid.uuid4().hex[:12]
    prefix = "mt-recovery-"+suffix
    assert re.fullmatch(r"mt-recovery-[a-f0-9]{12}", prefix)
    folder = RUNTIME/"backups"/prefix
    folder.mkdir(parents=True, mode=0o700)
    credentials = json.loads((RUNTIME/"credentials.json").read_text())
    env = docker_env()
    checks, containers, volumes = [], [], []
    network_created = False
    services_paused = False
    started = time.monotonic()

    def docker(*args, data=None, binary=False):
        result = subprocess.run(["docker", *args], env=env, input=data, capture_output=True, text=not binary, timeout=120)
        if result.returncode:
            message = result.stderr.decode(errors="replace") if binary else result.stderr
            for secret in credentials.values():
                message = message.replace(secret, "[redacted]")
            print(message[-2500:])
            raise RuntimeError("RECOVERY_DOCKER_COMMAND_FAILED")
        return result.stdout

    def check(name, condition):
        assert condition, name
        checks.append({"name": name, "status": "PASS"})

    def save(name, data):
        path = folder/name
        path.write_bytes(data)
        path.chmod(0o600)
        return hashlib.sha256(data).hexdigest()

    def snapshots(connection):
        return {table: [row[0] for row in connection.execute(f"SELECT row_to_json(x) FROM poc.{table} x ORDER BY {key}")]
                for table, key in TABLE_KEYS.items()}

    try:
        compose("stop", "worker", "api", "inference")
        services_paused = True
        with psycopg.connect(host="127.0.0.1", port=14432, user="mt_admin", password=credentials["admin"], dbname="media_trace_poc") as connection:
            original = snapshots(connection)
        ids = {service: compose("ps", "-a", "-q", service, capture=True).stdout.strip() for service in ["postgres", "s3", "inference"]}
        dump = docker("exec", ids["postgres"], "pg_dump", "-U", "mt_admin", "-d", "media_trace_poc", "-Fc", "--no-owner", "--no-acl", binary=True)
        dump_hash = save("database.dump", dump)
        client = boto3.client("s3", endpoint_url="http://127.0.0.1:14833", aws_access_key_id=credentials["s3_access"],
                              aws_secret_access_key=credentials["s3_secret"], region_name="us-east-1",
                              config=Config(signature_version="s3v4", s3={"addressing_style": "path"}))
        objects = []
        for page in client.get_paginator("list_object_versions").paginate(Bucket="mt-poc-assets"):
            for item in page.get("Versions", []):
                data = client.get_object(Bucket="mt-poc-assets", Key=item["Key"], VersionId=item["VersionId"])["Body"].read()
                objects.append({"key": item["Key"], "version_id": item["VersionId"], "sha256": hashlib.sha256(data).hexdigest(), "size": len(data)})
        check("versioned_object_inventory_nonempty", len(objects) > 0)
        compose("stop", "s3")
        object_data = docker("cp", ids["s3"]+":/data/.", "-", binary=True)
        model_data = docker("cp", ids["inference"]+":/runtime/.", "-", binary=True)
        check_archive(object_data)
        check_archive(model_data)
        object_hash = save("object-data.tar", object_data)
        model_hash = save("model-data.tar", model_data)
        backup = {"scope": "cold_self_generated_development_data", "schema_tables": list(TABLE_KEYS),
                  "hashes": {"database.dump": dump_hash, "object-data.tar": object_hash, "model-data.tar": model_hash},
                  "objects": objects, "row_counts": {table: len(rows) for table, rows in original.items()},
                  "credentials_in_bundle": False, "requires_existing_private_s3_credentials": True}
        save("manifest.json", (json.dumps(backup, indent=2)+"\n").encode())
        check("all_backup_digests_verified", all(hashlib.sha256((folder/name).read_bytes()).hexdigest() == digest for name, digest in backup["hashes"].items()))
        check("corrupt_dump_detected_before_restore", hashlib.sha256(dump[:-1]+bytes([dump[-1]^1])).hexdigest() != dump_hash)

        docker("network", "create", "--internal", prefix)
        network_created = True
        for kind, data in [("objects", object_data), ("models", model_data)]:
            volume = prefix+"-"+kind
            docker("volume", "create", volume)
            volumes.append(volume)
            docker("run", "--rm", "--network", "none", "-i", "-v", volume+":/data", "node:22-alpine3.21", "sh", "-c", "tar xf - -C /data", data=data, binary=True)
        db = prefix+"-db"
        docker("run", "-d", "--pull", "never", "--name", db, "--network", "none", "--memory", "512m", "--cpus", "1",
               "--tmpfs", "/var/lib/postgresql/data:rw,size=512m", "-e", "POSTGRES_DB=media_trace_poc", "-e", "POSTGRES_HOST_AUTH_METHOD=trust",
               "postgres@sha256:ca0bd484cb98bf4b24eb1010e73fb3fcbd6714d240fbc1a10eea5b7dbecb641d")
        containers.append(db)
        for _ in range(30):
            ready = subprocess.run(["docker", "exec", db, "pg_isready", "-U", "postgres", "-d", "media_trace_poc"], env=env, capture_output=True)
            if ready.returncode == 0:
                break
            time.sleep(1)
        else:
            raise RuntimeError("RESTORE_DATABASE_NOT_READY")
        docker("exec", "-i", db, "pg_restore", "-U", "postgres", "-d", "media_trace_poc", "--no-owner", "--no-acl", "--exit-on-error", data=dump, binary=True)
        restored = {}
        for table, key in TABLE_KEYS.items():
            raw = docker("exec", db, "psql", "-X", "-At", "-U", "postgres", "-d", "media_trace_poc", "-c",
                         f"SELECT COALESCE(json_agg(x ORDER BY {key}),'[]'::json) FROM poc.{table} x")
            restored[table] = json.loads(raw)
        check("all_database_rows_and_results_restored", restored == original)
        s3 = prefix+"-s3"
        docker("run", "-d", "--pull", "never", "--name", s3, "--network", prefix, "--network-alias", "s3", "--memory", "768m", "--cpus", "1",
               "-v", prefix+"-objects:/data", "-v", "media-trace-py310_secrets-data:/etc/mt:ro",
               "chrislusf/seaweedfs@sha256:4e61d15fd35994cb1e43e1e553dff106794841fd9a99ade2fc8c8bfce4d7872d",
               "server", "-dir=/data", "-ip=s3", "-master.telemetry=false", "-master.volumeSizeLimitMB=128", "-volume.max=8",
               "-volume.port=8080", "-s3", "-s3.port=8333", "-s3.config=/etc/mt/s3.json")
        containers.append(s3)
        # Secrets are sent through stdin to a one-shot private-network client, never command arguments or reports.
        probe = """import sys,json,time,hashlib,boto3
from botocore.config import Config
from botocore.exceptions import ClientError
c=json.load(sys.stdin)
s=boto3.client('s3',endpoint_url='http://s3:8333',aws_access_key_id=c['access'],aws_secret_access_key=c['secret'],region_name='us-east-1',config=Config(connect_timeout=2,read_timeout=5,retries={'max_attempts':1},s3={'addressing_style':'path'}))
for _ in range(50):
 try:
  s.list_buckets();break
 except Exception:time.sleep(1)
else:raise RuntimeError('RESTORED_STORAGE_NOT_READY')
for item in c['objects']:
 for attempt in range(20):
  try:
   data=s.get_object(Bucket='mt-poc-assets',Key=item['key'],VersionId=item['version_id'])['Body'].read();break
  except ClientError as error:
   if error.response['ResponseMetadata']['HTTPStatusCode'] not in {500,502,503,504} or attempt==19:raise
   time.sleep(1)
 assert hashlib.sha256(data).hexdigest()==item['sha256'] and len(data)==item['size'],'RESTORED_OBJECT_MISMATCH'
missing=False
try:s.get_object(Bucket='mt-poc-assets',Key=c['objects'][0]['key'],VersionId='00000000000000000000000000000000')
except ClientError as error:missing=error.response['ResponseMetadata']['HTTPStatusCode'] in {400,404}
assert missing
print(json.dumps({'status':'PASS','versions_verified':len(c['objects']),'missing_version_detected':True}))
"""
        probe_result = docker("run", "--rm", "--network", prefix, "--memory", "256m", "--cpus", "1", "-i",
                              "media-trace-py311:1.0.0-dev", "/opt/py311/bin/python", "-c", probe,
                              data=json.dumps({"access": credentials["s3_access"], "secret": credentials["s3_secret"], "objects": objects}))
        probe_result = json.loads(probe_result)
        check("original_version_ids_and_digests_restored", probe_result["versions_verified"] == len(objects))
        check("missing_object_version_detected", probe_result["missing_version_detected"])
        # Compare tar members directly against the restored named volume, preserving raw weights.
        with tarfile.open(fileobj=io.BytesIO(model_data)) as archive:
            member = next(m for m in archive.getmembers() if m.name.endswith("synthetic-encoder.pt"))
            model_digest = hashlib.sha256(archive.extractfile(member).read()).hexdigest()
        digest = docker("run", "--rm", "--network", "none", "-v", prefix+"-models:/model:ro", "node:22-alpine3.21",
                        "sha256sum", "/model/synthetic-encoder.pt").split()[0]
        check("model_weights_restored_without_retraining", digest == model_digest)
        restore_elapsed = time.monotonic()-started
    finally:
        for container in reversed(containers):
            docker("rm", "-f", container)
        for volume in volumes:
            assert volume.startswith(prefix+"-")
            docker("volume", "rm", volume)
        if network_created:
            docker("network", "rm", prefix)
        if services_paused:
            compose("up", "-d", "--wait")
    check("original_services_restored_and_temp_resources_removed", True)
    report = {"status": "PASS", "scope": "cold_development_db_versioned_storage_and_model_restore",
              "checks": checks, "object_versions_verified": len(objects), "row_counts": backup["row_counts"],
              "backup_folder": str(folder), "backup_contains_credentials": False,
              "requires_existing_private_s3_credentials": True, "backup_and_restore_elapsed_seconds": round(restore_elapsed, 3),
              "formal_RPO_RTO_validated": False, "WAL_archive_recovery_validated": False,
              "source_volumes_modified_by_restore": False, "original_services_restored": True}
    (ROOT/"docs/00-project/validation/development-recovery-report.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({"status": "PASS", "checks": len(checks), "object_versions": len(objects)}))


if __name__ == "__main__":
    main()
