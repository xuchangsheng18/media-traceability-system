"""Parser fixtures are synthetic; only the verifier's full pytest run is evidence."""

import copy
import importlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
COMMIT = "1" * 40
SENTINELS = (
    "tests.platform.test_t016::test_invalid_token_ttl_does_not_become_a_successful_rule[True]",
    "tests.business.test_t016_operation_tokens::test_issue_replay_is_same_credential_and_never_persists_plaintext",
    "tests.business.test_t016_permission_facts::test_real_sql_case_confirmation_rechecks_linked_task_and_source_in_same_root",
    "tests.business.test_t016_permission_facts::test_real_sql_two_case_member_cannot_replace_approval_case",
    "tests.business.test_t016_operation_tokens::test_consume_and_synthetic_business_write_commit_once",
    "tests.business.test_t016_operation_tokens::test_business_failure_rolls_back_consume_and_success_audit",
    "tests.business.test_t016_operation_token_recovery::test_0011_preserves_legacy_rows_and_original_migration_checksums",
    "tests.business.test_t016_operation_token_recovery::test_v1_nullable_bindings_cannot_bypass_sql_check",
    "tests.business.test_t016_operation_token_recovery::test_expiry_is_measured_at_consumption_after_transaction_start",
)


def gate_module():
    assert (ROOT / "scripts/verify_t016_tokens.py").is_file(), "T016_REQUIRED_RUNTIME_GATE_NOT_IMPLEMENTED"
    return importlib.import_module("scripts.verify_t016_tokens")


def parser_fixture(gate):
    source = dict.fromkeys(gate.REQUIRED_SOURCE_PATHS, "a" * 64)
    names = sorted(set(gate.REQUIRED_CASES) | set(SENTINELS))
    return dict(
        task_id="T016",
        status="PASS",
        source_commit=COMMIT,
        source_sha256=source,
        source_code_dirty=False,
        source_changes=[],
        formal_accepted=False,
        raw_logs_published=False,
        pytest_exit_code=0,
        targets=list(gate.TARGETS),
        collected_nodeids=names,
        test_cases=[dict(nodeid=name, status="passed") for name in names],
        totals=dict(tests=len(names), failures=0, errors=0, skipped=0),
        failure_probe=dict(
            totals=dict(tests=1, failures=1, errors=0, skipped=0),
            exit_code=1,
            expected_assertion_failure_verified=True,
        ),
    )


def validate(gate, report):
    gate.validate_report(
        report,
        expected_commit=COMMIT,
        expected_source=dict.fromkeys(gate.REQUIRED_SOURCE_PATHS, "a" * 64),
    )


def test_complete_parser_fixture_is_accepted_as_parser_input_only():
    gate = gate_module()
    validate(gate, parser_fixture(gate))


def test_permission_catalog_cannot_be_omitted_from_the_runtime_suite():
    gate = gate_module()
    report = parser_fixture(gate)
    report["targets"] = [
        target for target in report["targets"] if target != "tests/platform/test_t016_permission_catalog.py"
    ]
    with pytest.raises(RuntimeError):
        validate(gate, report)


def test_parser_regression_cannot_be_removed_with_matching_forged_collection():
    gate = gate_module()
    report = parser_fixture(gate)
    omitted = "tests.platform.test_t016_gate::test_partial_forged_or_stale_runtime_evidence_is_rejected[raw]"
    report["test_cases"] = [case for case in report["test_cases"] if case["nodeid"] != omitted]
    report["collected_nodeids"] = [name for name in report["collected_nodeids"] if name != omitted]
    report["totals"]["tests"] = len(report["test_cases"])
    with pytest.raises(RuntimeError):
        validate(gate, report)


