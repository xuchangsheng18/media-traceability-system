"""Real loopback API/queue/storage/inference checks using generated development credentials."""
import base64
import hashlib
import io
import json
import os
import re
import time
import uuid
from html.parser import HTMLParser
from pathlib import Path

import httpx
import psycopg
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = Path(os.environ.get("MT_RUNTIME_DIR", "/workspace/glwy/runtime/media-traceability-system"))


class FrontendPage(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title: list[str] = []
        self.in_title = False
        self.has_app = False
        self.scripts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        source = values.get("src")
        if tag == "title":
            self.in_title = True
        elif tag == "div" and values.get("id") == "app":
            self.has_app = True
        elif tag == "script" and values.get("type") == "module" and source:
            self.scripts.append(source)

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title.append(data)


def frontend_served(client: httpx.Client, base: str) -> bool:
    response = client.get(base)
    if response.status_code != 200 or response.headers.get("content-type", "").split(";", 1)[0] != "text/html":
        return False
    page = FrontendPage()
    page.feed(response.text)
    if "短视频与图片智能识别溯源系统" not in "".join(page.title) or not page.has_app or not page.scripts:
        return False
    for source in page.scripts:
        if re.fullmatch(r"/assets/[A-Za-z0-9_.-]+\.js", source) is None:
            return False
        script = client.get(base.rstrip("/") + source)
        if (
            script.status_code != 200
            or script.headers.get("content-type", "").split(";", 1)[0] not in {"text/javascript", "application/javascript"}
            or not script.content.strip()
        ):
            return False
    return True


def main():
    c = json.loads((RUNTIME/"credentials.json").read_text())
    base = "http://127.0.0.1:14180"
    headers = {"Authorization": "Bearer "+c["api_token"]}
    checks = []
    with httpx.Client(timeout=30) as client:
        def check(name, condition):
            assert condition, name
            checks.append({"name": name, "status": "PASS"})
        check("frontend_served", frontend_served(client, base))
        check("unauthorized_health_denied", client.get(base+"/api/v1/health").status_code == 401)
        health = client.get(base+"/api/v1/health", headers=headers)
        check("database_connected", health.status_code == 200 and health.json()["status"] == "ok")
        image = io.BytesIO()
        Image.new("RGB", (64, 64), (60, 110, 180)).save(image, "PNG")
        raw = image.getvalue()
        bad = client.post(base+"/poc/assets", headers=headers, json={"filename": "bad.png", "image_base64": base64.b64encode(b"bad").decode()})
        check("bad_media_rejected", bad.status_code == 422)
        uploaded = client.post(base+"/poc/assets", headers=headers, json={"filename": "synthetic-ci.png", "image_base64": base64.b64encode(raw).decode()})
        check("S3_versioned_upload", uploaded.status_code == 201 and bool(uploaded.json()["object_ref"]["version_id"]))
        check("original_digest_preserved", uploaded.json()["object_ref"]["sha256"] == hashlib.sha256(raw).hexdigest())
        asset = uploaded.json()["asset_id"]
        key = "ci-"+str(uuid.uuid4())
        h = dict(headers, **{"Idempotency-Key": key})
        body = {"asset_id": asset}
        created = client.post(base+"/poc/jobs", headers=h, json=body)
        check("queue_submission", created.status_code == 202)
        job = created.json()["job_id"]
        repeated = client.post(base+"/poc/jobs", headers=h, json=body)
        check("idempotent_submit", repeated.status_code == 202 and repeated.json()["job_id"] == job)
        unknown = client.get(base+"/poc/jobs/"+str(uuid.uuid4()), headers=headers)
        check("unknown_job_hidden", unknown.status_code == 404)
        for _ in range(60):
            status = client.get(base+"/poc/jobs/"+job, headers=headers).json()
            if status["state"] in {"FAILED", "SUCCEEDED"}:
                break
            time.sleep(1)
        check("worker_completed", status["state"] == "SUCCEEDED")
        result = status["result"]
        check("real_cpu_inference", result["mock"] is False and result["payload"]["dimension"] == 8)
        check("model_and_mapping_versions", result["model_name"] == "synthetic-cpu-encoder" and result["mapping_version"] == "poc-analysis-copy-1")
        check("result_object_version", bool(result["payload"]["vector_ref"]["version_id"]))
        check("task_and_inference_trace_match", created.json()["task_request_id"] == status["request_id"] == result["request_id"])
        check("run_version_matches_claim", status["run_version"] == result["run_version"] and status["run_version"] == status["attempts"])
        terminal = client.post(base+"/poc/jobs", headers=h, json=body)
        check("idempotent_response_preserves_terminal_state", terminal.json()["state"] == "SUCCEEDED")
        with psycopg.connect(host="127.0.0.1", port=14432, user="poc_app", password=c["app"], dbname="media_trace_poc") as connection:
            rows = connection.execute("SELECT event_type,request_id FROM poc.job_events WHERE job_id=%s", (job,)).fetchall()
            check("append_only_events_keep_trace", {row[0] for row in rows} >= {"job.created", "job.claimed", "job.succeeded"}
                  and {str(row[1]) for row in rows} == {status["request_id"]})
        internal = client.post("http://127.0.0.1:14201/internal/v1/inference/retrieval.image_embedding", json={})
        check("internal_error_uses_safe_problem", internal.status_code == 401 and internal.json()["code"] == "AUTH_REQUIRED"
              and internal.json()["request_id"] == internal.headers["x-request-id"])
        invalid_internal = client.post("http://127.0.0.1:14201/internal/v1/inference/retrieval.image_embedding", json={},
                                       headers={"Authorization": "Bearer "+c["internal_token"]})
        check("internal_contract_error_uses_problem", invalid_internal.status_code == 422 and invalid_internal.json()["code"] == "MODEL_CONTRACT_INVALID")
        inference = client.get("http://127.0.0.1:14201/healthz").json()
        check("container_python310", inference["python"].startswith("3.10."))
        check("CPU_profile", inference["device"] == "cpu" and inference["business_model"] is False)
        # Capture a durable task ID for a separate restart/persistence check, no secrets.
        report = {"status": "PASS", "scope": "real_cpu_development_vertical_slice", "checks": checks,
                  "job_id": job, "asset_id": asset, "model": inference, "business_model_validated": False}
        (ROOT/"docs/00-project/validation/poc-integration-report.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({"status": "PASS", "checks": len(checks), "job_id": job}))


if __name__ == "__main__":
    main()
