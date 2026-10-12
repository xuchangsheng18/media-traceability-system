"""Scoped failure injection against this development stack only, then restore services."""
import base64
import io
import json
import time
import uuid

import boto3
import httpx
import psycopg
from PIL import Image
from poc_control import ROOT, RUNTIME, compose


def main():
    credentials = json.loads((RUNTIME/"credentials.json").read_text())
    headers = {"Authorization": "Bearer "+credentials["api_token"]}
    base = "http://127.0.0.1:14180"
    checks = []
    prior = json.loads((ROOT/"docs/00-project/validation/poc-integration-report.json").read_text())
    with httpx.Client(timeout=40) as client:
        def check(name, value):
            assert value, name
            checks.append({"name": name, "status": "PASS"})
        try:
            compose("stop", "worker", "rabbitmq")
            submitted = client.post(base+"/poc/jobs", headers=dict(headers, **{"Idempotency-Key": "fault-"+str(uuid.uuid4())}),
                                    json={"asset_id": prior["asset_id"]})
            check("broker_outage_task_persisted", submitted.status_code == 202)
            job = submitted.json()["job_id"]
            # Explicitly simulate a worker crash after claim; observe lease-based recovery.
            with psycopg.connect(host="127.0.0.1", port=14432, user="poc_app", password=credentials["app"], dbname="media_trace_poc") as conn:
                conn.execute("UPDATE poc.jobs SET state='RUNNING',attempts=1,lease_until=now()-interval '1 second' WHERE job_id=%s", (job,))
            compose("start", "rabbitmq")
            compose("up", "-d", "--wait", "rabbitmq")
            compose("start", "worker")
            for _ in range(70):
                status = client.get(base+"/poc/jobs/"+job, headers=headers).json()
                if status["state"] in {"SUCCEEDED", "FAILED"}:
                    break
                time.sleep(1)
            check("outbox_and_expired_lease_recovered", status["state"] == "SUCCEEDED" and status["attempts"] >= 2)
            compose("restart", "api", "inference", "s3")
            for _ in range(40):
                try:
                    if client.get(base+"/poc/jobs/"+prior["job_id"], headers=headers).status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                time.sleep(1)
            durable = client.get(base+"/poc/jobs/"+prior["job_id"], headers=headers).json()
            check("task_and_result_survive_restart", durable["state"] == "SUCCEEDED" and durable["result"]["payload"]["dimension"] == 8)
            # Database/API readiness does not imply storage readiness after restart.
            s3 = boto3.client("s3", endpoint_url="http://127.0.0.1:14833", region_name="us-east-1",
                              aws_access_key_id=credentials["s3_access"], aws_secret_access_key=credentials["s3_secret"])
            for _ in range(40):
                try:
                    s3.list_buckets()
                    break
                except Exception:
                    time.sleep(1)
            else:
                raise RuntimeError("S3_RESTART_NOT_READY")
            ref = durable["result"]["payload"]["vector_ref"]
            stored = s3.get_object(Bucket="mt-poc-assets", Key="vectors/"+ref["object_id"], VersionId=ref["version_id"])["Body"].read()
            check("versioned_vector_survives_storage_restart", len(stored) == 8*4)
            image = io.BytesIO()
            Image.new("RGB", (32, 32), "red").save(image, "PNG")
            another = client.post(base+"/poc/assets", headers=headers, json={"filename": "synthetic-conflict.png", "image_base64": base64.b64encode(image.getvalue()).decode()}).json()
            key = "conflict-"+str(uuid.uuid4())
            h = dict(headers, **{"Idempotency-Key": key})
            first = client.post(base+"/poc/jobs", headers=h, json={"asset_id": prior["asset_id"]})
            second = client.post(base+"/poc/jobs", headers=h, json={"asset_id": another["asset_id"]})
            check("same_key_different_asset_rejected", first.status_code == 202 and second.status_code == 409)
        finally:
            compose("up", "-d", "--wait")
    report = {"status": "PASS", "scope": "development_stack_failure_injection", "checks": checks,
              "worker_claim_failure_simulated": True, "services_restored": True}
    (ROOT/"docs/00-project/validation/poc-resilience-report.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({"status": "PASS", "checks": len(checks)}))


if __name__ == "__main__":
    main()
