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
def test_ci_transport_requires_locked_content_and_a_private_exact_policy(tmp_path, monkeypatch, alias_matches):
    from scripts.identity import ci

    commands = []
    monkeypatch.setattr(ci, "hosted_runner", lambda: tmp_path)
    monkeypatch.setenv("GITHUB_RUN_ID", "12345")
    monkeypatch.setattr(ci, "execute", lambda args, name, **kw: commands.append((args, name)))

    def inspect(*args):
        if args[-1] == "{{json .RepoDigests}}":
            return json.dumps([args[2] if alias_matches else "postgres@sha256:" + "b" * 64])
        return "sha256:" + "a" * 64

    monkeypatch.setattr(ci.common, "docker", inspect)
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
    assert not any("tag" in args for args, _ in commands)
    override = policy.parent / "compose-source-override.json"
    assert override.stat().st_mode & 0o077 == 0
    assert json.loads(override.read_text())["services"]["identity-gateway"]["image"].startswith(
        "docker.io/library/nginx@sha256:"
    )
    with pytest.raises(FileExistsError):
        ci.configure_image_transport()


def test_ci_transport_default_keeps_the_original_shared_image_references(monkeypatch):
    from scripts.identity import common

    monkeypatch.delenv("MT_IDENTITY_CI_IMAGE_TRANSPORT", raising=False)
    versions = json.loads((ROOT / "config/identity/versions.json").read_text())
    assert common.image("postgres") == versions["images"]["postgres"]["reference"]
    assert common.ci_compose_override() is None


@pytest.mark.parametrize("condition", ["valid", "ordinary", "bad_marker", "bad_override", "unknown_profile"])
def test_ci_transport_profile_is_owned_pinned_and_fails_closed(tmp_path, monkeypatch, condition):
    from scripts.identity import common, control

    for key, value in {
        "MT_IDENTITY_CI_IMAGE_TRANSPORT": "official-pinned-v1",
        "GITHUB_ACTIONS": "true",
        "RUNNER_ENVIRONMENT": "github-hosted",
        "GITHUB_REPOSITORY": "xuchangsheng18/media-traceability-system",
        "GITHUB_RUN_ID": "12345",
        "GITHUB_WORKSPACE": str(common.ROOT),
        "RUNNER_TEMP": str(tmp_path),
    }.items():
        monkeypatch.setenv(key, value)
    private = tmp_path / "identity-ci-private"
    private.mkdir(mode=0o700)
    marker = private / "ownership.json"
    marker.write_text(json.dumps({"run_id": "12345", "project": "media-trace-identity"}) + "\n")
    marker.chmod(0o600)
    versions = json.loads((ROOT / "config/identity/versions.json").read_text())
    image = "docker.io/library/nginx@" + versions["images"]["nginx"]["reference"].rsplit("@", 1)[1]
    override = private / "compose-source-override.json"
    override.write_text(json.dumps({"services": {"identity-gateway": {"image": image}}}, sort_keys=True) + "\n")
    override.chmod(0o600)
    if condition == "ordinary":
        monkeypatch.setenv("GITHUB_ACTIONS", "false")
    elif condition == "bad_marker":
        marker.write_text('{"run_id":"12345","project":"unrelated"}\n')
    elif condition == "unknown_profile":
        monkeypatch.setenv("MT_IDENTITY_CI_IMAGE_TRANSPORT", "unapproved")
    if condition in {"ordinary", "bad_marker", "unknown_profile"}:
        with pytest.raises(RuntimeError, match="PROFILE"):
            common.image("postgres")
        return
    assert common.image("postgres").startswith("docker.io/library/postgres@sha256:")
    if condition == "bad_override":
        override.write_text('{"services":{"identity-gateway":{"image":"untrusted.invalid/nginx:latest"}}}\n')
        with pytest.raises(RuntimeError, match="OVERRIDE"):
            control.command("status")
        return
    command = control.command("status")
    assert command.count("-f") == 2 and str(override) in command


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


