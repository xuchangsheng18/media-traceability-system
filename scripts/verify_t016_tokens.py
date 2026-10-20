"""Verify the complete isolated T016 runtime suite, source binding and failure gate."""

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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))
TARGETS = (
    "tests/platform/test_t016.py",
    "tests/platform/test_t016_gate.py",
    "tests/platform/test_t016_permission_catalog.py",
    "tests/business/test_t016_operation_tokens.py",
    "tests/business/test_t016_operation_token_recovery.py",
    "tests/business/test_t016_permission_facts.py",
)
REQUIRED_SOURCE_PATHS = frozenset(
    TARGETS
    + (
        "scripts/verify_t016_tokens.py",
        "scripts/verify_t014_permissions.py",
        "scripts/verify_t015_scope.py",
        "scripts/run_ci.py",
        "config/stage-three-profile.json",
        "config/locks/requirements-py310.lock",
        ".github/workflows/ci.yml",
        "backend/business_app/controls/operation_tokens.py",
        "backend/business_app/controls/providers.py",
        "backend/business_app/controls/approvals.py",
        "backend/business_app/controls/common.py",
        "backend/business_app/controls/router.py",
        "backend/business_app/main.py",
        "backend/business_app/settings.py",
        "backend/business_app/auth.py",
        "backend/business_app/types.py",
        "backend/business_app/db.py",
        "backend/business_app/data_scope.py",
        "backend/business_app/scope_context.py",
        "backend/business_app/scope_collections.py",
        "backend/business_app/scope_lookup.py",
        "backend/business_app/identity/config.py",
        "backend/business_app/identity/directory.py",
        "backend/business_app/identity/runtime.py",
        "backend/business_app/identity/tokens.py",
        "backend/business_app/permissions/object_facts.py",
        "backend/business_app/permissions/conditional.py",
        "backend/business_app/permissions/fence.py",
        "backend/business_app/permissions/context.py",
        "backend/business_app/permissions/duties.py",
        "backend/business_app/permissions/guard.py",
        "backend/business_app/permissions/policy.py",
        "backend/business_app/permissions/role_facts.py",
        "backend/business_app/permissions/rule_types.py",
        "backend/business_app/permissions/six_role.py",
        "backend/business_app/permissions/types.py",
        "backend/business_app/scope_catalog.py",
        "backend/business_migrations/0011_operation_token.sql",
        "docs/03-api/openapi.yaml",
        "docs/04-database/api-field-mapping.csv",
    )
)

