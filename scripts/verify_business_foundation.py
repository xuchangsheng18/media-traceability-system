"""Run the selected business checks against explicit isolated test targets only."""

import argparse
import datetime
import json
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from psycopg.conninfo import conninfo_to_dict

ROOT = Path(__file__).resolve().parents[1]


def validate_target(env: dict[str, str]) -> None:
    dsn = env.get("MT_BUSINESS_TEST_ADMIN_DSN")
    if not dsn or not env.get("MT_BUSINESS_TEST_BROKER_URL"):
        raise RuntimeError("EXPLICIT_ISOLATED_BUSINESS_TEST_TARGETS_REQUIRED")
    values = conninfo_to_dict(dsn)
    if values.get("dbname") == "media_trace_poc" or values.get("user") == "media_trace_poc":
        raise RuntimeError("POC_TARGET_FORBIDDEN")
    if values.get("host") not in {"127.0.0.1", "localhost", "::1"} or not values.get("port"):
        raise RuntimeError("EXPLICIT_LOOPBACK_TEST_INSTANCE_REQUIRED")


def test_totals(path: Path) -> dict[str, int]:
    if not path.is_file():
        return {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
    return {key: sum(int(s.get(key, "0")) for s in suites) for key in ["tests", "failures", "errors", "skipped"]}


def run_checks(root: Path, env: dict[str, str], junit: Path) -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/business", "-q", "--tb=short", "--junitxml", str(junit)],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=600,
    )
    totals = test_totals(junit)
    success = (
        result.returncode == 0 and totals["tests"] > 0 and not any(totals[k] for k in ["failures", "errors", "skipped"])
    )
    # Raw tracebacks can include isolated credentials. Publish counts and safe identifiers only.
    return {
        "status": "PASS" if success else "FAIL",
        "exit_code": 0 if success else result.returncode or 1,
        "test_count": totals["tests"],
        "totals": totals,
        "raw_logs_published": False,
    }


def configured_environment() -> dict[str, str]:
    env = dict(os.environ, PYTHONPATH=os.pathsep.join([str(ROOT / "backend"), str(ROOT)]))
    runtime = Path(env.get("MT_RUNTIME_DIR", "/workspace/glwy/runtime/media-traceability-system"))
    for key, file, value in [
        ("MT_BUSINESS_TEST_ADMIN_DSN", "business-test-postgres-private.json", "admin_dsn"),
        ("MT_BUSINESS_TEST_BROKER_URL", "business-test-broker-private.json", "url"),
    ]:
        if not env.get(key) and (runtime / file).is_file():
            env[key] = json.loads((runtime / file).read_text())[value]
    return env


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["run", "failure-probe"], nargs="?", default="run")
    args = parser.parse_args()
    env = configured_environment()
    report: dict[str, Any] = {
        "scope": "isolated_development_upload_history_controls_adapters_execution_inference_boundaries",
        "formal_accepted": False,
        "all_13_gaps_closed": False,
        "observed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    try:
        validate_target(env)
        with tempfile.TemporaryDirectory(prefix="media-trace-business-verification-") as temp:
            if args.action == "failure-probe":
                path = Path(temp) / "test_controlled_failure.py"
                path.write_text("def test_controlled_failure():\n    assert 1 == 2\n")
                junit = Path(temp) / "failure.xml"
                result = subprocess.run(
                    [sys.executable, "-m", "pytest", str(path), "-q", "--junitxml", str(junit)],
                    cwd=ROOT,
                    env=env,
                    capture_output=True,
                    timeout=60,
                )
                totals = test_totals(junit)
                expected = result.returncode == 1 and totals == {"tests": 1, "failures": 1, "errors": 0, "skipped": 0}
                print(json.dumps({"expected_assertion_failure_verified": expected, "exit_code": result.returncode}))
                return 1 if expected else 2
            report.update(run_checks(ROOT, env, Path(temp) / "business.xml"))
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError):
        report.update(status="BLOCKED_OR_FAIL", exit_code=2, test_count=0)
    report["source_commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    from stage_three_types import source_tree_state

    report.update(source_tree_state(ROOT))
    report["workflow_run_id"] = os.environ.get("GITHUB_RUN_ID")
    (ROOT / "docs/00-project/validation/business-foundation-report.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps({"status": report["status"], "test_count": report["test_count"], "scope": report["scope"]}))
    return int(report["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