@pytest.mark.parametrize("code", ["RECOVERY_LAB_READINESS_TIMEOUT", "RECOVERY_LAB_REAL_CODE_EXCHANGE_FAILED"])
def test_recovery_failure_reports_only_source_defined_diagnostic_codes(tmp_path, code):
    value = (
        '<testsuites><testsuite tests="1" failures="1" errors="0" skipped="0">'
        '<testcase classname="tests.identity.test_recovery_live" '
        'name="test_restart_and_database_dependency_readiness">'
        f'<failure message="RuntimeError: {code} RECOVERY_LAB_UNTRUSTED_PRIVATE_VALUE '
        'NEVER-PUBLISH-PRIVATE-DETAIL">NEVER-PUBLISH-PRIVATE-TRACE</failure>'
        "</testcase></testsuite></testsuites>"
    )
    result, output, _ = invoke(tmp_path, value)
    assert result.returncode == 1
    case = json.loads(output.read_text())["groups"][0]["failed_cases"][0]
    assert case["diagnostic_codes"] == [code]
    assert case["exception_types"] == ["RuntimeError"]
    assert "RECOVERY_LAB_UNTRUSTED_PRIVATE_VALUE" not in output.read_text()
    assert "NEVER-PUBLISH-PRIVATE" not in output.read_text() + result.stdout + result.stderr


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


def test_recovery_readiness_timeout_code_is_preserved_without_private_payload(tmp_path):
    code = "KEYCLOAK_READINESS_DID_NOT_DETECT_DATABASE_FAILURE"
    private_value = "NEVER-PUBLISH-PRIVATE-T013-RECOVERY-PAYLOAD"
    fake_code = code + "_PRIVATE_SUFFIX"
    contents = (
        '<testsuites><testsuite tests="1" failures="1" errors="0" skipped="0">'
        '<testcase classname="tests.identity.test_recovery_live" '
        f'name="test_restart_and_database_dependency_readiness[{private_value}-{fake_code}]">'
        f'<failure message="AssertionError: {code}">'
        f"{private_value} {fake_code} NEVER-PUBLISH-PRIVATE-T013-RECOVERY-TRACE</failure>"
        "</testcase></testsuite></testsuites>"
    )
    result, output, _ = invoke(tmp_path, contents)
    assert result.returncode == 1
    report = json.loads(output.read_text())
    assert report["status"] == "FAIL"
    assert report["totals"] == {"tests": 3, "failures": 1, "errors": 0, "skipped": 0}
    group = report["groups"][0]
    assert group["status"] == "FAIL"
    assert group["totals"] == {"tests": 1, "failures": 1, "errors": 0, "skipped": 0}
    assert group["failed_cases"] == [
        {
            "case": "tests.identity.test_recovery_live.test_restart_and_database_dependency_readiness",
            "kind": "failure",
            "diagnostic_codes": [code],
            "exception_types": ["AssertionError"],
        }
    ]
    published = output.read_text() + result.stdout + result.stderr
    assert private_value not in published
    assert fake_code not in published
    assert "NEVER-PUBLISH-PRIVATE-T013-RECOVERY-TRACE" not in published


READINESS_ASSERT_CODES = tuple(
    "RECOVERY_LAB_READINESS_" + suffix
    for suffix in (
        "RESTART_SNAPSHOT_CHANGED",
        "RESTART_SESSION_INACTIVE",
        "DATABASE_STATE_NOT_DOWN",
        "DISCOVERY_FAILURE_BOUNDARY",
        "VERIFIER_STATUS_NOT_503",
        "RECOVERED_SNAPSHOT_CHANGED",
        "RECOVERED_SUBJECT_CHANGED",
    )
)
READINESS_TIMEOUT_CODE = "KEYCLOAK_READINESS_DID_NOT_DETECT_DATABASE_FAILURE"
READINESS_MISSING_ERROR_CODE = "RECOVERY_LAB_READINESS_BUSINESS_ERROR_NOT_RAISED"
READINESS_PRIVATE_MARKER = "NEVER-PUBLISH-PRIVATE-T013-READINESS-DETAIL"


