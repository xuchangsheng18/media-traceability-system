"""Verify the current mounted permission boundary; never publish raw test logs or credentials."""

import argparse
import datetime
import hashlib
import json
import os
import re
import secrets
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TARGETS = [
    "tests/platform/test_t014.py",
    "tests/platform/test_t014_gate.py",
    "tests/business/test_t014_permissions.py",
    "tests/business/test_t014_runtime.py",
]
ROLES = json.loads((ROOT / "docs/08-security/access-control-model.json").read_text(encoding="utf8"))["roles"]
REQUIRED_CASES = frozenset(
    [
        ("tests.platform.test_t014", "test_business_401_has_bearer_challenge"),
        ("tests.platform.test_t014", "test_duplicate_authorization_header_is_rejected"),
        ("tests.platform.test_t014", "test_request_reuses_exact_principal_and_rejects_changed_headers_or_expiry"),
        ("tests.platform.test_t014", "test_unknown_permission_and_truthy_authority_return_do_not_allow"),
        ("tests.business.test_t014_permissions", "test_permission_lookup_role_cannot_read_or_write_catalog"),
        ("tests.business.test_t014_permissions", "test_permission_reader_refuses_privileged_connection"),
        (
            "tests.business.test_t014_permissions",
            "test_permission_facts_and_least_privilege_survive_independent_restore",
        ),
        ("tests.business.test_t014_permissions", "test_directory_facts_never_allow_without_explicit_policy"),
        ("tests.business.test_t014_runtime", "test_all_42_real_resource_requests_deny_before_business_side_effects"),
        (
            "tests.business.test_t014_runtime",
            "test_revoked_function_permission_rejects_old_cursor_and_idempotent_receipt",
        ),
        (
            "tests.business.test_t014_runtime",
            "test_upload_permission_revocation_refuses_old_part_cursor_and_write_receipt",
        ),
    ]
    + [
        ("tests.platform.test_t014", f"test_new_or_duplicated_business_route_fails_startup_audit[{case}]")
        for case in ["new", "duplicate", "outside_namespace", "mount", "guard_override"]
    ]
    + [
        (
            "tests.business.test_t014_permissions",
            f"test_policy_decision_cannot_outlive_its_exact_directory_fact[{case}]",
        )
        for case in ["role-403", "identity-401", "version-503"]
    ]
    + [
        (
            "tests.business.test_t014_runtime",
            f"test_each_candidate_role_has_no_implicit_permission_or_formal_allow[{role['code']}]",
        )
        for role in ROLES
    ]
    + [
        (
            "tests.business.test_t014_runtime",
            f"test_same_old_bearer_is_rechecked_after_real_directory_revocation[{case}]",
        )
        for case in ["role-403", "permission-403", "role_disabled-403", "identity-401", "user-401", "unit-401"]
    ]
)


def validate_results(junit: Path, operation_ids: set[str]) -> dict[str, Any]:
    from scripts.verify_business_foundation import test_totals

    try:
        root = ET.parse(junit).getroot()
        cases = list(root.iter("testcase"))
    except (OSError, ET.ParseError):
        raise RuntimeError("T014_REPORT_INVALID") from None
    failed = any(case.find(tag) is not None for case in cases for tag in ["failure", "error", "skipped"])
    totals = test_totals(junit)
    if not cases or failed or any(totals[key] for key in ["failures", "errors", "skipped"]):
        raise RuntimeError("T014_PERMISSION_TESTS_FAILED")
    if totals["tests"] != len(cases):
        raise RuntimeError("T014_REPORT_INVALID")
    rows = Counter((case.attrib.get("classname", ""), case.attrib.get("name", "")) for case in cases)
    checks: dict[str, dict[str, str]] = {}
    for operation in sorted(operation_ids):
        names = {
            "unauthenticated": f"test_all_42_mounted_business_operations_require_authentication[{operation}]",
            "permission_denied": f"test_all_42_operations_deny_missing_permission[{operation}]",
            "policy_missing": f"test_all_42_operations_fail_closed_on_missing_or_unavailable_permissions[missing-FORMAL_POLICY_UNCONFIGURED-{operation}]",
            "authority_unavailable": f"test_all_42_operations_fail_closed_on_missing_or_unavailable_permissions[unavailable-IDENTITY_AUTHORITY_UNAVAILABLE-{operation}]",
        }
        if any(rows[("tests.platform.test_t014", name)] != 1 for name in names.values()):
            raise RuntimeError("T014_OPERATION_MATRIX_INCOMPLETE")
        checks[operation] = {name: "PASS" for name in names}
    if any(rows[row] != 1 for row in REQUIRED_CASES):
        raise RuntimeError("T014_REQUIRED_REGRESSION_MISSING")
    return dict(
        mounted_operation_count=len(operation_ids), operation_checks=checks, required_regressions=len(REQUIRED_CASES)
    )


