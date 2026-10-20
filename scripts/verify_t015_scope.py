"""Prove isolated data scopes with actual SQL, HTTP, object and restore tests."""

import argparse
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))
from business_app.scope_catalog import TABLE_SCOPES  # noqa: E402

TARGETS = [
    "tests/business/test_t015_scope_sql.py",
    "tests/business/test_t015_scope_http.py",
    "tests/business/test_t015_collections.py",
    "tests/business/test_t015_scoped_objects.py",
    "tests/business/test_t015_scope_recovery.py",
    "tests/platform/test_t015_data_scope.py",
    "tests/platform/test_t015_object_callers.py",
    "tests/platform/test_t015_object_storage_failures.py",
]
CATEGORIES = {
    "S01": "tests.business.test_t015_scope_sql::test_case_query_without_case_filter_does_not_return_another_valid_membership",
    "S02": "tests.business.test_t015_scope_sql::test_cross_case_update_is_not_allowed_by_other_valid_membership",
    "S03": "tests.business.test_t015_scope_sql::test_forged_scope_without_evidence_cannot_open_business_transaction",
    "S04": "tests.business.test_t015_collections::test_same_case_task_and_history_version_swap_is_denied",
    "S05": "tests.business.test_t015_scope_recovery::test_restored_scope_policies_acl_and_generation_are_not_bypassed",
    "S06": "tests.business.test_t015_scoped_objects::test_cross_case_object_ref_is_denied_before_store_read",
    "S07": "tests.business.test_t015_collections::test_admin_without_explicit_case_membership_is_denied",
    "S08": "tests.business.test_t015_collections::test_item_filter_precedes_limit_count_and_cursor",
    "S09": "tests.business.test_t015_scope_http::test_default_application_still_refuses_unconfigured_real_policy",
}
REQUIRED_CASES = frozenset(CATEGORIES.values())
MATRIX = json.loads((ROOT / "docs/08-security/t014-interface-scope-matrix.json").read_text(encoding="utf8"))
NOT_MOUNTED_OPERATIONS = tuple(sorted(row["operation_id"] for row in MATRIX["operations"] if not row["runtime_route"]))
DAO_CASES = {
    "RUNTIME_SQL": CATEGORIES["S01"],
    "RUNTIME_HTTP": CATEGORIES["S09"],
    "RUNTIME_OBJECT": CATEGORIES["S06"],
    "RUNTIME_RESTORE": CATEGORIES["S05"],
}


def parse_junit(path: Path) -> tuple[list[dict[str, str]], dict[str, int]]:
    try:
        root = ET.parse(path).getroot()
        suites = list(root.iter("testsuite"))
        if not suites or any(list(suite.findall("testsuite")) for suite in suites):
            raise ValueError()
        results: list[dict[str, str]] = []
        totals = dict(tests=0, failures=0, errors=0, skipped=0)
        for suite in suites:
            cases = list(suite.findall("testcase"))
            actual = dict(tests=len(cases), failures=0, errors=0, skipped=0)
            for case in cases:
                name = case.attrib["classname"] + "::" + case.attrib["name"]
                if not re.fullmatch(r"[A-Za-z0-9_.:\[\]()/,+-]+", name):
                    raise ValueError()
                present = [tag for tag in ("failure", "error", "skipped") if case.find(tag) is not None]
                if len(present) > 1:
                    raise ValueError()
                tag = present[0] if present else "passed"
                status = {"failure": "failed", "error": "error", "skipped": "skipped", "passed": "passed"}[tag]
                if tag != "passed":
                    actual[{"failure": "failures", "error": "errors", "skipped": "skipped"}[tag]] += 1
                results.append(dict(nodeid=name, status=status))
            if any(int(suite.attrib[key]) != value for key, value in actual.items()):
                raise ValueError()
            for key, value in actual.items():
                totals[key] += value
        if not results or len({row["nodeid"] for row in results}) != len(results):
            raise ValueError()
        return results, totals
    except (OSError, ET.ParseError, KeyError, TypeError, ValueError):
        raise RuntimeError("T015_JUNIT_INVALID") from None


