"""The CI parser must reject missing, duplicate, skipped and failed proof rows."""

import hashlib
import importlib
import json
import subprocess
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
            f"test_all_46_mounted_business_operations_require_authentication[{operation}]",
            f"test_all_46_operations_deny_missing_permission[{operation}]",
            f"test_all_46_operations_fail_closed_on_missing_or_unavailable_permissions[missing-FORMAL_POLICY_UNCONFIGURED-{operation}]",
            f"test_all_46_operations_fail_closed_on_missing_or_unavailable_permissions[unavailable-IDENTITY_AUTHORITY_UNAVAILABLE-{operation}]",
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


def test_complete_report_has_exact_46_operation_matrix(tmp_path):
    gate = gate_module()
    result = gate.validate_results(synthetic_report(tmp_path, gate), OPERATIONS)
    assert result["mounted_operation_count"] == 46
    assert set(result["operation_checks"]) == OPERATIONS


@pytest.mark.parametrize(
    "name",
    [
        "test_asset_detail_is_actual_metadata_and_fixed_object_version",
        "test_asset_list_reads_current_authorized_database_rows",
        "test_task_list_includes_current_task_without_result",
    ],
)
def test_gate_requires_catalog_read_positive_evidence(tmp_path, name):
    gate = gate_module()
    path = synthetic_report(tmp_path, gate, missing=("tests.business.test_catalog_reads", name))
    with pytest.raises(RuntimeError, match="T014_REQUIRED_REGRESSION_MISSING"):
        gate.validate_results(path, OPERATIONS)


def test_gate_source_context_binds_confirmed_six_role_input():
    path = "docs/08-security/t014-six-role-rule-proposal.json"
    actual = gate_module().source_context()
    expected = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
    assert actual["source_sha256"].get(path) == expected


@pytest.mark.parametrize(
    "path",
    [
        "docs/08-security/catalog-read-contract-adoption.json",
        "docs/08-security/history/t001-t123-catalog-predecessor-openapi.yaml",
        "docs/08-security/history/t001-t123-catalog-predecessor-scope-matrix.json",
    ],
)
def test_source_context_detects_uncommitted_catalog_adoption_evidence(monkeypatch, path):
    gate = gate_module()
    types = importlib.import_module("scripts.stage_three_types")
    monkeypatch.setattr(types, "source_tree_state", lambda root: {"source_code_dirty": False, "source_changes": []})

    def output(command, **kwargs):
        if command[:3] == ["git", "rev-parse", "HEAD"]:
            return "1" * 40
        assert command[:3] == ["git", "status", "--porcelain"]
        return " M " + path + "\n" if path in command else ""

    monkeypatch.setattr(gate.subprocess, "check_output", output)
    result = gate.source_context()
    assert result["source_code_dirty"] is True
    assert result["source_changes"] == [path]


@pytest.mark.parametrize(
    "classname,name",
    [
        (
            "tests.platform.test_t014_six_role",
            "test_all_246_cells_match_confirmed_input[asset.upload-data_admin-INGEST]",
        ),
        ("tests.platform.test_t014_six_role", "test_nonmatching_role_still_triggers_conflict"),
        ("tests.platform.test_t014_work_trust", "test_noop_work_port_cannot_open_an_unfenced_business_path"),
        ("tests.business.test_t014_role_facts", "test_all_active_roles_include_nonmatching_permission_role"),
        (
            "tests.business.test_t014_object_rules",
            "test_missing_classification_or_authoritative_purpose_is_unavailable",
        ),
        ("tests.business.test_t014_duties", "test_two_subjects_or_two_users_for_same_person_count_once"),
        ("tests.business.test_t014_duties", "test_approval_expiry_at_1800_seconds_is_invalid"),
        ("tests.business.test_t014_revocation", "test_revoke_committed_before_fence_blocks_business_commit"),
        ("tests.business.test_t014_revocation", "test_actual_restored_database_needs_fresh_independent_generation"),
        (
            "tests.business.test_t014_revocation",
            "test_committed_revocation_rejects_new_requests_within_five_seconds[identity-401]",
        ),
        ("tests.business.test_t014_work", "test_missing_work_port_rejects_before_broker_or_published_receipt"),
        (
            "tests.business.test_t014_work",
            "test_upload_work_rechecks_live_facts_and_rolls_back_uncommitted_result[terminal_replay]",
        ),
        ("tests.business.test_t014_work", "test_node_finish_and_export_delivery_revalidate[export]"),
        ("tests.business.test_migrations", "test_work_role_facts_upgrade_is_atomic_and_function_only[True]"),
    ],
)
def test_gate_rejects_report_missing_new_rule_or_work_evidence(tmp_path, classname, name):
    gate = gate_module()
    path = synthetic_report(tmp_path, gate, missing=(classname, name))
    with pytest.raises(RuntimeError, match="T014_REQUIRED_REGRESSION_MISSING"):
        gate.validate_results(path, OPERATIONS)


