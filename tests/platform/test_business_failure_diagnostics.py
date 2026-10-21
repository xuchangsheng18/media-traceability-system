"""Safe CI failure selectors, with real child pytest and no raw failure messages."""

import json
import os
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from scripts import verify_business_foundation as verifier

MARKER = "SYNTHETIC_UNPUBLISHED_MARKER"


def fixture_source(root: Path) -> Path:
    path = root / "tests/business/test_fixture.py"
    path.parent.mkdir(parents=True)
    path.write_text(
        "def test_public_case(): pass\nclass TestGroup:\n    def test_error_case(self): pass\n", encoding="utf8"
    )
    return path


def diagnostics(root, path):
    read = getattr(verifier, "failure_diagnostics", None)
    assert callable(read), "Business verification loses failure selectors when temporary JUnit is removed"
    return read(root, path)


def write_junit(path, entries):
    suite = ET.Element("testsuite")
    for classname, name, kind in entries:
        case = ET.SubElement(suite, "testcase", classname=classname, name=name)
        if kind:
            child = ET.SubElement(case, kind, message=MARKER, type=MARKER)
            child.text = MARKER
    ET.ElementTree(suite).write(path, encoding="utf8")


def test_only_existing_source_selectors_survive_failure_message_and_parameter_redaction(tmp_path):
    fixture_source(tmp_path)
    path = tmp_path / "results.xml"
    write_junit(
        path,
        [
            ("tests.business.test_fixture", "test_public_case[" + MARKER + "]", "failure"),
            ("tests.business.test_fixture.TestGroup", "test_error_case", "error"),
            ("outside." + MARKER, "test_unknown", "failure"),
            ("tests.business.test_fixture", "test_not_in_source_" + MARKER, "failure"),
            ("tests.business.test_fixture", "test_public_case", None),
        ],
    )
    value = diagnostics(tmp_path, path)
    assert value == {
        "items": [
            dict(nodeid="tests/business/test_fixture.py::test_public_case", kind="failure", testcase_index=0),
            dict(nodeid="tests/business/test_fixture.py::TestGroup::test_error_case", kind="error", testcase_index=1),
        ],
        "omitted": 2,
        "parameters_and_failure_text_published": False,
    }
    assert MARKER not in json.dumps(value)


def test_diagnostic_budget_never_publishes_unbounded_failed_cases(tmp_path):
    fixture_source(tmp_path)
    path = tmp_path / "results.xml"
    write_junit(path, [("tests.business.test_fixture", "test_public_case[" + MARKER + "]", "failure")] * 25)
    value = diagnostics(tmp_path, path)
    assert len(value["items"]) == 20 and value["omitted"] == 5
    assert [item["testcase_index"] for item in value["items"]] == list(range(20))
    assert MARKER not in json.dumps(value)


def test_missing_junit_has_no_fabricated_failure_selector(tmp_path):
    value = diagnostics(tmp_path, tmp_path / "missing.xml")
    assert value["items"] == [] and value["omitted"] == 0


@pytest.mark.parametrize("outcome", ["failure", "skip", "pass"])
def test_real_child_pytest_preserves_gate_and_safe_failure_identity(tmp_path, outcome):
    path = fixture_source(tmp_path)
    expression = {
        "failure": "raise AssertionError('" + MARKER + "')",
        "skip": "import pytest; pytest.skip('" + MARKER + "')",
        "pass": "assert 2 + 2 == 4",
    }[outcome]
    path.write_text("def test_public_case():\n    " + expression + "\n", encoding="utf8")
    value = verifier.run_checks(tmp_path, dict(os.environ), tmp_path / "results.xml")
    assert value["status"] == ("PASS" if outcome == "pass" else "FAIL")
    assert value["exit_code"] == (0 if outcome == "pass" else 1)
    assert value["test_count"] == 1
    assert value["totals"] == dict(
        tests=1, failures=int(outcome == "failure"), errors=0, skipped=int(outcome == "skip")
    )
    assert value["raw_logs_published"] is False
    assert "failure_diagnostics" in value, "Actual CI report must retain safe failure selectors"
    items = value["failure_diagnostics"]["items"]
    assert items == (
        [dict(nodeid="tests/business/test_fixture.py::test_public_case", kind="failure", testcase_index=0)]
        if outcome == "failure"
        else []
    )
    assert value["failure_diagnostics"]["omitted"] == 0
    assert MARKER not in json.dumps(value)