def validate_report(report: dict[str, Any], *, expected_commit: str, expected_source: dict[str, str]) -> None:
    def require(condition: bool) -> None:
        if not condition:
            raise RuntimeError("T015_REQUIRED_EVIDENCE_INVALID")

    try:
        require(report["status"] == "PASS")
        require(re.fullmatch(r"[0-9a-f]{40}", expected_commit) is not None)
        require(report["source_commit"] == expected_commit and report["source_sha256"] == expected_source)
        require(
            bool(expected_source) and all(re.fullmatch(r"[0-9a-f]{64}", value) for value in expected_source.values())
        )
        require(report["source_code_dirty"] is False)
        require(report["formal_accepted"] is report["raw_logs_published"] is False)
        cases = report["test_cases"]
        require(isinstance(cases, list) and bool(cases))
        require(all(row["status"] == "passed" for row in cases))
        names = [row["nodeid"] for row in cases]
        require(len(set(names)) == len(names) and REQUIRED_CASES <= set(names))
        require(all(type(value) is int for value in report["totals"].values()))
        require(report["totals"] == dict(tests=len(cases), failures=0, errors=0, skipped=0))
        probe = report["failure_probe"]
        require(
            type(probe["exit_code"]) is int
            and probe["exit_code"] == 1
            and probe["expected_assertion_failure_verified"] is True
        )
        require(all(type(value) is int for value in probe["totals"].values()))
        require(probe["totals"] == dict(tests=1, failures=1, errors=0, skipped=0))
        catalog = report["table_catalog"]
        require(len(catalog) == len(TABLE_SCOPES) == 64)
        require(len({row["table"] for row in catalog}) == 64)
        require({row["table"] for row in catalog} == set(TABLE_SCOPES))
        for row in catalog:
            spec = TABLE_SCOPES[row["table"]]
            require(row["scope_class"] == spec.scope_class and row["runtime_select"] is spec.runtime_select)
            require(row["evidence_kind"] == "CATALOG_ONLY")
            if spec.runtime_select:
                require(row["row_security"] is row["restrictive_policy"] is True)
                require(row["force_row_security"] is (spec.scope_class != "DIRECTORY"))
        coverage = report["dao_coverage"]
        require(len(coverage) == len(DAO_CASES))
        require({row["evidence_kind"] for row in coverage} == set(DAO_CASES))
        for row in coverage:
            require(DAO_CASES[row["evidence_kind"]] in row["test_nodeids"])
            require(set(row["test_nodeids"]) <= set(names))
        require(report["not_mounted_operation_ids"] == list(NOT_MOUNTED_OPERATIONS))
        require(report["missing_formal_providers_remain_denied"] is True)
    except (KeyError, TypeError, ValueError, AttributeError):
        raise RuntimeError("T015_REQUIRED_EVIDENCE_INVALID") from None


def table_catalog(env: dict[str, str]) -> list[dict[str, Any]]:
    import psycopg
    from business_migrations.runner import apply_migrations
    from psycopg import sql
    from psycopg.conninfo import make_conninfo

    name = "mt_business_test_" + uuid4().hex
    with psycopg.connect(env["MT_BUSINESS_TEST_ADMIN_DSN"], autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {} TEMPLATE template0").format(sql.Identifier(name)))
        try:
            dsn = make_conninfo(env["MT_BUSINESS_TEST_ADMIN_DSN"], dbname=name)
            apply_migrations(dsn, ROOT / "backend/business_migrations")
            with psycopg.connect(dsn) as connection:
                rows = connection.execute(
                    "SELECT c.relname,c.relrowsecurity,c.relforcerowsecurity,EXISTS(SELECT 1 FROM pg_policies p "
                    "WHERE p.schemaname='mt' AND p.tablename=c.relname AND p.policyname='request_data_scope' "
                    "AND p.permissive='RESTRICTIVE') FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
                    "WHERE n.nspname='mt' AND c.relkind='r' ORDER BY c.relname"
                ).fetchall()
                if {row[0] for row in rows} != set(TABLE_SCOPES):
                    raise RuntimeError("T015_TABLE_CATALOG_CHANGED")
                return [
                    dict(
                        table=table,
                        scope_class=TABLE_SCOPES[table].scope_class,
                        runtime_select=TABLE_SCOPES[table].runtime_select,
                        evidence_kind="CATALOG_ONLY",
                        row_security=enabled,
                        force_row_security=forced,
                        restrictive_policy=restrictive,
                    )
                    for table, enabled, forced, restrictive in rows
                ]
        finally:
            assert name.startswith("mt_business_test_") and len(name) == 49
            admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name)))


