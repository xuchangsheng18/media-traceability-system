"""Validate the T011 design against the canonical API and run its synthetic review suite."""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
MODEL = "docs/08-security/access-control-model.json"
SCHEMA = "schemas/security/access-control-model.schema.json"
MATRIX = "docs/08-security/permission-matrix.md"
START = "<!-- t011-matrix:start -->"
END = "<!-- t011-matrix:end -->"


def operations(root):
    contract = yaml.safe_load((root / "docs/03-api/openapi.yaml").read_text(encoding="utf8"))
    result = []
    for path, methods in contract["paths"].items():
        for method, operation in methods.items():
            if method.upper() in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS", "TRACE"}:
                result.append(
                    dict(
                        operation_id=operation["operationId"],
                        method=method.upper(),
                        path=path,
                        permission=operation["x-required-permission"],
                    )
                )
    return sorted(result, key=lambda row: row["operation_id"])


def validate_model(model, root):
    schema = json.loads((root / SCHEMA).read_text(encoding="utf8"))
    if list(jsonschema.Draft202012Validator(schema).iter_errors(model)):
        raise ValueError("MODEL_SCHEMA_INVALID")
    if model["operations"] != operations(root):
        raise ValueError("OPERATION_CATALOG_DRIFT")
    if len({row["operation_id"] for row in model["operations"]}) != len(model["operations"]):
        raise ValueError("DUPLICATE_OPERATION")
    expected = {row["permission"] for row in model["operations"]}
    if set(model["permissions"]) != expected:
        raise ValueError("PERMISSION_CATALOG_DRIFT")
    if not set(model["case_review_permissions"]).issubset(expected):
        raise ValueError("CASE_REVIEW_PERMISSION_UNKNOWN")
    if len({role["code"] for role in model["roles"]}) != 6:
        raise ValueError("ROLE_COVERAGE_INVALID")
    for role in model["roles"]:
        if set(role["permission_review"]) != expected:
            raise ValueError("ROLE_PERMISSION_COVERAGE_INVALID")
        source = (root / role["source_ref"].split("#")[0]).resolve()
        if not source.is_relative_to(root.resolve()) or not source.is_file():
            raise ValueError("ROLE_SOURCE_INVALID")
    for source in model["sources"]:
        if not (root / source).is_file():
            raise ValueError("MODEL_SOURCE_MISSING")
    sql = (root / "backend/business_migrations/0001_business_baseline.sql").read_text(encoding="utf8")
    for name in model["entities"]:
        if re.search(r"CREATE TABLE mt\." + re.escape(name) + r"\s*\(", sql) is None:
            raise ValueError("ENTITY_NOT_IN_EXISTING_MIGRATION")


def matrix_block(model):
    labels = {"SOURCE_RESPONSIBILITY": "职责", "SOURCE_RESTRICTION": "限制", "PENDING_CONFIRMATION": "待定"}
    text = START + "\n## T011 全部权限码评审矩阵\n\n"
    text += "候选模型来源为[access-control-model.json](access-control-model.json)，关系和适用边界见[设计说明](access-control-model.md)。"
    text += "职责表示来源职责候选映射，限制表示来源约束，待定表示未获决定；三者均不是正式ALLOW。角色代码也是候选标识，未写入真实账号。\n\n"
    text += "| 权限码 | " + " | ".join(role["name"] for role in model["roles"]) + " |\n"
    text += "| --- |" + " --- |" * len(model["roles"]) + "\n"
    for permission in model["permissions"]:
        text += (
            "| "
            + permission
            + " | "
            + " | ".join(labels[role["permission_review"][permission]] for role in model["roles"])
            + " |\n"
        )
    return (
        text
        + f"\n{len(model['operations'])}个外部操作与权限码逐项绑定保存在机器模型；实际数量由校验器从唯一OpenAPI核对，不把多个操作共享一个权限码当成操作遗漏。\n"
        + END
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-matrix", action="store_true")
    parser.add_argument("--run-tests", action="store_true")
    args = parser.parse_args()
    model = json.loads((ROOT / MODEL).read_text(encoding="utf8"))
    validate_model(model, ROOT)
    block = matrix_block(model)
    current = (ROOT / MATRIX).read_text(encoding="utf8")
    if START in current:
        before, rest = current.split(START)
        _, after = rest.split(END)
        updated = before + block + after
    else:
        updated = current.rstrip() + "\n\n" + block + "\n"
    if args.write_matrix:
        (ROOT / MATRIX).write_text(updated, encoding="utf8", newline="\n")
    elif current != updated:
        raise ValueError("PERMISSION_MATRIX_DRIFT")
    report: dict[str, Any] = dict(
        status="PASS",
        task_id="T011",
        scope="candidate_access_design_and_synthetic_review_not_runtime_authorization",
        python=sys.version.split()[0],
        source_commit=os.environ.get("GITHUB_SHA"),
        observed_at=datetime.now(timezone.utc).isoformat(),
        roles=len(model["roles"]),
        permissions=len(model["permissions"]),
        external_operations=len(model["operations"]),
        formal_approved=False,
        production_enabled=False,
        runtime_authorization_asserted=False,
    )
    if args.run_tests:
        with tempfile.TemporaryDirectory(prefix="t011-review-") as folder:
            junit = Path(folder) / "tests.xml"
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/platform/test_t011.py", "-q", "--junitxml", str(junit)],
                cwd=ROOT,
            )
            suites = ET.parse(junit).getroot().findall("testsuite") if junit.is_file() else []
            totals = {
                key: sum(int(suite.get(key, "0")) for suite in suites)
                for key in ["tests", "failures", "errors", "skipped"]
            }
            report["test_run"] = dict(
                command="python -m pytest tests/platform/test_t011.py -q", exit_code=result.returncode, **totals
            )
            if (
                result.returncode
                or not suites
                or totals["failures"]
                or totals["errors"]
                or totals["skipped"]
                or not totals["tests"]
            ):
                report["status"] = "FAIL"
        sources = [
            MODEL,
            SCHEMA,
            "tools/access_control_review.py",
            "tests/platform/test_t011.py",
            "scripts/validate_access_control_model.py",
            "docs/03-api/openapi.yaml",
        ]
        report["source_file_sha256"] = {
            path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in sources
        }
        (ROOT / "docs/00-project/validation/t011-access-model-report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf8"
        )
    print(json.dumps(report, ensure_ascii=False))
    return report["status"] != "PASS"


if __name__ == "__main__":
    raise SystemExit(main())
