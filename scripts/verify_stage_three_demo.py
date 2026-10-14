"""Actually run the isolated three-service fixture; preserve the existing Docker stack."""

import json
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

import httpx
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]


def port():
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        return server.getsockname()[1]


def main():
    ports = {role: port() for role in ["inference", "backend", "frontend"]}
    while len(set(ports.values())) != 3:
        ports = {role: port() for role in ports}
    token = secrets.token_hex(24)
    env = dict(os.environ, MT_DEMO_INTERNAL_TOKEN=token, PYTHONDONTWRITEBYTECODE="1")
    env["MT_DEMO_INFERENCE_URL"] = "http://127.0.0.1:" + str(ports["inference"])
    env["MT_DEMO_BACKEND_URL"] = "http://127.0.0.1:" + str(ports["backend"])
    env["MT_DEMO_FRONTEND_URL"] = "http://127.0.0.1:" + str(ports["frontend"])
    processes, checks, logs = [], [], {}
    temporary = tempfile.TemporaryDirectory(prefix="media-trace-demo-")
    streams = []
    try:
        for role, number in ports.items():
            logs[role] = Path(temporary.name) / (role + ".jsonl")
            stream = logs[role].open("wb")
            streams.append(stream)
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "tools.stage_three_demo.app:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(number),
                    "--no-access-log",
                    "--log-level",
                    "error",
                ],
                cwd=ROOT,
                env=dict(env, MT_DEMO_ROLE=role),
                stdout=stream,
                stderr=subprocess.DEVNULL,
            )
            processes.append(process)
            url = "http://127.0.0.1:" + str(number)
            for _ in range(100):
                if process.poll() is not None:
                    raise RuntimeError("DEMO_SERVICE_EXITED")
                try:
                    if httpx.get(url + "/api/v1/ready", timeout=1).status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                time.sleep(0.1)
            else:
                raise RuntimeError("DEMO_SERVICE_START_TIMEOUT")
            checks.append({"name": role + "_independent_health_and_ready", "status": "PASS"})
        back = env["MT_DEMO_BACKEND_URL"]
        denied = httpx.post(back + "/api/v1/mock", json={"nonce": str(uuid.uuid4())})
        assert denied.status_code == 401 and denied.json()["code"] == "AUTH_REQUIRED"
        assert denied.headers["x-request-id"] == denied.json()["request_id"]
        checks.append({"name": "missing_bearer_safe_problem_and_trace", "status": "PASS"})
        invalid = httpx.post(
            back + "/api/v1/mock",
            headers={"Authorization": "Bearer " + token},
            json={"nonce": str(uuid.uuid4()), "case_id": str(uuid.uuid4())},
        )
        assert invalid.status_code == 422
        checks.append({"name": "business_fields_rejected_by_fixture", "status": "PASS"})
        nonce = str(uuid.uuid4())
        response = httpx.post(
            back + "/api/v1/mock", headers={"Authorization": "Bearer " + token}, json={"nonce": nonce}
        )
        assert response.status_code == 200
        schema = json.loads((ROOT / "schemas/development/mock-connectivity.response.schema.json").read_text())
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(response.json())
        assert response.json()["nonce"] == nonce and token not in response.text
        assert response.json()["request_id"] == response.headers["x-request-id"]
        checks.append({"name": "backend_calls_inference_schema_and_explicit_mock", "status": "PASS"})
        trace = str(uuid.uuid4())
        front = httpx.post(env["MT_DEMO_FRONTEND_URL"] + "/demo/check", headers={"X-Request-ID": trace}, timeout=10)
        assert front.status_code == 200 and front.json()["mock"] is True
        assert front.json()["request_id"] == trace
        checks.append({"name": "frontend_proxy_backend_inference_actual_HTTP", "status": "PASS"})
        browser_env = dict(env)
        browser_env["PATH"] = (
            os.environ.get("MT_NODE_BIN", "/home/glwy/.cache/media-trace-node/node-v22.21.1-linux-x64/bin")
            + os.pathsep
            + env.get("PATH", "")
        )
        browser_env.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/home/glwy/.cache/media-trace-browsers")
        subprocess.run(
            [
                "npm",
                "--prefix",
                "frontend",
                "exec",
                "--",
                "playwright",
                "test",
                "--config=frontend/stage-three-playwright.config.ts",
            ],
            cwd=ROOT,
            env=browser_env,
            check=True,
            timeout=120,
        )
        checks.append({"name": "actual_Vue_browser_health_page", "status": "PASS"})
        processes[0].terminate()
        processes[0].wait(timeout=10)
        unavailable = httpx.get(back + "/api/v1/ready", timeout=5)
        failed = httpx.post(
            back + "/api/v1/mock",
            headers={"Authorization": "Bearer " + token},
            json={"nonce": nonce},
            timeout=5,
        )
        assert unavailable.status_code == 503 and unavailable.json()["code"] == "DEMO_DEPENDENCY_NOT_READY"
        assert failed.status_code == 502 and failed.json()["code"] == "DEMO_INFERENCE_UNAVAILABLE"
        assert token not in unavailable.text + failed.text and nonce not in failed.text
        checks.append({"name": "stopped_mock_dependency_ready_503_and_call_502_no_input_echo", "status": "PASS"})
    finally:
        for process in reversed(processes):
            if process.poll() is None:
                process.terminate()
        for process in processes:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        for stream in streams:
            stream.close()
        if sys.exc_info()[0] is not None:
            temporary.cleanup()
    try:
        records = {role: [json.loads(line) for line in path.read_text().splitlines()] for role, path in logs.items()}
        for role, rows in records.items():
            assert rows and all(row["role"] == role and row["development_fixture"] for row in rows)
            assert all(row["business_result"] is False for row in rows)
            assert any(row["request_id"] == trace and row["status"] == 200 for row in rows)
            assert token not in logs[role].read_text() and nonce not in logs[role].read_text()
            assert all(
                set(row)
                == {
                    "event",
                    "role",
                    "method",
                    "route",
                    "status",
                    "request_id",
                    "elapsed_ms",
                    "development_fixture",
                    "business_result",
                }
                for row in rows
            )
        checks.append({"name": "three_service_structured_trace_logs_exclude_headers_body_and_token", "status": "PASS"})
    finally:
        temporary.cleanup()
    checks.append({"name": "own_three_processes_stopped_existing_stack_untouched", "status": "PASS"})
    report = {
        "status": "PASS",
        "scope": "isolated_Vue_FastAPI_mock_three_process_fixture_not_business_or_real_model_acceptance",
        "checks": checks,
        "model_weights_or_GPU_loaded": False,
        "database_or_object_store_accessed": False,
        "existing_Docker_stack_changed": False,
        "private_values_printed": False,
        "structured_log_counts": {role: len(rows) for role, rows in records.items()},
        "correlated_trace": {
            role: [row for row in rows if row["request_id"] == trace] for role, rows in records.items()
        },
    }
    (ROOT / "docs/00-project/validation/stage-three-demo-report.json").write_bytes(
        (json.dumps(report, indent=2) + "\n").encode()
    )
    print(json.dumps({"status": "PASS", "checks": len(checks), "mock": True, "business_acceptance": False}))


if __name__ == "__main__":
    main()
