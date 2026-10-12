"""Prove that an intentional failing gate stops the actual runner before build/deploy."""
import json
import subprocess

from poc_control import PY310, ROOT


def main():
    process = subprocess.run([str(PY310), "scripts/run_ci.py", "all", "--failure-probe"], cwd=ROOT)
    result = json.loads((ROOT/"docs/00-project/validation/ci-failure-probe-report.json").read_text())
    assert process.returncode != 0
    assert result["status"] == "FAIL" and len(result["checks"]) == 2
    assert all(c["stage"] == "validate" for c in result["checks"])
    result = {"status": "PASS", "scope": "expected_failure_stops_actual_ci_runner", "probe_exit_code": process.returncode,
              "build_or_deployment_executed": False, "evidence": "ci-failure-probe-report.json"}
    (ROOT/"docs/00-project/validation/ci-failure-gate-report.json").write_text(json.dumps(result, indent=2)+"\n")


if __name__ == "__main__":
    main()