@pytest.mark.parametrize(
    "path",
    [
        "backend/business_app/db.py",
        "backend/business_app/scope_context.py",
        "backend/business_app/data_scope.py",
        "backend/business_app/scope_collections.py",
        "backend/business_app/controls/approvals.py",
        "backend/business_app/main.py",
        "backend/business_app/controls/router.py",
        "backend/business_app/identity/directory.py",
        "backend/business_app/permissions/policy.py",
        "backend/business_app/permissions/types.py",
    ],
)
def test_unbound_transaction_or_identity_source_cannot_be_accepted(path):
    gate = gate_module()
    report = parser_fixture(gate)
    report["source_sha256"].pop(path, None)
    with pytest.raises(RuntimeError):
        gate.validate_report(report, expected_commit=COMMIT, expected_source=report["source_sha256"])


@pytest.mark.parametrize("sentinel", SENTINELS)
def test_each_independent_token_security_sentinel_is_required(sentinel):
    gate = gate_module()
    report = parser_fixture(gate)
    report["test_cases"] = [case for case in report["test_cases"] if case["nodeid"] != sentinel]
    report["collected_nodeids"].remove(sentinel)
    report["totals"]["tests"] -= 1
    with pytest.raises(RuntimeError):
        validate(gate, report)


@pytest.mark.parametrize(
    "defect",
    [
        "empty",
        "duplicate",
        "skipped",
        "failure",
        "error",
        "count",
        "boolean_count",
        "pytest_exit",
        "boolean_exit",
        "partial_targets",
        "extra_target",
        "unexecuted_collection",
        "missing_collection",
        "duplicate_collection",
        "commit",
        "hash",
        "missing_hash",
        "dirty",
        "hidden_changes",
        "formal",
        "raw",
        "probe_missing",
        "probe_passed",
        "probe_skipped",
        "probe_boolean_count",
        "probe_boolean_exit",
    ],
)
def test_partial_forged_or_stale_runtime_evidence_is_rejected(defect):
    gate = gate_module()
    report = parser_fixture(gate)
    if defect == "empty":
        report.update(test_cases=[], collected_nodeids=[], totals=dict(tests=0, failures=0, errors=0, skipped=0))
    elif defect == "duplicate":
        report["test_cases"].append(copy.deepcopy(report["test_cases"][0]))
        report["totals"]["tests"] += 1
    elif defect in {"skipped", "failure", "error"}:
        report["test_cases"][0]["status"] = {"failure": "failed"}.get(defect, defect)
    elif defect == "count":
        report["totals"]["tests"] += 1
    elif defect == "boolean_count":
        report["totals"]["failures"] = False
    elif defect == "pytest_exit":
        report["pytest_exit_code"] = 1
    elif defect == "boolean_exit":
        report["pytest_exit_code"] = False
    elif defect == "partial_targets":
        report["targets"].pop()
    elif defect == "extra_target":
        report["targets"].append("tests/business/test_controls.py")
    elif defect == "unexecuted_collection":
        report["collected_nodeids"].append("tests.platform.test_t016::test_unexecuted")
    elif defect == "missing_collection":
        report["collected_nodeids"].pop()
    elif defect == "duplicate_collection":
        report["collected_nodeids"].append(report["collected_nodeids"][0])
    elif defect == "commit":
        report["source_commit"] = "2" * 40
    elif defect == "hash":
        report["source_sha256"]["backend/business_migrations/0011_operation_token.sql"] = "b" * 64
    elif defect == "missing_hash":
        report["source_sha256"].pop("backend/business_app/controls/operation_tokens.py")
    elif defect == "dirty":
        report["source_code_dirty"] = True
    elif defect == "hidden_changes":
        report["source_changes"] = ["backend/business_migrations/0011_operation_token.sql"]
    elif defect == "formal":
        report["formal_accepted"] = True
    elif defect == "raw":
        report["raw_logs_published"] = True
    elif defect == "probe_missing":
        report.pop("failure_probe")
    elif defect == "probe_passed":
        report["failure_probe"]["totals"]["failures"] = 0
    elif defect == "probe_skipped":
        report["failure_probe"]["totals"]["skipped"] = 1
    elif defect == "probe_boolean_count":
        report["failure_probe"]["totals"]["failures"] = True
    else:
        report["failure_probe"]["exit_code"] = True
    with pytest.raises(RuntimeError):
        validate(gate, report)


