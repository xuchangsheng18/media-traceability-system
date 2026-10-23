"""Check self-owned request markers against actual isolated CI HTTP service logs."""

import json
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scripts.poc_control import compose
else:
    from poc_control import compose

ROOT = Path(__file__).resolve().parents[1]


def main():
    marker = "self-owned-log-privacy-" + uuid.uuid4().hex
    checks = []
    for service, port in [("api", 14200), ("inference", 14201), ("web", 14180)]:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/poc/{marker}?token={marker}", timeout=15)
        except urllib.error.HTTPError as error:
            response = json.loads(error.read())
            assert error.code == 404 and response["code"] == "RESOURCE_NOT_FOUND"
            assert marker not in json.dumps(response)
        else:
            raise RuntimeError("UNKNOWN_ROUTE_NOT_REJECTED")
        checks.append({"name": service + "_unknown_request_safe_response", "status": "PASS"})
    logs = compose("logs", "--no-color", "api", "inference", "web", capture=True)
    assert marker not in logs.stdout and marker not in logs.stderr, "RAW_REQUEST_TARGET_IN_HTTP_LOG"
    checks.append({"name": "raw_target_absent_from_actual_service_logs", "status": "PASS"})
    report = {
        "status": "PASS",
        "checks": checks,
        "scope": "isolated_development_actual_http_logs",
        "shared_server_services_changed": False,
        "full_DLP_or_production_acceptance": False,
    }
    (ROOT / "docs/00-project/validation/http-log-privacy-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": "PASS", "checks": len(checks)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
