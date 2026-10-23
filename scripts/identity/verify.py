"""Validate evidence completeness, without treating document assertions as tests."""

import argparse
import datetime
import json
import re
from pathlib import Path
from typing import Any


def evaluate(evidence: dict[str, Any]) -> dict[str, Any]:
    names = {f"IDP-{n:02d}" for n in range(1, 23)}
    if set(evidence) - names:
        raise RuntimeError("IDENTITY_ACCEPTANCE_EVIDENCE_UNKNOWN")
    checks = []
    for name in sorted(names):
        item = evidence.get(name)
        if item is None:
            checks.append({"id": name, "status": "NOT_EXECUTED"})
            continue
        if (
            not isinstance(item, dict)
            or item.get("status") not in {"PASS", "FAIL", "NOT_EXECUTED"}
            or not item.get("observed_at")
            or not item.get("command")
            or re.fullmatch("[a-f0-9]{64}", item.get("artifact_sha256", "")) is None
            or re.fullmatch("[a-f0-9]{40}", item.get("source_commit", "")) is None
        ):
            raise RuntimeError("IDENTITY_ACCEPTANCE_EVIDENCE_INCOMPLETE")
        checks.append({"id": name, **item})
    return {
        "status": "EVIDENCE_COMPLETE_REQUIRES_ACCEPTANCE_REVIEW"
        if all(c["status"] == "PASS" for c in checks)
        else "NOT_COMPLETE",
        "scope": "evidence_completeness_not_independent_runtime_verification",
        "checks": checks,
        "formal_accepted": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    values = json.loads(args.config.read_text())
    report = evaluate(values)
    report["evaluated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    if args.report.exists():
        raise RuntimeError("IDENTITY_EVIDENCE_REPORT_ALREADY_EXISTS")
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "formal_accepted": False}))
    raise SystemExit(report["status"] == "NOT_COMPLETE")


if __name__ == "__main__":
    main()