def test_optimized_python_cannot_remove_gate_validation():
    gate = gate_module()
    report = parser_fixture(gate)
    report["status"] = "FAIL"
    code = (
        "import json,sys\nfrom scripts.verify_t016_tokens import validate_report\n"
        "report=json.load(sys.stdin)\ntry:\n"
        " validate_report(report,expected_commit='1'*40,expected_source=report['source_sha256'])\n"
        "except RuntimeError:\n raise SystemExit(0)\nraise SystemExit(23)\n"
    )
    result = subprocess.run(
        [sys.executable, "-O", "-c", code],
        input=json.dumps(report),
        text=True,
        capture_output=True,
        cwd=ROOT,
        timeout=15,
    )
    assert result.returncode == 0


@pytest.mark.parametrize("defect", ["empty", "duplicate", "header", "double_status", "unsafe_name", "nested"])
def test_malformed_or_unsafe_junit_is_rejected_without_raw_output(tmp_path, defect):
    gate = gate_module()
    root = ET.Element("testsuites")
    if defect != "empty":
        suite = ET.SubElement(
            root, "testsuite", tests="2" if defect == "header" else "1", failures="0", errors="0", skipped="0"
        )
        case = ET.SubElement(suite, "testcase", classname="tests.platform.test_t016", name="test_example")
        if defect == "duplicate":
            ET.SubElement(suite, "testcase", dict(case.attrib))
            suite.set("tests", "2")
        elif defect == "double_status":
            ET.SubElement(case, "failure").text = "synthetic private diagnostic"
            ET.SubElement(case, "error").text = "synthetic private diagnostic"
        elif defect == "unsafe_name":
            case.set("name", "test_example?credential=synthetic-private")
        elif defect == "nested":
            ET.SubElement(suite, "testsuite")
    path = tmp_path / "synthetic-parser-input-only.xml"
    ET.ElementTree(root).write(path, encoding="utf8")
    with pytest.raises(RuntimeError) as failure:
        gate.parse_junit(path)
    assert "synthetic-private" not in str(failure.value)


def test_independent_failure_probe_is_a_real_failed_pytest_and_safe_json():
    gate_module()
    result = subprocess.run(
        [sys.executable, "scripts/verify_t016_tokens.py", "failure-probe"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 1 and not result.stderr
    report = json.loads(result.stdout)
    assert report["status"] == "EXPECTED_FAILURE" and report["expected_assertion_failure_verified"] is True
    assert report["totals"] == dict(tests=1, failures=1, errors=0, skipped=0)
    assert report["formal_accepted"] is report["raw_logs_published"] is False
    assert not ({"stdout", "stderr", "traceback", "dsn", "token"} & set(report))


@pytest.mark.parametrize("fails", [False, True])
def test_engineering_ci_runs_token_gate_and_propagates_failure(tmp_path, monkeypatch, fails):
    module = importlib.import_module("scripts.run_ci")
    checks = []

    def run(command, **kwargs):
        checks.append(command)
        return subprocess.CompletedProcess(command, 7 if fails and "scripts/verify_t016_tokens.py" in command else 0)

    (tmp_path / "docs/00-project/validation").mkdir(parents=True)
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["run_ci.py", "validate"])
    monkeypatch.setattr(module.subprocess, "run", run)
    assert bool(module.main()) is fails
    assert [module.PYTHON, "scripts/verify_t015_scope.py", "run"] in checks
    assert [module.PYTHON, "scripts/verify_t016_tokens.py", "run"] in checks
    report = json.loads((tmp_path / "docs/00-project/validation/ci-validate-report.json").read_text())
    assert report["status"] == ("FAIL" if fails else "PASS")
