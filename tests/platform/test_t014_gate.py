"""The CI parser must reject missing, duplicate, skipped and failed proof rows."""

import importlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MATRIX = json.loads((ROOT / "docs/08-security/t014-interface-scope-matrix.json").read_text(encoding="utf8"))
OPERATIONS = {row["operation_id"] for row in MATRIX["operations"] if row["runtime_route"] is not None}


def gate_module():
    assert (ROOT / "scripts/verify_t014_permissions.py").is_file(), "T014 CI verification entry is missing"
    return importlib.import_module("scripts.verify_t014_permissions")


def synthetic_report(tmp_path, gate, *, missing=None, duplicate=None, skipped=False, failure=False):
    # Synthetic XML tests parser behavior only; actual runtime proof is produced
    # exclusively by running the selected test files against isolated services.
    names = set(gate.REQUIRED_CASES)
    for operation in OPERATIONS:
        for name in [
            f"test_all_42_mounted_business_operations_require_authentication[{operation}]",
            f"test_all_42_operations_deny_missing_permission[{operation}]",
            f"test_all_42_operations_fail_closed_on_missing_or_unavailable_permissions[missing-FORMAL_POLICY_UNCONFIGURED-{operation}]",
            f"test_all_42_operations_fail_closed_on_missing_or_unavailable_permissions[unavailable-IDENTITY_AUTHORITY_UNAVAILABLE-{operation}]",
        ]:
            names.add(("tests.platform.test_t014", name))
    if missing:
        names.discard(missing)
    ordered = sorted(names)
    if duplicate:
        ordered.append(duplicate)
    root = ET.Element("testsuites")
    suite = ET.SubElement(
        root, "testsuite", tests=str(len(ordered)), failures=str(int(failure)), errors="0", skipped=str(int(skipped))
    )
    for index, (classname, name) in enumerate(ordered):
        item = ET.SubElement(suite, "testcase", classname=classname, name=name)
        if index == 0 and skipped:
            ET.SubElement(item, "skipped")
        if index == 0 and failure:
            ET.SubElement(item, "failure").text = "private-sentinel-never-publish"
    path = tmp_path / "synthetic-parser-only.xml"
    ET.ElementTree(root).write(path, encoding="utf8")
    return path


def test_complete_report_has_exact_42_operation_matrix(tmp_path):
    gate = gate_module()
    result = gate.validate_results(synthetic_report(tmp_path, gate), OPERATIONS)
    assert result["mounted_operation_count"] == 42
    assert set(result["operation_checks"]) == OPERATIONS


@pytest.mark.parametrize(
    "kind", ["missing_operation", "duplicate_operation", "missing_SQL_restore", "missing_real_resources"]
)
def test_gate_rejects_incomplete_or_duplicate_runtime_evidence(tmp_path, kind):
    gate = gate_module()
    operation = sorted(OPERATIONS)[0]
    target = ("tests.platform.test_t014", f"test_all_42_operations_deny_missing_permission[{operation}]")
    missing = {
        "missing_operation": target,
        "missing_SQL_restore": (
            "tests.business.test_t014_permissions",
            "test_permission_facts_and_least_privilege_survive_independent_restore",
        ),
        "missing_real_resources": (
            "tests.business.test_t014_runtime",
            "test_all_42_real_resource_requests_deny_before_business_side_effects",
        ),
    }
    path = synthetic_report(
        tmp_path, gate, missing=missing.get(kind), duplicate=target if kind == "duplicate_operation" else None
    )
    with pytest.raises(RuntimeError, match="T014_(OPERATION_MATRIX_INCOMPLETE|REQUIRED_REGRESSION_MISSING)"):
        gate.validate_results(path, OPERATIONS)


@pytest.mark.parametrize("failure", [False, True])
def test_gate_rejects_skip_or_failure_without_revealing_details(tmp_path, failure):
    gate = gate_module()
    path = synthetic_report(tmp_path, gate, skipped=not failure, failure=failure)
    with pytest.raises(RuntimeError) as caught:
        gate.validate_results(path, OPERATIONS)
    assert str(caught.value) == "T014_PERMISSION_TESTS_FAILED"
    assert "private-sentinel" not in str(caught.value)


@pytest.mark.parametrize("field", ["tests", "failures"])
def test_declared_report_counts_cannot_be_ignored(tmp_path, field):
    gate = gate_module()
    path = synthetic_report(tmp_path, gate)
    root = ET.parse(path)
    suite = root.getroot().find("testsuite")
    assert suite is not None
    suite.set(field, "1")
    root.write(path, encoding="utf8")
    with pytest.raises(RuntimeError, match="T014_(REPORT_INVALID|PERMISSION_TESTS_FAILED)"):
        gate.validate_results(path, OPERATIONS)
