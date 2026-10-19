"""CI must not report success for missing, failed, skipped or inconsistent tests."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
GROUPS = ("identity-live.xml", "identity-adapters.xml", "identity-mapping.xml")


def test_ci_official_plan_preserves_the_locked_manifest_digests():
    from scripts.identity import ci

    versions = json.loads((ROOT / "config/identity/versions.json").read_text())
    plan = ci.pinned_transport_plan(versions)
    assert set(plan) == {"postgres", "nginx"}
    for name, route in plan.items():
        assert route["locked"] == versions["images"][name]["reference"]
        assert route["source"] == "docker.io/library/" + name + "@" + route["locked"].rsplit("@", 1)[1]


@pytest.mark.parametrize(
    "name,field,value",
    [
        ("postgres", "reference", "docker.m.daocloud.io/library/postgres:latest"),
        ("postgres", "official_repository", "untrusted.invalid/library/postgres"),
        ("nginx", "reference", "docker.m.daocloud.io/library/nginx@sha256:bad"),
        ("postgres", "reference", "untrusted.invalid/library/postgres@sha256:" + "a" * 64),
    ],
)
def test_ci_official_plan_refuses_unpinned_or_unapproved_sources(name, field, value):
    from scripts.identity import ci

    versions = json.loads((ROOT / "config/identity/versions.json").read_text())
    versions["images"][name][field] = value
    with pytest.raises(RuntimeError, match="TRANSPORT"):
        ci.pinned_transport_plan(versions)


@pytest.mark.parametrize("alias_matches", [True, False])
def test_ci_transport_alias_requires_equal_content_and_a_private_exact_policy(tmp_path, monkeypatch, alias_matches):
    from scripts.identity import ci

    commands = []
    monkeypatch.setattr(ci, "hosted_runner", lambda: tmp_path)
    monkeypatch.setenv("GITHUB_RUN_ID", "12345")
    monkeypatch.setattr(ci, "execute", lambda args, name, **kw: commands.append((args, name)))
    monkeypatch.setattr(
        ci.common,
        "docker",
        lambda *args: "sha256:" + ("a" * 64 if alias_matches or args[2].startswith("docker.io/") else "b" * 64),
    )
    if not alias_matches:
        with pytest.raises(RuntimeError, match="TRANSPORT_MISMATCH"):
            ci.configure_image_transport()
        assert len([args for args, _ in commands if "pull" in args]) == 1
        return
    policy = ci.configure_image_transport()
    assert policy.parent == tmp_path / "identity-ci-private"
    assert policy.stat().st_mode & 0o077 == 0
    rules = json.loads(policy.read_text())["rules"]
    assert len(rules) == 2 and all(r["action"] == "CONVERT" for r in rules)
    for rule in rules:
        assert rule["selector"]["identifier"].rsplit("@", 1)[1] == rule["updates"]["identifier"].rsplit("@", 1)[1]
        assert rule["updates"]["identifier"].startswith("docker-image://docker.io/library/")
    assert len([args for args, _ in commands if "pull" in args]) == 2
    assert len([args for args, _ in commands if "tag" in args]) == 2
    with pytest.raises(FileExistsError):
        ci.configure_image_transport()


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