def failure_probe(env: dict[str, str], private: Path) -> dict[str, Any]:
    probe = private / "test_t015_expected_failure.py"
    probe.write_text("def test_t015_failure_gate():\n    assert False, 'self-owned failure probe'\n", encoding="utf8")
    junit = private / "probe.xml"
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(probe), "-q", "--junitxml", str(junit)],
        cwd=ROOT,
        env=env,
        capture_output=True,
        timeout=60,
    )
    _, totals = parse_junit(junit)
    expected = result.returncode == 1 and totals == dict(tests=1, failures=1, errors=0, skipped=0)
    return dict(totals=totals, exit_code=result.returncode, expected_assertion_failure_verified=expected)


def source_context() -> dict[str, Any]:
    from scripts.verify_t014_permissions import source_context as permission_source

    result = permission_source()
    paths = [Path(__file__).resolve(), *sorted((ROOT / "tests/platform").glob("test_t015*.py"))]
    for path in paths:
        result["source_sha256"][path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def run(action: str) -> dict[str, Any]:
    from scripts.verify_business_foundation import configured_environment, validate_target
    from scripts.verify_t014_permissions import mounted_catalog

    env = configured_environment()
    validate_target(env)
    with tempfile.TemporaryDirectory(prefix="media-trace-t015-private-") as folder:
        private = Path(folder)
        if action == "failure-probe":
            probe = failure_probe(env, private)
            expected = probe["expected_assertion_failure_verified"] is True
            return dict(status="EXPECTED_FAILURE" if expected else "FAIL", **probe)
        before = source_context()
        _, unmounted = mounted_catalog()
        if unmounted != list(NOT_MOUNTED_OPERATIONS):
            raise RuntimeError("T015_OPERATION_CATALOG_CHANGED")
        report: dict[str, Any] = dict(
            task_id="T015",
            status="FAIL",
            observed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            **before,
            formal_accepted=False,
            raw_logs_published=False,
            shared_migration_or_policy_adopted=False,
            Python_candidates_created=False,
            not_mounted_operation_ids=unmounted,
            missing_formal_providers_remain_denied=True,
            command="python -m pytest " + " ".join(TARGETS) + " -q --tb=short --junitxml PRIVATE_PATH",
            workflow_run_id=os.environ.get("GITHUB_RUN_ID"),
        )
        junit = private / "runtime.xml"
        result = subprocess.run(
            [sys.executable, "-m", "pytest", *TARGETS, "-q", "--tb=short", "--junitxml", str(junit)],
            cwd=ROOT,
            env=env,
            capture_output=True,
            timeout=1600,
        )
        cases, totals = parse_junit(junit)
        report.update(test_cases=cases, totals=totals, pytest_exit_code=result.returncode)
        if result.returncode:
            return report
        report.update(
            table_catalog=table_catalog(env),
            dao_coverage=[dict(evidence_kind=kind, test_nodeids=[nodeid]) for kind, nodeid in DAO_CASES.items()],
            failure_probe=failure_probe(env, private),
        )
        if source_context() != before:
            raise RuntimeError("T015_SOURCE_CHANGED_DURING_RUN")
        report["status"] = "PASS"
        validate_report(report, expected_commit=before["source_commit"], expected_source=before["source_sha256"])
        return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["run", "failure-probe"], nargs="?", default="run")
    action = parser.parse_args().action
    os.umask(0o077)
    try:
        report = run(action)
    except Exception:
        report = dict(task_id="T015", status="FAIL", error="T015_VERIFICATION_FAILED_RAW_DETAILS_WITHHELD")
    report.update(formal_accepted=False, raw_logs_published=False)
    if action == "failure-probe":
        print(json.dumps(report))
        return 1 if report.get("expected_assertion_failure_verified") is True else 2
    path = ROOT / "docs/00-project/validation/t015-data-scope-report.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(json.dumps({key: report[key] for key in ("status", "totals", "task_id") if key in report}))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