# Independent fixed nodeids complement full collection equality: shortening the
# test selection or deleting an existing security category cannot turn the gate green.
REQUIRED_TESTS: dict[str, dict[str, tuple[str, ...] | None]] = {
    "tests.platform.test_t016_permission_catalog": {
        "test_issuance_is_a_fixed_approval_lookup_and_seal_remains_internal": None,
        "test_case_confirmation_requires_complete_sql_and_classification_conditions": None,
        "test_http_claims_must_equal_authoritative_approval_metadata": ("object_id", "object_version", "purpose"),
        "test_http_target_uses_server_case_and_approval_row_version": None,
        "test_http_uuid_claims_compare_canonical_identifiers": None,
        "test_seal_consumer_target_validation_is_exact_without_http_registration": None,
        "test_confirmation_uses_linked_task_sources_and_exact_current_binding": None,
        "test_changed_approval_or_task_never_produces_a_complete_confirmation": (
            "object_version",
            "run_version",
            "result_version",
            "policy_version",
            "purpose",
            "state",
            "owner",
            "task_id",
        ),
        "test_empty_or_invalid_linked_source_does_not_satisfy_confirmation": ("empty", "revoked", "purpose", "expired"),
        "test_confirmation_requires_the_linked_task_source_not_an_approval_source": None,
        "test_supplemental_adapter_cannot_override_confirmation_sql_binding": None,
    },
    "tests.platform.test_t016": {
        "test_invalid_token_ttl_does_not_become_a_successful_rule": ("True", "0", "-1", "1.5", "None", "60"),
        "test_ambiguous_or_unimplemented_actions_cannot_be_signed": (
            "",
            "sealEvidence,createReport",
            "rolloutModel",
            "exportAudit",
            "None",
        ),
        "test_invalid_key_material_is_rejected_before_derivation": ("", "short", "not-bytes", "key3", "None"),
        "test_secret_material_is_not_exposed_by_repr": None,
        "test_only_the_explicit_case_task_seal_mapping_can_resolve": (
            "unknown",
            "model",
            "purpose",
            "organization",
            "missing_rule",
        ),
        "test_credential_is_reconstructable_but_hash_and_identifier_are_not_credentials": None,
        "test_client_cannot_add_scope_action_or_approval_claims": ("case_id", "actor_id", "action", "approved"),
        "test_case_issuance_and_same_transaction_consumption_capability": None,
    },
    "tests.business.test_t016_operation_tokens": {
        "test_issue_replay_is_same_credential_and_never_persists_plaintext": None,
        "test_uuid_spelling_is_canonical_before_binding_and_idempotency": None,
        "test_http_issuance_uses_real_six_role_facts_and_current_source": None,
        "test_missing_provider_never_creates_token": ("rules", "keys", "confirmation_authority"),
        "test_unapproved_or_revoked_chain_cannot_issue": (
            "REQUESTED",
            "REVOKED",
            "RETURNED",
            "REJECTED",
            "INVALIDATED",
        ),
        "test_wrong_database_service_is_denied_before_writes_even_when_caught": None,
        "test_two_connections_compete_for_exactly_one_consumption": None,
        "test_real_fence_concurrent_issuance_does_not_upgrade_shared_task_locks": None,
        "test_idempotent_retry_and_consumer_use_consistent_database_lock_order": None,
        "test_actual_expiry_cannot_be_extended_by_new_request": None,
        "test_restored_database_does_not_revive_old_generation_token": None,
        "test_issue_rejects_request_binding_swap": ("object", "version", "purpose"),
        "test_consume_and_synthetic_business_write_commit_once": None,
        "test_business_failure_rolls_back_consume_and_success_audit": None,
        "test_consume_rejects_binding_key_rule_or_generation_change": (
            "action",
            "object",
            "version",
            "approval",
            "hash",
            "generation",
            "issuance_root",
            "key",
            "rule",
        ),
        "test_commit_time_revalidation_rolls_back_late_change": ("key", "rule", "approval"),
    },
    "tests.business.test_t016_operation_token_recovery": dict.fromkeys(
        (
            "test_v1_nullable_bindings_cannot_bypass_sql_check",
            "test_v1_empty_or_invalid_key_rule_and_generation_are_rejected",
            "test_same_member_of_two_cases_cannot_mix_token_and_approval_scope",
            "test_consumption_cannot_change_credential_reconstruction_bindings",
            "test_expiry_is_measured_at_consumption_after_transaction_start",
            "test_0011_preserves_legacy_rows_and_original_migration_checksums",
            "test_0011_partial_failure_rolls_back_new_columns_and_scope_catalog",
        )
    ),
    "tests.business.test_t016_permission_facts": {
        "test_real_sql_case_confirmation_rechecks_linked_task_and_source_in_same_root": None,
        "test_real_sql_stale_task_or_invalid_approval_cannot_confirm": (
            "row_version",
            "run_version",
            "result_version",
            "policy_version",
            "owner",
            "state",
            "expires_at",
        ),
        "test_real_sql_linked_source_authorization_is_required": ("revoked", "purpose", "expired"),
        "test_real_sql_confirmation_does_not_infer_classification_or_accept_override": None,
        "test_real_sql_two_case_member_cannot_replace_approval_case": None,
        "test_real_sql_commit_fence_rechecks_confirmation_binding_and_rolls_back": ("task_policy", "source_purpose"),
        "test_real_sql_http_object_claims_are_compared_with_approval": ("object_id", "object_version", "purpose"),
    },
    "tests.platform.test_t016_gate": {
        "test_complete_parser_fixture_is_accepted_as_parser_input_only": None,
        "test_permission_catalog_cannot_be_omitted_from_the_runtime_suite": None,
        "test_parser_regression_cannot_be_removed_with_matching_forged_collection": None,
        "test_each_independent_token_security_sentinel_is_required": (
            "tests.platform.test_t016::test_invalid_token_ttl_does_not_become_a_successful_rule[True]",
            "tests.business.test_t016_operation_tokens::test_issue_replay_is_same_credential_and_never_persists_plaintext",
            "tests.business.test_t016_permission_facts::test_real_sql_case_confirmation_rechecks_linked_task_and_source_in_same_root",
            "tests.business.test_t016_permission_facts::test_real_sql_two_case_member_cannot_replace_approval_case",
            "tests.business.test_t016_operation_tokens::test_consume_and_synthetic_business_write_commit_once",
            "tests.business.test_t016_operation_tokens::test_business_failure_rolls_back_consume_and_success_audit",
            "tests.business.test_t016_operation_token_recovery::test_0011_preserves_legacy_rows_and_original_migration_checksums",
            "tests.business.test_t016_operation_token_recovery::test_v1_nullable_bindings_cannot_bypass_sql_check",
            "tests.business.test_t016_operation_token_recovery::test_expiry_is_measured_at_consumption_after_transaction_start",
        ),
        "test_partial_forged_or_stale_runtime_evidence_is_rejected": (
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
        ),
        "test_malformed_or_unsafe_junit_is_rejected_without_raw_output": (
            "empty",
            "duplicate",
            "header",
            "double_status",
            "unsafe_name",
            "nested",
        ),
        "test_unbound_transaction_or_identity_source_cannot_be_accepted": (
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
        ),
        "test_optimized_python_cannot_remove_gate_validation": None,
        "test_independent_failure_probe_is_a_real_failed_pytest_and_safe_json": None,
        "test_engineering_ci_runs_token_gate_and_propagates_failure": ("False", "True"),
    },
}
REQUIRED_CASES = frozenset(
    module + "::" + name + ("[" + value + "]" if value is not None else "")
    for module, tests in REQUIRED_TESTS.items()
    for name, parameters in tests.items()
    for value in (parameters if parameters is not None else (None,))
)
NODE_PATTERN = re.compile(r"[A-Za-z0-9_.:\[\]()/,+-]+")