def readiness_junit(
    message,
    *,
    module="tests.identity.test_recovery_live",
    case="test_restart_and_database_dependency_readiness",
    kind="failure",
    problem_type=None,
    body=None,
):
    from xml.etree import ElementTree as ET

    root = ET.Element("testsuites")
    suite = ET.SubElement(
        root,
        "testsuite",
        tests="1",
        failures="1" if kind == "failure" else "0",
        errors="1" if kind == "error" else "0",
        skipped="0",
    )
    test = ET.SubElement(suite, "testcase", classname=module, name=case + "[" + READINESS_PRIVATE_MARKER + "]")
    attributes = {} if message is None else {"message": message}
    if problem_type is not None:
        attributes["type"] = problem_type
    problem = ET.SubElement(test, kind, **attributes)
    problem.text = body or (
        READINESS_PRIVATE_MARKER + " https://self-owned.invalid/never-publish?token=" + READINESS_PRIVATE_MARKER
    )
    return ET.tostring(root, encoding="unicode")


def readiness_failure_report(tmp_path, message, **kwargs):
    result, output, _ = invoke(tmp_path, readiness_junit(message, **kwargs))
    assert result.returncode == 1
    report = json.loads(output.read_text())
    error = kwargs.get("kind", "failure") == "error"
    assert report["status"] == "FAIL"
    assert report["totals"] == {"tests": 3, "failures": 0 if error else 1, "errors": 1 if error else 0, "skipped": 0}
    assert report["groups"][0]["status"] == "FAIL"
    assert report["groups"][0]["totals"] == {
        "tests": 1,
        "failures": 0 if error else 1,
        "errors": 1 if error else 0,
        "skipped": 0,
    }
    published = output.read_text() + result.stdout + result.stderr
    assert READINESS_PRIVATE_MARKER not in published
    assert "self-owned.invalid" not in published
    return report["groups"][0]["failed_cases"][0], published


@pytest.mark.parametrize("code", READINESS_ASSERT_CODES)
@pytest.mark.parametrize("explanation", ["", "\nassert False\n" + READINESS_PRIVATE_MARKER])
def test_readiness_assertion_diagnostics_preserve_only_the_exact_static_first_line(tmp_path, code, explanation):
    case, published = readiness_failure_report(
        tmp_path,
        "AssertionError: " + code + explanation,
        body=code + "_PRIVATE_SUFFIX " + READINESS_PRIVATE_MARKER,
    )
    assert case == {
        "case": "tests.identity.test_recovery_live.test_restart_and_database_dependency_readiness",
        "kind": "failure",
        "diagnostic_codes": [code],
        "exception_types": ["AssertionError"],
    }
    assert code + "_PRIVATE_SUFFIX" not in published


@pytest.mark.parametrize("explanation", ["", "\n" + READINESS_PRIVATE_MARKER])
def test_readiness_expected_business_error_absence_has_one_exact_static_reason(tmp_path, explanation):
    case, _ = readiness_failure_report(tmp_path, "Failed: DID NOT RAISE BusinessError" + explanation)
    assert case == {
        "case": "tests.identity.test_recovery_live.test_restart_and_database_dependency_readiness",
        "kind": "failure",
        "diagnostic_codes": [READINESS_MISSING_ERROR_CODE],
    }


@pytest.mark.parametrize("code", [READINESS_ASSERT_CODES[0], READINESS_TIMEOUT_CODE])
@pytest.mark.parametrize(
    "module,case",
    [
        ("tests.identity.test_recovery_live", "test_encrypted_restore_reconciles_old_sessions_keys_and_rollback"),
        ("tests.platform.test_t013_identity_checks", "test_missing_group_fails_closed"),
        ("tests.identity.test_not_real", "test_restart_and_database_dependency_readiness"),
        ("tests.identity.test_recovery_live", "test_unrecognized_private_case"),
    ],
)
def test_readiness_new_codes_are_never_global_legacy_codes_for_other_selectors(tmp_path, code, module, case):
    failure, published = readiness_failure_report(tmp_path, "AssertionError: " + code, module=module, case=case)
    assert "diagnostic_codes" not in failure
    assert code not in published