@pytest.mark.parametrize(
    "classname,name",
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
    ],
)
def test_gate_requires_review_regressions(tmp_path, classname, name):
    gate = gate_module()
    path = synthetic_report(tmp_path, gate, missing=(classname, name))
    with pytest.raises(RuntimeError, match="T014_REQUIRED_REGRESSION_MISSING"):
        gate.validate_results(path, OPERATIONS)


@pytest.mark.parametrize(
    "kind", ["missing_operation", "duplicate_operation", "missing_SQL_restore", "missing_real_resources"]
)
def test_gate_rejects_incomplete_or_duplicate_runtime_evidence(tmp_path, kind):
    gate = gate_module()
    operation = sorted(OPERATIONS)[0]
    target = ("tests.platform.test_t014", f"test_all_46_operations_deny_missing_permission[{operation}]")
    missing = {
        "missing_operation": target,
        "missing_SQL_restore": (
            "tests.business.test_t014_permissions",
            "test_permission_facts_and_least_privilege_survive_independent_restore",
        ),
        "missing_real_resources": (
            "tests.business.test_t014_runtime",
            "test_all_46_real_resource_requests_deny_before_business_side_effects",
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


@pytest.mark.parametrize(
    "changed,dirty",
    [
        ("config/locks/runtime-archive.json", False),
        ("config/locks/requirements-py310.lock", True),
        ("docs/03-api/openapi.yaml", True),
        ("docs/08-security/t014-six-role-rule-proposal.json", True),
        ("docs/08-security/catalog-read-contract-adoption.json", True),
        ("docs/08-security/history/t001-t123-catalog-predecessor-openapi.yaml", True),
        ("docs/08-security/history/t001-t123-catalog-predecessor-scope-matrix.json", True),
        ("backend/business_app/permissions/guard.py", True),
    ],
)
def test_source_binding_distinguishes_generated_archive_from_actual_changes(tmp_path, monkeypatch, changed, dirty):
    gate = gate_module()
    files = [
        "scripts/verify_t014_permissions.py",
        "config/locks/runtime-archive.json",
        "config/locks/requirements-py310.lock",
        "docs/03-api/openapi.yaml",
        "docs/08-security/access-control-model.json",
        "docs/08-security/t014-interface-scope-matrix.json",
        "docs/08-security/t014-six-role-rule-proposal.json",
        "docs/08-security/catalog-read-contract-adoption.json",
        "docs/08-security/history/t001-t123-catalog-predecessor-openapi.yaml",
        "docs/08-security/history/t001-t123-catalog-predecessor-scope-matrix.json",
        "backend/business_app/permissions/guard.py",
    ]
    for name in files:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture original\n")
    for args in [
        ["init", "--quiet"],
        ["add", "."],
        ["-c", "user.name=Fixture", "-c", "user.email=fixture@example.test", "commit", "--quiet", "-m", "fixture"],
    ]:
        subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / changed).write_text("fixture changed\n")
    monkeypatch.setattr(gate, "ROOT", tmp_path)
    result = gate.source_context()
    assert result["source_code_dirty"] is dirty
    if not dirty:
        assert result["build_metadata_changes"] == [changed]
