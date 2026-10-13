"""Actually run the isolated three-service fixture; preserve the existing Docker stack."""

import json
import os
import secrets
import socket
import subprocess
import sys
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
    processes, checks = [], []
    try:
        for role, number in ports.items():
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
                stdout=subprocess.DEVNULL,
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
        front = httpx.post(env["MT_DEMO_FRONTEND_URL"] + "/demo/check", timeout=10)
        assert front.status_code == 200 and front.json()["mock"] is True
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
    finally:
        for process in reversed(processes):
            process.terminate()
        for process in processes:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
    checks.append({"name": "own_three_processes_stopped_existing_stack_untouched", "status": "PASS"})
    report = {
        "status": "PASS",
        "scope": "isolated_Vue_FastAPI_mock_three_process_fixture_not_business_or_real_model_acceptance",
        "checks": checks,
        "model_weights_or_GPU_loaded": False,
        "database_or_object_store_accessed": False,
        "existing_Docker_stack_changed": False,
        "private_values_printed": False,
    }
    (ROOT / "docs/00-project/validation/stage-three-demo-report.json").write_bytes(
        (json.dumps(report, indent=2) + "\n").encode()
    )
    print(json.dumps({"status": "PASS", "checks": len(checks), "mock": True, "business_acceptance": False}))


if __name__ == "__main__":
    main()
