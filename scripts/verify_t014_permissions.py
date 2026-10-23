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
    "tests/business/test_task_creation_http.py",
    "tests/platform/test_t014.py",
    "tests/platform/test_t014_gate.py",
    "tests/business/test_t014_permissions.py",
    "tests/business/test_t014_runtime.py",
    "tests/platform/test_t014_six_role.py",
    "tests/platform/test_t014_work_trust.py",
    "tests/business/test_t014_role_facts.py",
    "tests/business/test_t014_object_rules.py",
    "tests/business/test_t014_indirect_reads.py",
    "tests/business/test_t014_duties.py",
    "tests/business/test_t014_revocation.py",
    "tests/business/test_t014_work.py",
    "tests/business/test_catalog_reads.py",
    "tests/platform/test_permission_catalog_cache.py",
    "tests/platform/test_business_route_registration.py",
    "tests/business/test_registry_projection.py",
    "tests/business/test_registry_reads.py",
    "tests/business/test_report_migration.py",
    "tests/business/test_asset_download.py",
    "tests/platform/test_asset_download_projection.py",
    "tests/business/test_source_registration.py",
    "tests/business/test_source_registration_provider.py",
    "tests/business/test_model_catalog.py",
    "tests/platform/test_model_catalog_projection.py",
    "tests/business/test_resource_registry_migration.py",
    "tests/business/test_migrations.py::test_empty_database_migrates_and_replay_noops",
    "tests/business/test_migrations.py::test_work_role_facts_upgrade_is_atomic_and_function_only",
    "tests/business/test_migrations.py::test_0012_catalog_reads_upgrade_preserves_existing_registries_and_tables",
]
ROLES = json.loads((ROOT / "docs/08-security/access-control-model.json").read_text(encoding="utf8"))["roles"]
REQUIRED_CASES = frozenset(
    [
        (
            "tests.business.test_task_creation_http",
            "test_task_creation_is_mounted_and_refuses_unauthenticated_requests",
        ),
        ("tests.business.test_task_creation_http", "test_http_acceptance_replays_exact_response_and_writes_one_run"),
        ("tests.business.test_asset_download", "test_full_download_verifies_exact_bytes_and_appends_request_audit"),
        ("tests.business.test_source_registration", "test_registration_replay_does_not_insert_or_audit_twice"),
        ("tests.business.test_model_catalog", "test_per_row_visibility_precedes_model_pagination"),
        ("tests.business.test_model_catalog", "test_per_row_evaluation_scope_precedes_pagination"),
        ("tests.business.test_catalog_reads", "test_asset_detail_is_actual_metadata_and_fixed_object_version"),
        ("tests.business.test_catalog_reads", "test_asset_list_reads_current_authorized_database_rows"),
        ("tests.business.test_catalog_reads", "test_task_list_includes_current_task_without_result"),
        ("tests.business.test_registry_reads", "test_report_reads_actual_persisted_metadata_and_evidence"),
        ("tests.business.test_registry_reads", "test_report_reads_exact_registered_object_metadata"),
        ("tests.business.test_registry_reads", "test_report_permission_change_after_projection_is_refused"),
        (
            "tests.platform.test_permission_catalog_cache",
            "test_changed_content_with_unchanged_size_and_mtime_is_revalidated",
        ),
        (
            "tests.platform.test_permission_catalog_cache",
            "test_returned_dictionary_mutation_cannot_change_cached_permissions",
        ),
        (
            "tests.platform.test_t014_six_role",
            "test_catalog_read_adoption_preserves_roles_and_only_approved_query_scope",
        ),
        (
            "tests.business.test_migrations",
            "test_0012_catalog_reads_upgrade_preserves_existing_registries_and_tables",
        ),
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
        ("tests.business.test_t014_runtime", "test_all_52_real_resource_requests_deny_before_business_side_effects"),
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

# Independent confirmed-input names: a shortened pytest selection must not retain
# a green gate after dropping any of the 246 cells or the new work/fence proofs.
RULE_INPUT = json.loads((ROOT / "docs/08-security/t014-six-role-rule-proposal.json").read_text(encoding="utf8"))
ISOLATED_REQUIRED_CASES = frozenset(
    [
        (
            "tests.platform.test_t014_six_role",
            f"test_all_246_cells_match_confirmed_input[{row['permission']}-{role}-{cell['condition_ref']}]",
        )
        for row in RULE_INPUT["permissions"]
        for role, cell in row["cells"].items()
    ]
    + [
        ("tests.platform.test_t014_six_role", "test_nonmatching_role_still_triggers_conflict"),
        ("tests.platform.test_t014_work_trust", "test_noop_work_port_cannot_open_an_unfenced_business_path"),
        ("tests.business.test_t014_role_facts", "test_all_active_roles_include_nonmatching_permission_role"),
        (
            "tests.business.test_t014_object_rules",
            "test_missing_classification_or_authoritative_purpose_is_unavailable",
        ),
        ("tests.business.test_t014_object_rules", "test_policy_list_SQL_scope_and_cursor_follow_current_role_kind"),
        ("tests.business.test_t014_duties", "test_two_subjects_or_two_users_for_same_person_count_once"),
        ("tests.business.test_t014_duties", "test_approval_expiry_at_1800_seconds_is_invalid"),
        ("tests.business.test_t014_duties", "test_real_current_executor_change_invalidates_without_deleting_votes"),
        ("tests.business.test_t014_revocation", "test_revoke_committed_before_fence_blocks_business_commit"),
        ("tests.business.test_t014_revocation", "test_business_commit_before_revoke_is_ordered_and_audited"),
        ("tests.business.test_t014_revocation", "test_actual_restored_database_needs_fresh_independent_generation"),
        ("tests.business.test_t014_work", "test_missing_work_port_rejects_before_broker_or_published_receipt"),
        (
            "tests.business.test_t014_work",
            "test_upload_work_rechecks_live_facts_and_rolls_back_uncommitted_result[terminal_replay]",
        ),
        (
            "tests.business.test_t014_work",
            "test_upload_work_rechecks_live_facts_and_rolls_back_uncommitted_result[service_after_store]",
        ),
        ("tests.business.test_t014_work", "test_node_finish_and_export_delivery_revalidate[node]"),
        ("tests.business.test_t014_work", "test_node_finish_and_export_delivery_revalidate[export]"),
    ]
    + [
        ("tests.business.test_migrations", f"test_work_role_facts_upgrade_is_atomic_and_function_only[{case}]")
        for case in ["False", "True"]
    ]
    + [
        ("tests.business.test_t014_work", f"test_work_directory_rejects_excessive_runtime_privilege[{role}]")
        for role in ["pg_signal_backend", "pg_checkpoint"]
    ]
    + [
        (
            "tests.business.test_t014_revocation",
            f"test_committed_revocation_rejects_new_requests_within_five_seconds[{kind}-{code}]",
        )
        for kind, code in [
            ("identity", 401),
            ("role", 403),
            ("membership", 404),
            ("permission", 403),
            ("policy", 503),
            ("database", 503),
        ]
    ]
)
REQUIRED_CASES = REQUIRED_CASES | ISOLATED_REQUIRED_CASES
REQUIRED_CASES = REQUIRED_CASES | frozenset(
    [
        ("tests.business.test_t014_object_rules", "test_propagation_resolver_uses_canonical_cluster_path"),
        ("tests.business.test_t014_object_rules", "test_exact_trusted_delegation_can_authorize_nonowner[cancelTask]"),
        ("tests.business.test_t014_object_rules", "test_exact_trusted_delegation_can_authorize_nonowner[getApproval]"),
        ("tests.business.test_t014_duties", "test_person_proof_renewal_preserves_live_vote_and_approval_expiry"),
        ("tests.business.test_t014_duties", "test_person_proof_freshness_can_renew_between_bound_reads"),
        ("tests.business.test_t014_revocation", "test_same_generation_proof_renewal_allows_unchanged_transaction"),
        ("tests.business.test_t014_revocation", "test_concurrent_clock_samples_do_not_create_false_rollback"),
        ("tests.business.test_t014_work", "test_upload_longer_than_fact_refresh_rechecks_before_commit[False]"),
        ("tests.business.test_t014_work", "test_upload_longer_than_fact_refresh_rechecks_before_commit[True]"),
        ("tests.business.test_t014_indirect_reads", "test_indirect_read_HTTP_checks_every_source[getImport]"),
        ("tests.business.test_t014_indirect_reads", "test_indirect_read_HTTP_checks_every_source[getReview]"),
        ("tests.business.test_t014_indirect_reads", "test_indirect_read_HTTP_checks_every_source[getFirstSource]"),
        ("tests.business.test_t014_indirect_reads", "test_indirect_read_HTTP_checks_every_source[getPropagation]"),
        (
            "tests.business.test_t014_indirect_reads",
            "test_review_collections_filter_before_pagination_and_allow_empty[listReviews]",
        ),
        (
            "tests.business.test_t014_indirect_reads",
            "test_review_collections_filter_before_pagination_and_allow_empty[listPendingReviews]",
        ),
    ]
)
REQUIRED_CASES = REQUIRED_CASES | frozenset(
    ("tests.platform.test_t014_work_trust", f"test_malformed_work_kind_is_a_registered_denial[kind{index}]")
    for index in range(3)
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
            "unauthenticated": f"test_all_52_mounted_business_operations_require_authentication[{operation}]",
            "permission_denied": f"test_all_52_operations_deny_missing_permission[{operation}]",
            "policy_missing": f"test_all_52_operations_fail_closed_on_missing_or_unavailable_permissions[missing-FORMAL_POLICY_UNCONFIGURED-{operation}]",
            "authority_unavailable": f"test_all_52_operations_fail_closed_on_missing_or_unavailable_permissions[unavailable-IDENTITY_AUTHORITY_UNAVAILABLE-{operation}]",
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
        ROOT / "docs/08-security/t014-six-role-rule-proposal.json",
        ROOT / "docs/08-security/catalog-read-contract-adoption.json",
        ROOT / "docs/08-security/history/t001-t123-catalog-predecessor-openapi.yaml",
        ROOT / "docs/08-security/history/t001-t123-catalog-predecessor-scope-matrix.json",
        ROOT / "config/locks/requirements-py310.lock",
        ROOT / "config/locks/requirements-py311.lock",
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
            "docs/08-security/t014-six-role-rule-proposal.json",
            "docs/08-security/catalog-read-contract-adoption.json",
            "docs/08-security/history/t001-t123-catalog-predecessor-openapi.yaml",
            "docs/08-security/history/t001-t123-catalog-predecessor-scope-matrix.json",
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
            if len(operations) != 52 or len(catalog) != 73 or len(ROLES) != 6:
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