@pytest.mark.parametrize("code", [READINESS_ASSERT_CODES[0], READINESS_TIMEOUT_CODE, READINESS_MISSING_ERROR_CODE])
@pytest.mark.parametrize("phase", ["setup", "teardown", "call"])
def test_readiness_new_codes_do_not_match_phase_prefixed_message_noise(tmp_path, code, phase):
    first = "Failed: DID NOT RAISE BusinessError" if code == READINESS_MISSING_ERROR_CODE else "AssertionError: " + code
    failure, _ = readiness_failure_report(tmp_path, f"failed on {phase} with {first}")
    assert failure["phase"] == phase
    assert "diagnostic_codes" not in failure


@pytest.mark.parametrize("code", [READINESS_ASSERT_CODES[0], READINESS_TIMEOUT_CODE, READINESS_MISSING_ERROR_CODE])
def test_readiness_new_codes_require_a_normal_failure_not_an_error_element(tmp_path, code):
    message = (
        "Failed: DID NOT RAISE BusinessError" if code == READINESS_MISSING_ERROR_CODE else "AssertionError: " + code
    )
    failure, published = readiness_failure_report(tmp_path, message, kind="error")
    assert failure["kind"] == "error" and "diagnostic_codes" not in failure
    assert code not in published


@pytest.mark.parametrize("problem_type", ["", "AssertionError", "RuntimeError", "SELF_OWNED_PRIVATE_TYPE"])
@pytest.mark.parametrize("missing_error", [False, True])
def test_readiness_special_shapes_require_the_observed_missing_type_attribute(tmp_path, problem_type, missing_error):
    message = "Failed: DID NOT RAISE BusinessError" if missing_error else "AssertionError: " + READINESS_ASSERT_CODES[0]
    failure, published = readiness_failure_report(tmp_path, message, problem_type=problem_type)
    assert "diagnostic_codes" not in failure
    assert "SELF_OWNED_PRIVATE_TYPE" not in published


@pytest.mark.parametrize(
    "shape",
    [
        "bare",
        "prefix",
        "suffix",
        "suffix_code",
        "leading_space",
        "lowercase_exception",
        "url",
        "new_line_before_code",
        "message_missing",
        "body_only",
        "unknown_keycloak",
        "unknown_readiness",
    ],
)
def test_readiness_message_noise_and_unknown_codes_never_become_safe_diagnostics(tmp_path, shape):
    code = READINESS_ASSERT_CODES[0]
    messages = {
        "bare": code,
        "prefix": "untrusted-prefix AssertionError: " + code,
        "suffix": "AssertionError: " + code + " " + READINESS_PRIVATE_MARKER,
        "suffix_code": "AssertionError: " + code + "_PRIVATE_SUFFIX",
        "leading_space": " AssertionError: " + code,
        "lowercase_exception": "assertionerror: " + code,
        "url": "AssertionError: https://self-owned.invalid/" + code,
        "new_line_before_code": "AssertionError:\n" + code,
        "message_missing": None,
        "body_only": "AssertionError: self-owned-different-assertion",
        "unknown_keycloak": "AssertionError: KEYCLOAK_SELF_OWNED_UNTRUSTED_VALUE",
        "unknown_readiness": "AssertionError: RECOVERY_LAB_READINESS_SELF_OWNED_UNTRUSTED_VALUE",
    }
    failure, published = readiness_failure_report(
        tmp_path, messages[shape], body="AssertionError: " + code + " " + READINESS_PRIVATE_MARKER
    )
    assert "diagnostic_codes" not in failure
    assert "KEYCLOAK_SELF_OWNED_UNTRUSTED_VALUE" not in published
    assert "RECOVERY_LAB_READINESS_SELF_OWNED_UNTRUSTED_VALUE" not in published
    assert code + "_PRIVATE_SUFFIX" not in published