def source_context() -> dict[str, Any]:
    from scripts.stage_three_types import source_tree_state

    paths = [
        *sorted((ROOT / "backend/business_app").rglob("*.py")),
        *sorted((ROOT / "backend/business_migrations").glob("*.sql")),
        *sorted((ROOT / "backend/business_migrations").glob("*.py")),
        *sorted((ROOT / "tests/business").glob("*.py")),
        *sorted((ROOT / "tests/platform").glob("test_t014*.py")),
        ROOT / "scripts/verify_t014_permissions.py",
        ROOT / "docs/03-api/openapi.yaml",
        ROOT / "docs/08-security/access-control-model.json",
        ROOT / "docs/08-security/t014-interface-scope-matrix.json",
        ROOT / "config/locks/requirements-py310.lock",
    ]
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    state = source_tree_state(ROOT)
    document_changes = subprocess.check_output(
        [
            "git",
            "status",
            "--porcelain",
            "--",
            "docs/03-api/openapi.yaml",
            "docs/08-security/access-control-model.json",
            "docs/08-security/t014-interface-scope-matrix.json",
        ],
        cwd=ROOT,
        text=True,
    )
    state["source_changes"] += [line[3:] for line in document_changes.splitlines() if line]
    state["source_code_dirty"] = bool(state["source_changes"])
    return dict(
        source_commit=head,
        **state,
        source_sha256={
            path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths
        },
    )


def mounted_catalog() -> tuple[set[str], list[str]]:
    sys.path.insert(0, str(ROOT / "backend"))
    from business_app.main import create_app
    from business_app.permissions.catalog import load_catalog
    from business_app.settings import BusinessSettings
    from fastapi.routing import APIRoute, iter_route_contexts

    with tempfile.TemporaryDirectory(prefix="media-trace-t014-catalog-") as temporary:
        app = create_app(
            BusinessSettings(
                "host=127.0.0.1 port=1 dbname=mt_business_catalog user=unreachable",
                Path(temporary),
                1024,
                512,
                60,
                secrets.token_hex(32),
            )
        )
        try:
            operations: set[str] = set()
            for route in iter_route_contexts(app.routes):
                if isinstance(route.original_route, APIRoute) and (route.path or "").startswith("/api/v1/"):
                    identifier = getattr(route, "operation_id", None)
                    if not isinstance(identifier, str) or identifier in operations:
                        raise RuntimeError("T014_MOUNTED_SCOPE_CHANGED")
                    operations.add(identifier)
            catalog = load_catalog(ROOT)
            if len(operations) != 42 or len(catalog) != 73 or len(ROLES) != 6:
                raise RuntimeError("T014_MOUNTED_SCOPE_CHANGED")
            return operations, sorted(set(catalog) - operations)
        finally:
            app.state.business_database.close()


def run(action: str) -> dict[str, Any]:
    sys.path.insert(0, str(ROOT))
    from scripts.verify_business_foundation import configured_environment, test_totals, validate_target

    env = configured_environment()
    validate_target(env)
    private = Path(tempfile.mkdtemp(prefix="media-trace-t014-private-"))
    junit = private / "junit.xml"
    if action == "failure-probe":
        probe = private / "test_expected_failure.py"
        probe.write_text("def test_failure_gate():\n    assert False, 'self-owned controlled failure'\n")
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(probe), "-q", "--junitxml", str(junit)],
            cwd=ROOT,
            env=env,
            capture_output=True,
            timeout=60,
        )
        totals = test_totals(junit)
        expected = result.returncode == 1 and totals == dict(tests=1, failures=1, errors=0, skipped=0)
        return dict(
            status="EXPECTED_FAILURE" if expected else "FAIL",
            expected_assertion_failure_verified=expected,
            exit_code=1 if expected else 2,
            raw_logs_published=False,
        )
    mounted, unmounted = mounted_catalog()
    report = dict(
        task_id="T014",
        status="FAIL",
        observed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        scope="current_mounted_ASGI_permission_boundary_and_real_isolated_SQL_resources_only",
        **source_context(),
        command="python -m pytest " + " ".join(TARGETS) + " -q --tb=short --junitxml PRIVATE_PATH",
        Python_candidates_created=False,
        formal_accepted=False,
        raw_logs_published=False,
        private_material_published=False,
        shared_services_adopted=False,
        not_mounted_operation_ids=unmounted,
        not_mounted_operation_count=len(unmounted),
        not_mounted_operations_implemented_or_HTTP_verified=False,
    )
    result = subprocess.run(
        [sys.executable, "-m", "pytest", *TARGETS, "-q", "--tb=short", "--junitxml", str(junit)],
        cwd=ROOT,
        env=env,
        capture_output=True,
        timeout=1200,
    )
    (private / "stdout.log").write_bytes(result.stdout)
    (private / "stderr.log").write_bytes(result.stderr)
    report.update(totals=test_totals(junit), pytest_exit_code=result.returncode)
    if result.returncode == 0:
        report.update(validate_results(junit, mounted))
        report["status"] = "PASS"
    else:
        names = []
        if junit.is_file():
            for case in ET.parse(junit).getroot().iter("testcase"):
                if case.find("failure") is not None or case.find("error") is not None:
                    name = case.attrib.get("classname", "") + "." + case.attrib.get("name", "")
                    names.append(
                        name if re.fullmatch(r"[A-Za-z0-9_.\[\]()-]+", name) else "PARAMETRIZED_TEST_ID_REDACTED"
                    )
        report["failed_test_ids"] = names
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["run", "failure-probe"], nargs="?", default="run")
    action = parser.parse_args().action
    os.umask(0o077)
    try:
        report = run(action)
    except Exception:
        report = dict(
            task_id="T014",
            status="FAIL",
            error="T014_VERIFICATION_FAILED_RAW_DETAILS_WITHHELD",
            raw_logs_published=False,
            formal_accepted=False,
        )
    if action == "failure-probe":
        print(json.dumps(report))
        return int(report.get("exit_code", 2))
    path = ROOT / "docs/00-project/validation/t014-permissions-report.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(
        json.dumps(
            {
                key: report[key]
                for key in ["status", "totals", "mounted_operation_count", "not_mounted_operation_count"]
                if key in report
            }
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
