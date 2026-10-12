"""Portable CI gates invoked locally and by the isolated GitHub-hosted workflow."""
import argparse
import datetime
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = "/opt/conda/glwy/envs/py310/bin/python"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["validate", "build", "integration", "all"])
    parser.add_argument("--failure-probe", action="store_true", help="Insert an intentional failed gate; never build or deploy")
    args = parser.parse_args()
    env = dict(os.environ, PYTHONPATH=str(ROOT/"backend"), PYTHONDONTWRITEBYTECODE="1")
    env["PATH"] = os.environ.get("MT_NODE_BIN", "/home/glwy/.cache/media-trace-node/node-v22.21.1-linux-x64/bin")+":"+env["PATH"]
    env["PLAYWRIGHT_BROWSERS_PATH"] = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/home/glwy/.cache/media-trace-browsers")
    hosted = os.environ.get("GITHUB_ACTIONS") == "true"
    report = {"started_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "runner": "github-hosted-ubuntu-24.04" if hosted else "local-shell",
              "python": sys.version, "stage": args.stage, "checks": [], "hosted_pipeline_executed": hosted,
              "provider": "github_actions" if hosted else "local_shell",
              "source_commit": os.environ.get("GITHUB_SHA"), "workflow_run_id": os.environ.get("GITHUB_RUN_ID")}
    stages = {
        "validate": [[PYTHON, "-m", "pip", "check"], [PYTHON, "scripts/verify_runtime_lock.py"], [PYTHON, "-m", "ruff", "check", "--config", "ruff.toml", "backend/app", "ai-services/inference", "tests/poc", "scripts/poc_control.py", "scripts/run_ci.py", "scripts/verify_poc.py", "scripts/verify_poc_resilience.py", "scripts/verify_generated_contracts.py", "scripts/verify_media_and_queries.py", "scripts/verify_sql_baseline.py", "scripts/verify_runtime_lock.py", "scripts/collect_environment.py", "scripts/verify_ci_failure_gate.py", "scripts/check_repository_secrets.py", "scripts/verify_migrations_and_fencing.py", "scripts/verify_media_timestamps.py", "scripts/verify_development_recovery.py"],
                     [PYTHON, "-m", "pytest", "tests/poc", "-q"], [PYTHON, "scripts/validate_inputs.py"],
                     [PYTHON, "scripts/validate_database_contracts.py"], ["npm", "--prefix", "frontend", "ci", "--no-audit", "--no-fund"],
                     [PYTHON, "scripts/verify_generated_contracts.py"], ["npm", "--prefix", "frontend", "audit", "--audit-level=high"]],
        "build": [[PYTHON, "-m", "build", "--no-isolation", "backend"], [PYTHON, "scripts/poc_control.py", "pack"], [PYTHON, "scripts/poc_control.py", "build"]],
        "integration": [[PYTHON, "scripts/poc_control.py", "up"], [PYTHON, "scripts/verify_sql_baseline.py"],
                        [PYTHON, "scripts/verify_migrations_and_fencing.py"],
                        [PYTHON, "scripts/verify_poc.py"], [PYTHON, "scripts/verify_poc_resilience.py"],
                        [PYTHON, "scripts/verify_media_and_queries.py"], [PYTHON, "scripts/verify_media_timestamps.py"],
                        [PYTHON, "scripts/verify_development_recovery.py"],
                        ["npm", "--prefix", "frontend", "exec", "--", "playwright", "test", "--config=frontend/playwright.config.ts"]],
    }
    if args.failure_probe:
        stages["validate"].insert(1, [PYTHON, "-c", "raise SystemExit(42)"])
    try:
        for stage, commands in stages.items():
            if args.stage not in {stage, "all"}:
                continue
            for command in commands:
                started = datetime.datetime.now(datetime.timezone.utc)
                p = subprocess.run(command, cwd=ROOT, env=env, timeout=600)
                report["checks"].append({"stage": stage, "command": command, "status": "PASS" if p.returncode == 0 else "FAIL"})
                report["checks"][-1]["elapsed_seconds"] = (datetime.datetime.now(datetime.timezone.utc)-started).total_seconds()
                if p.returncode:
                    raise RuntimeError("CI_GATE_FAILED")
        report["status"] = "PASS"
    except Exception as exc:
        report["status"] = "FAIL"
        report["error"] = type(exc).__name__
    report["ended_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    destination = ROOT/"docs/00-project/validation"
    if args.failure_probe:
        (destination/"ci-failure-probe-report.json").write_text(json.dumps(report, indent=2)+"\n")
    else:
        (destination/f"ci-{args.stage}-report.json").write_text(json.dumps(report, indent=2)+"\n")
        (destination/"ci-report.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({"status": report["status"], "checks": len(report["checks"]), "hosted_pipeline_executed": hosted}))
    return report["status"] != "PASS"


if __name__ == "__main__":
    raise SystemExit(main())
