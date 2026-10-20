"""Synthetic parser documents only; real gate evidence comes from actual pytest."""

import copy
import importlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from business_app.scope_catalog import TABLE_SCOPES

ROOT = Path(__file__).resolve().parents[2]
COMMIT = "1" * 40
SOURCE = {"backend/business_app/data_scope.py": "a" * 64}
# Independent acceptance sentinels: dropping one category must never turn a
# partial run into a successful gate, even if totals are otherwise positive.
SENTINELS = {
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


def gate_module():
    assert (ROOT / "scripts/verify_t015_scope.py").is_file(), "T015_REQUIRED_RUNTIME_GATE_NOT_IMPLEMENTED"
    return importlib.import_module("scripts.verify_t015_scope")


def parser_fixture(gate):
    names = sorted(set(gate.REQUIRED_CASES) | set(SENTINELS.values()))
    return dict(
        status="PASS",
        source_commit=COMMIT,
        source_sha256=dict(SOURCE),
        source_code_dirty=False,
        formal_accepted=False,
        raw_logs_published=False,
        test_cases=[dict(nodeid=name, status="passed") for name in names],
        totals=dict(tests=len(names), failures=0, errors=0, skipped=0),
        failure_probe=dict(
            totals=dict(tests=1, failures=1, errors=0, skipped=0), exit_code=1, expected_assertion_failure_verified=True
        ),
        table_catalog=[
            dict(
                table=name,
                scope_class=row.scope_class,
                runtime_select=row.runtime_select,
                evidence_kind="CATALOG_ONLY",
                row_security=True,
                force_row_security=row.scope_class != "DIRECTORY",
                restrictive_policy=row.runtime_select,
            )
            for name, row in TABLE_SCOPES.items()
        ],
        dao_coverage=[
            dict(evidence_kind="RUNTIME_SQL", test_nodeids=[SENTINELS["S01"]]),
            dict(evidence_kind="RUNTIME_HTTP", test_nodeids=[SENTINELS["S09"]]),
            dict(evidence_kind="RUNTIME_OBJECT", test_nodeids=[SENTINELS["S06"]]),
            dict(evidence_kind="RUNTIME_RESTORE", test_nodeids=[SENTINELS["S05"]]),
        ],
        not_mounted_operation_ids=list(gate.NOT_MOUNTED_OPERATIONS),
        missing_formal_providers_remain_denied=True,
    )


def validate(gate, report):
    gate.validate_report(report, expected_commit=COMMIT, expected_source=SOURCE)


def test_complete_parser_fixture_is_accepted_as_parser_input_only():
    gate = gate_module()
    validate(gate, parser_fixture(gate))


def test_optimized_python_cannot_remove_required_gate_checks():
    gate = gate_module()
    report = parser_fixture(gate)
    report["status"] = "FAIL"
    code = "import json,sys\nfrom scripts.verify_t015_scope import validate_report\ntry:\n validate_report(json.load(sys.stdin),expected_commit='1'*40,expected_source={'backend/business_app/data_scope.py':'a'*64})\nexcept RuntimeError:\n raise SystemExit(0)\nraise SystemExit(23)\n"
    result = subprocess.run(
        [sys.executable, "-O", "-c", code],
        input=json.dumps(report),
        text=True,
        capture_output=True,
        cwd=ROOT,
        timeout=15,
    )
    assert result.returncode == 0


@pytest.mark.parametrize("defect", ["test_count", "probe_count", "probe_exit", "forced_case_rls"])
def test_boolean_counts_and_missing_business_force_rls_are_rejected(defect):
    gate = gate_module()
    report = parser_fixture(gate)
    if defect == "test_count":
        report["totals"]["failures"] = False
    elif defect == "probe_count":
        report["failure_probe"]["totals"]["failures"] = True
    elif defect == "probe_exit":
        report["failure_probe"]["exit_code"] = True
    else:
        next(row for row in report["table_catalog"] if row["scope_class"] == "CASE")["force_row_security"] = False
    with pytest.raises(RuntimeError):
        validate(gate, report)


@pytest.mark.parametrize("category", list(SENTINELS))
def test_each_acceptance_category_requires_its_actual_case(category):
    gate = gate_module()
    report = parser_fixture(gate)
    report["test_cases"] = [case for case in report["test_cases"] if case["nodeid"] != SENTINELS[category]]
    report["totals"]["tests"] -= 1
    with pytest.raises(RuntimeError):
        validate(gate, report)


@pytest.mark.parametrize("defect", ["duplicate", "empty", "skipped", "failure", "error", "wrong_total"])
def test_invalid_or_partial_test_results_cannot_pass(defect):
    gate = gate_module()
    report = parser_fixture(gate)
    if defect == "duplicate":
        report["test_cases"].append(copy.deepcopy(report["test_cases"][0]))
        report["totals"]["tests"] += 1
    elif defect == "empty":
        report["test_cases"] = []
        report["totals"]["tests"] = 0
    elif defect == "wrong_total":
        report["totals"]["tests"] += 1
    else:
        report["test_cases"][0]["status"] = {"skipped": "skipped", "failure": "failed", "error": "error"}[defect]
        report["totals"][{"skipped": "skipped", "failure": "failures", "error": "errors"}[defect]] = 1
    with pytest.raises(RuntimeError):
        validate(gate, report)


@pytest.mark.parametrize(
    "defect",
    [
        "missing_table",
        "duplicate_table",
        "catalog_as_crud",
        "missing_actual_DAO",
        "missing_restrictive_policy",
        "wrong_scope_class",
    ],
)
def test_catalog_does_not_replace_actual_dao_or_restore_evidence(defect):
    gate = gate_module()
    report = parser_fixture(gate)
    if defect == "missing_table":
        report["table_catalog"].pop()
    elif defect == "duplicate_table":
        report["table_catalog"][-1] = copy.deepcopy(report["table_catalog"][0])
    elif defect == "catalog_as_crud":
        report["table_catalog"][0]["evidence_kind"] = "ALL_CRUD"
    elif defect == "missing_actual_DAO":
        report["dao_coverage"] = []
    elif defect == "wrong_scope_class":
        report["table_catalog"][0]["scope_class"] = "ORG"
    else:
        next(row for row in report["table_catalog"] if row["runtime_select"])["restrictive_policy"] = False
    with pytest.raises(RuntimeError):
        validate(gate, report)


@pytest.mark.parametrize(
    "defect",
    [
        "commit",
        "hash",
        "source_missing",
        "probe_missing",
        "probe_not_real_failure",
        "probe_skipped",
        "unmounted_as_mounted",
        "formal_success",
        "raw_logs",
    ],
)
def test_source_probe_and_applicability_cannot_be_forged_by_pass_label(defect):
    gate = gate_module()
    report = parser_fixture(gate)
    if defect == "commit":
        report["source_commit"] = "2" * 40
    elif defect == "hash":
        report["source_sha256"][next(iter(SOURCE))] = "b" * 64
    elif defect == "source_missing":
        report["source_sha256"] = {}
    elif defect == "probe_missing":
        report.pop("failure_probe")
    elif defect == "probe_not_real_failure":
        report["failure_probe"]["totals"]["failures"] = 0
    elif defect == "probe_skipped":
        report["failure_probe"]["totals"]["skipped"] = 1
    elif defect == "unmounted_as_mounted":
        report["not_mounted_operation_ids"] = []
    elif defect == "formal_success":
        report["formal_accepted"] = True
    else:
        report["raw_logs_published"] = True
    with pytest.raises(RuntimeError):
        validate(gate, report)


@pytest.mark.parametrize("defect", ["empty", "duplicate", "wrong_header"])
def test_empty_duplicate_or_inconsistent_junit_is_rejected(tmp_path, defect):
    gate = gate_module()
    root = ET.Element("testsuites")
    if defect != "empty":
        suite = ET.SubElement(
            root, "testsuite", tests="0" if defect == "wrong_header" else "2", failures="0", errors="0", skipped="0"
        )
        for _ in range(2):
            ET.SubElement(suite, "testcase", classname="tests.example", name="test_identical")
    target = tmp_path / "synthetic-parser-input-only.xml"
    ET.ElementTree(root).write(target, encoding="utf-8")
    with pytest.raises(RuntimeError):
        gate.parse_junit(target)