def parse_junit(path: Path) -> tuple[list[dict[str, str]], dict[str, int]]:
    try:
        root = ET.parse(path).getroot()
        suites = list(root.iter("testsuite"))
        if not suites or any(suite.findall("testsuite") for suite in suites):
            raise ValueError()
        results: list[dict[str, str]] = []
        totals = dict(tests=0, failures=0, errors=0, skipped=0)
        for suite in suites:
            cases = list(suite.findall("testcase"))
            actual = dict(tests=len(cases), failures=0, errors=0, skipped=0)
            for case in cases:
                name = case.attrib["classname"] + "::" + case.attrib["name"]
                if NODE_PATTERN.fullmatch(name) is None:
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
        raise RuntimeError("T016_JUNIT_INVALID") from None


def validate_report(report: dict[str, Any], *, expected_commit: str, expected_source: dict[str, str]) -> None:
    def require(condition: bool) -> None:
        if not condition:
            raise RuntimeError("T016_REQUIRED_EVIDENCE_INVALID")

    try:
        require(report["task_id"] == "T016" and report["status"] == "PASS")
        require(re.fullmatch(r"[0-9a-f]{40}", expected_commit) is not None)
        require(report["source_commit"] == expected_commit and report["source_sha256"] == expected_source)
        require(REQUIRED_SOURCE_PATHS <= set(expected_source))
        require(all(re.fullmatch(r"[0-9a-f]{64}", value) for value in expected_source.values()))
        require(report["source_code_dirty"] is False and report["source_changes"] == [])
        require(report["formal_accepted"] is report["raw_logs_published"] is False)
        require(type(report["pytest_exit_code"]) is int and report["pytest_exit_code"] == 0)
        require(report["targets"] == list(TARGETS))
        cases, collected = report["test_cases"], report["collected_nodeids"]
        require(isinstance(cases, list) and bool(cases) and isinstance(collected, list))
        require(all(set(row) == {"nodeid", "status"} and row["status"] == "passed" for row in cases))
        names = [row["nodeid"] for row in cases]
        require(all(isinstance(name, str) and NODE_PATTERN.fullmatch(name) for name in names))
        require(len(names) == len(set(names)) and REQUIRED_CASES <= set(names))
        require(len(collected) == len(set(collected)) and set(collected) == set(names))
        modules = {name.split("::")[0] for name in names}
        require(modules == {target[:-3].replace("/", ".") for target in TARGETS})
        require(all(type(value) is int for value in report["totals"].values()))
        require(report["totals"] == dict(tests=len(cases), failures=0, errors=0, skipped=0))
        probe = report["failure_probe"]
        require(type(probe["exit_code"]) is int and probe["exit_code"] == 1)
        require(probe["expected_assertion_failure_verified"] is True)
        require(all(type(value) is int for value in probe["totals"].values()))
        require(probe["totals"] == dict(tests=1, failures=1, errors=0, skipped=0))
    except (KeyError, TypeError, ValueError, AttributeError):
        raise RuntimeError("T016_REQUIRED_EVIDENCE_INVALID") from None


