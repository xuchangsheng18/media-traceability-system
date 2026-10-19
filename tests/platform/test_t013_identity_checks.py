"""CI must not report success for missing, failed, skipped or inconsistent tests."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
GROUPS = ("identity-live.xml", "identity-adapters.xml", "identity-mapping.xml")


def invoke(tmp_path, changed=None):
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    for name in GROUPS:
        value = '<testsuites><testsuite tests="1" failures="0" errors="0" skipped="0"><testcase name="self_owned_case"/></testsuite></testsuites>'
        if changed and name == GROUPS[0]:
            value = changed
        path = root / name
        path.write_text(value)
        path.chmod(0o600)
    output = tmp_path / "safe-report.json"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.identity.checks",
            "collect",
            "--private-root",
            str(root),
            "--output",
            str(output),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return result, output, root


def test_successful_reports_are_collected_without_private_payloads(tmp_path):
    result, output, _ = invoke(tmp_path)
    assert result.returncode == 0, "IDENTITY_TEST_REPORT_COLLECTOR_NOT_AVAILABLE_OR_INVALID"
    report = json.loads(output.read_text())
    assert report["status"] == "PASS"
    assert report["totals"] == {"tests": 3, "failures": 0, "errors": 0, "skipped": 0}
    assert report["formal_accepted"] is False
    assert report["raw_logs_published"] is False


@pytest.mark.parametrize(
    "contents",
    [
        '<testsuites><testsuite tests="0" failures="0" errors="0" skipped="0"/></testsuites>',
        '<testsuites><testsuite tests="1" failures="0" errors="0" skipped="1"><testcase name="case"><skipped/></testcase></testsuite></testsuites>',
        '<testsuites><testsuite tests="1" failures="1" errors="0" skipped="0"><testcase classname="tests.platform.test_t013_identity_checks" name="test_missing_group_fails_closed[NEVER-PUBLISH-PRIVATE-PARAMETER]"><failure>NEVER-PUBLISH-PRIVATE-FAILURE</failure></testcase></testsuite></testsuites>',
        '<testsuites><testsuite tests="1" failures="0" errors="1" skipped="0"><testcase name="case"><error>NEVER-PUBLISH-PRIVATE-FAILURE</error></testcase></testsuite></testsuites>',
        '<testsuites><testsuite tests="1" failures="0" errors="0" skipped="0"><testcase name="case"><failure>NEVER-PUBLISH-PRIVATE-FAILURE</failure></testcase></testsuite></testsuites>',
        '<testsuites><testsuite tests="-1" failures="0" errors="0" skipped="0"/></testsuites>',
        "not xml",
    ],
    ids=["empty", "skipped", "failure", "error", "inconsistent", "negative", "malformed"],
)
def test_missing_or_nonpassing_evidence_cannot_be_success(tmp_path, contents):
    result, output, _ = invoke(tmp_path, contents)
    assert result.returncode != 0
    assert output.is_file()
    assert json.loads(output.read_text())["status"] == "FAIL"
    assert "NEVER-PUBLISH-PRIVATE-FAILURE" not in output.read_text() + result.stdout + result.stderr
    assert "NEVER-PUBLISH-PRIVATE-PARAMETER" not in output.read_text() + result.stdout + result.stderr
    if "NEVER-PUBLISH-PRIVATE-PARAMETER" in contents:
        group = json.loads(output.read_text())["groups"][0]
        assert group["failed_cases"] == [
            {"case": "tests.platform.test_t013_identity_checks.test_missing_group_fails_closed", "kind": "failure"}
        ]


def test_missing_group_fails_closed(tmp_path):
    _, output, root = invoke(tmp_path)
    (root / GROUPS[1]).unlink()
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.identity.checks",
            "collect",
            "--private-root",
            str(root),
            "--output",
            str(output),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert json.loads(output.read_text())["status"] == "FAIL"


def test_ci_bootstrap_refuses_an_ordinary_machine(tmp_path):
    env = dict(os.environ, GITHUB_ACTIONS="false", RUNNER_TEMP=str(tmp_path))
    result = subprocess.run(
        [sys.executable, "-m", "scripts.identity.ci", "prepare"], cwd=ROOT, env=env, capture_output=True, text=True
    )
    assert result.returncode == 1
    assert "IDENTITY_CI_DISPOSABLE_RUNNER_REQUIRED" in result.stdout


@pytest.mark.parametrize("phase", ["setup", "teardown"])
def test_failure_diagnostic_is_limited_to_static_codes_and_phase(tmp_path, phase):
    value = (
        '<testsuites><testsuite tests="1" failures="0" errors="1" skipped="0">'
        '<testcase classname="tests.platform.test_t013_identity_checks" '
        'name="test_failure_diagnostic_is_limited_to_static_codes_and_phase[NEVER-PUBLISH-PRIVATE-PARAMETER]">'
        f'<error message="failed on {phase} with RuntimeError: IDENTITY_ADMIN_OPERATION_FAILED '
        'NEVER-PUBLISH-PRIVATE-DETAIL IDENTITY_UNTRUSTED_PRIVATE_VALUE">'
        "NEVER-PUBLISH-PRIVATE-TRACE</error></testcase></testsuite></testsuites>"
    )
    result, output, _ = invoke(tmp_path, value)
    assert result.returncode == 1
    case = json.loads(output.read_text())["groups"][0]["failed_cases"][0]
    assert case["phase"] == phase
    assert case["diagnostic_codes"] == ["IDENTITY_ADMIN_OPERATION_FAILED"]
    assert case["exception_types"] == ["RuntimeError"]
    assert "NEVER-PUBLISH-PRIVATE" not in output.read_text() + result.stdout + result.stderr
    assert "IDENTITY_UNTRUSTED_PRIVATE_VALUE" not in output.read_text()