@pytest.mark.parametrize(
    "message",
    [
        "DID NOT RAISE BusinessError",
        "Failed: DID NOT RAISE RuntimeError",
        "Failed: DID NOT RAISE business_app.errors.BusinessError",
        "Failed: DID NOT RAISE <class 'business_app.errors.BusinessError'>",
        "Failed: DID NOT RAISE BusinessError " + READINESS_PRIVATE_MARKER,
        "untrusted-prefix Failed: DID NOT RAISE BusinessError",
    ],
)
def test_readiness_unknown_missing_exception_shapes_remain_failed_without_a_new_reason(tmp_path, message):
    failure, published = readiness_failure_report(tmp_path, message)
    assert "diagnostic_codes" not in failure
    assert READINESS_MISSING_ERROR_CODE not in published


def test_readiness_diagnostic_messages_preserve_the_original_conditions_and_recovery_control_flow():
    import ast
    import hashlib

    fixtures = (
        (
            "tests/identity/test_recovery_live.py",
            "test_restart_and_database_dependency_readiness",
            "beba6652277f1ce9dc174637cdf2c64530c89a417f27206d256a4c02754579e9",
            7,
        ),
        (
            "tests/identity/recovery_lab.py",
            "wait_dependency_down",
            "e2503c902fb236ebfdf7973f1cb010809b295c3dd1b93017d05c94218cb93ac8",
            0,
        ),
    )
    for relative, name, digest, count in fixtures:
        tree = ast.parse((ROOT / relative).read_text(encoding="utf8"))
        function = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == name)
        assertions = [node for node in ast.walk(function) if isinstance(node, ast.Assert)]
        assert len(assertions) == count
        if count:
            assert {node.msg.value for node in assertions if isinstance(node.msg, ast.Constant)} == set(
                READINESS_ASSERT_CODES
            )
        for node in assertions:
            node.msg = None
        normalized = {
            "normalization_version": "python-ast-function-fields-v1",
            "ast": canonical_recovery_ast_fields(function),
        }
        raw = json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode(
            "utf8"
        )
        semantic_digest = hashlib.sha256(raw).hexdigest()
        # Expectations come from original 6c9ab9d9 Git blobs, independently
        # normalized on Python 3.10.22 and 3.13.9. Only Assert.msg and the known
        # new empty FunctionDef.type_params differ; every other field, including
        # None/empty parameter fields, predicates, raises/finally and 45s stays.
        assert semantic_digest == digest

    probe = ast.parse("def self_owned_probe(arg=None, *, keyword=None):\n    pass\n").body[0]
    assert isinstance(probe, ast.FunctionDef)
    original_fields = tuple(name for name in probe._fields if name != "type_params")
    setattr(probe, "_fields", original_fields)
    original = canonical_recovery_ast_fields(probe)
    assert ["returns", None] in original[1]
    assert ["posonlyargs", []] in canonical_recovery_ast_fields(probe.args)[1]
    assert canonical_recovery_ast_fields(None) is None
    assert canonical_recovery_ast_fields([]) == []
    setattr(probe, "_fields", (*original_fields, "type_params"))
    setattr(probe, "type_params", [])
    assert canonical_recovery_ast_fields(probe) == original
    setattr(probe, "type_params", None)
    assert canonical_recovery_ast_fields(probe) != original
    setattr(probe, "type_params", [ast.Name(id="SelfOwnedType", ctx=ast.Load())])
    assert canonical_recovery_ast_fields(probe) != original
    setattr(probe, "_fields", (*original_fields, "self_owned_future_field"))
    setattr(probe, "self_owned_future_field", [])
    assert canonical_recovery_ast_fields(probe) != original


def canonical_recovery_ast_fields(value):
    """Stable fields, not ast.dump defaults; omit only the known empty addition."""
    import ast

    if isinstance(value, ast.AST):
        fields = []
        for name in value._fields:
            if not hasattr(value, name):
                fields.append([name, {"missing_field": True}])
                continue
            item = getattr(value, name)
            if isinstance(value, ast.FunctionDef) and name == "type_params" and type(item) is list and not item:
                continue
            fields.append([name, canonical_recovery_ast_fields(item)])
        return [type(value).__name__, fields]
    if type(value) is list:
        return [canonical_recovery_ast_fields(item) for item in value]
    if value is None or type(value) in (str, int, bool):
        return value
    raise TypeError("UNSUPPORTED_AST_FIELD_TYPE")