def source_context() -> dict[str, Any]:
    from scripts.verify_t014_permissions import source_context as permission_source

    result = permission_source()
    for name in REQUIRED_SOURCE_PATHS:
        result["source_sha256"][name] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    changes = subprocess.check_output(
        ["git", "status", "--porcelain=v1", "-z", "--", "docs/04-database/api-field-mapping.csv"],
        cwd=ROOT,
    )
    result["source_changes"] = sorted(
        set(result["source_changes"]) | {record.decode("utf8")[3:] for record in changes.split(b"\0") if record}
    )
    result["source_code_dirty"] = bool(result["source_changes"])
    return result


def collect_cases(env: dict[str, str]) -> list[str]:
    discovered = sorted(
        path.relative_to(ROOT).as_posix()
        for folder in (ROOT / "tests/business", ROOT / "tests/platform")
        for path in folder.glob("test_t016*.py")
    )
    if discovered != sorted(TARGETS):
        raise RuntimeError("T016_TEST_TARGET_CATALOG_CHANGED")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", *TARGETS, "--collect-only", "-q"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=90,
    )
    if result.returncode != 0:
        raise RuntimeError("T016_COLLECTION_FAILED")
    names = []
    for line in result.stdout.splitlines():
        if line.startswith("tests/") and "::" in line:
            path, name = line.split("::", 1)
            nodeid = path[:-3].replace("/", ".") + "::" + name
            if path not in TARGETS or not path.endswith(".py") or NODE_PATTERN.fullmatch(nodeid) is None:
                raise RuntimeError("T016_COLLECTION_INVALID")
            names.append(nodeid)
    if not names or len(set(names)) != len(names) or not REQUIRED_CASES <= set(names):
        raise RuntimeError("T016_COLLECTION_INCOMPLETE")
    return sorted(names)


def failure_probe(env: dict[str, str], private: Path) -> dict[str, Any]:
    probe = private / "test_t016_expected_failure.py"
    probe.write_text("def test_t016_failure_gate():\n    assert False, 'self-owned failure probe'\n", encoding="utf8")
    configuration = private / "probe.ini"
    configuration.write_text("[pytest]\n", encoding="utf8")
    junit = private / "probe.xml"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-c",
            str(configuration),
            "--rootdir",
            str(private),
            probe.name,
            "-q",
            "--junitxml",
            str(junit),
        ],
        cwd=private,
        env=env,
        capture_output=True,
        timeout=45,
    )
    cases, totals = parse_junit(junit)
    expected = (
        result.returncode == 1
        and totals == dict(tests=1, failures=1, errors=0, skipped=0)
        and cases == [dict(nodeid="test_t016_expected_failure::test_t016_failure_gate", status="failed")]
    )
    return dict(totals=totals, exit_code=result.returncode, expected_assertion_failure_verified=expected)


def run(action: str) -> dict[str, Any]:
    env = dict(os.environ, PYTHONPATH=os.pathsep.join([str(ROOT / "backend"), str(ROOT)]))
    if env.get("PYTEST_ADDOPTS"):
        raise RuntimeError("T016_EXTERNAL_PYTEST_SELECTION_FORBIDDEN")
    with tempfile.TemporaryDirectory(prefix="media-trace-t016-private-") as folder:
        private = Path(folder)
        if action == "failure-probe":
            probe = failure_probe(env, private)
            return dict(status="EXPECTED_FAILURE" if probe["expected_assertion_failure_verified"] else "FAIL", **probe)
        from scripts.verify_business_foundation import configured_environment, validate_target

        before = source_context()
        if before["source_code_dirty"] is not False or before["source_changes"]:
            raise RuntimeError("T016_CLEAN_SOURCE_REQUIRED")
        env = configured_environment()
        validate_target(env)
        report: dict[str, Any] = dict(
            task_id="T016",
            status="FAIL",
            observed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            **before,
            formal_accepted=False,
            raw_logs_published=False,
            shared_migration_or_policy_adopted=False,
            Python_candidates_created=False,
            targets=list(TARGETS),
            collected_nodeids=collect_cases(env),
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
        report["failure_probe"] = failure_probe(env, private)
        if source_context() != before:
            raise RuntimeError("T016_SOURCE_CHANGED_DURING_RUN")
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
        report = dict(task_id="T016", status="FAIL", error="T016_VERIFICATION_FAILED_RAW_DETAILS_WITHHELD")
    report.update(formal_accepted=False, raw_logs_published=False)
    if action == "failure-probe":
        print(json.dumps(report))
        return 1 if report.get("expected_assertion_failure_verified") is True else 2
    path = ROOT / "docs/00-project/validation/t016-operation-token-report.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(json.dumps({key: report[key] for key in ("status", "totals", "task_id") if key in report}))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
