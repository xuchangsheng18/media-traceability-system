"""Test first-stage engineering controls and unknown-input boundaries on synthetic data."""
import copy
import json

from generate_interface_docs import ROOT, digest, read
from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from plan_placeholder_schedule import outputs as placeholder_outputs
from stage_one_controls import (
    active_node_plan,
    authorize_candidate_action,
    count_authorized_manifest,
    foundation_preflight,
    returned_plan,
    select_snapshot,
    validate_dag,
    validate_event_commit,
    validate_schema,
    validate_snapshot,
)


def rejects(action):
    try:
        action()
    except (AssertionError, ValidationError, LookupError):
        return True
    raise AssertionError("invalid case unexpectedly accepted")


def main():
    checks, errors = [], []

    def check(name, action):
        try:
            checks.append({"name": name, "status": "PASS", "detail": action()})
        except Exception as exc:
            checks.append({"name": name, "status": "FAIL"})
            errors.append({"name": name, "error": str(exc)})

    def sources():
        register = read("docs/00-project/source-authority-register.json")
        inventory = read("docs/00-project/source-inventory.json")
        assert len(register["documents"]) == len(inventory) == 10
        assert register["source_inventory_sha256"] == digest("docs/00-project/source-inventory.json")
        for row in register["documents"]:
            original = inventory[int(row["inventory_pointer"].lstrip("/"))]
            assert row["sha256"] == original["sha256"] == digest(row["path"])
            assert row["official_authority_confirmed"] is False and row["authority_record_ref"] is None
        assert sum(r["identity_conflict"] for r in register["documents"]) == 2
        assert len({r["domain"] for r in register["technical_authorities"]}) == 13
        assert all((ROOT / r["path"]).exists() and r["owner_name"] is None for r in register["technical_authorities"])
        return {"protected_sources": 10, "version_conflicts_explicit": 2, "structural_authorities": 13}

    check("source_identity_precedence_and_originals", sources)

    candidate = read("config/business-parameters.candidate.json")
    context = {k: True for k in ["authenticated", "function_permission", "case_scope", "purpose_authorized", "current_authorization",
                                "current_object_version", "current_version_approved", "approvers_currently_authorized"]}
    confirmed = copy.deepcopy(candidate)
    confirmed.update(mode="FORMAL", formal_record_ref="synthetic-test-policy-not-real-approval")
    values = {"risk_label_version": "synthetic-v1", "review_thresholds": {"synthetic": .5}, "approval_purposes": ["report", "export", "feedback"],
              "dual_approval_purposes": ["report", "export"], "feedback_allowed_purposes": ["training"], "returned_mode": "reason_selected"}
    for key, value in values.items():
        confirmed["parameters"][key] = {"status": "CONFIRMED", "value": value, "record_ref": "synthetic-only", "version": "test-1"}

    def policy():
        validate_schema("schemas/controls/business-parameters.schema.json", candidate)
        assert len(candidate["parameters"]) == 14
        assert all(not authorize_candidate_action(candidate, a, context)["allowed_on_supplied_test_context"] for a in ["report", "export", "feedback", "delete", "returned"])
        good = dict(context, approver_ids=["synthetic-reviewer-1", "synthetic-reviewer-2"])
        assert authorize_candidate_action(confirmed, "report", good)["allowed_on_supplied_test_context"]
        for field in ["case_scope", "current_authorization", "current_object_version", "current_version_approved"]:
            assert not authorize_candidate_action(confirmed, "report", dict(good, **{field: False}))["allowed_on_supplied_test_context"]
        assert not authorize_candidate_action(confirmed, "report", dict(good, approver_ids=["same", "same"]))["allowed_on_supplied_test_context"]
        assert not authorize_candidate_action(confirmed, "feedback", dict(good, split="sealed_test", feedback_purpose="training"))["allowed_on_supplied_test_context"]
        invalid = copy.deepcopy(confirmed)
        invalid["parameters"]["review_thresholds"]["value"] = {"synthetic": 1.1}
        rejects(lambda: validate_schema("schemas/controls/business-parameters.schema.json", invalid))
        invalid = copy.deepcopy(candidate)
        invalid["parameters"]["retention_days_by_data_class"]["value"] = {"evidence": 365}
        rejects(lambda: validate_schema("schemas/controls/business-parameters.schema.json", invalid))
        assert not authorize_candidate_action(confirmed, "delete", dict(good, legal_hold=True))["allowed_on_supplied_test_context"]
        return {"parameter_slots": 14, "unknown_revoked_scope_same_person_holdout_and_illegal_value_rejections": "PASS", "live_permission_granted": False}

    check("business_rule_config_and_fail_closed_actions", policy)

    def returned():
        unchanged = returned_plan(confirmed, dict(context, input_or_model_or_policy_changed=False, run_version=2, result_version=3))
        changed = returned_plan(confirmed, dict(context, input_or_model_or_policy_changed=True, run_version=2, result_version=3))
        assert unchanged["transition"] == {"state": "WAIT_REVIEW", "run_version": 2, "result_version": 4, "old_snapshot_immutable": True, "old_approval_inherited": False}
        assert changed["transition"] == {"state": "QUEUED", "run_version": 3, "result_version": 1, "old_snapshot_immutable": True, "old_approval_inherited": False}
        assert returned_plan(candidate, context)["transition"] is None
        return {"supplement_and_recompute_versions": "PASS", "unknown_mode_denied": True, "real_task_state_changed": False}

    check("returned_two_paths_and_no_approval_inheritance", returned)

    snapshot = read("tests/fixtures/stage-one-controls.json")["snapshot"]

    def workflow():
        index = read("docs/05-workflows/dag-index.json")
        source = {r["requirement_id"]: r for r in read("docs/00-project/requirement-traceability.yaml")["requirements"] if r["type"] == "functional"}
        assert set(index["requirements"]) == set(source) and len(index["paths"]) == 36
        for rid, path in index["paths"].items():
            dag = read(path)
            assert dag["source_task_ids"] == source[rid]["task_ids"]
            assert [n["model_id"] for n in dag["nodes"] if n["kind"] == "model"] == source[rid]["model_ids"]
            validate_dag(dag)
            for entry in dag["entry_variants"]:
                active_node_plan(dag, entry["operation_id"])
        sample = read(next(iter(index["paths"].values())))
        bad = copy.deepcopy(sample)
        bad["nodes"][0]["dependencies"] = [bad["nodes"][-1]["node_id"]]
        rejects(lambda: validate_dag(bad))
        bad = copy.deepcopy(sample)
        bad["nodes"].append(copy.deepcopy(bad["nodes"][0]))
        rejects(lambda: validate_dag(bad))
        validate_snapshot(snapshot)
        bad = copy.deepcopy(snapshot)
        bad["capability_outputs"][0]["model_id"] = "M02"
        rejects(lambda: validate_snapshot(bad))
        bad = copy.deepcopy(snapshot)
        bad["capability_outputs"][0]["response"]["run_version"] += 1
        rejects(lambda: validate_snapshot(bad))
        bad = copy.deepcopy(snapshot)
        bad["formal_eligibility"] = "formally_authorized"
        bad["capability_outputs"][0]["response"]["mock"] = True
        rejects(lambda: validate_snapshot(bad))
        projection = read("docs/06-algorithms/capability-projection-register.json")["records"]
        assert len(projection) == 34
        for row in projection:
            assert row["response_sha256"] == digest(row["response_schema"])
            assert row["request_sha256"] == digest(row["request_schema"])
            assert row["raw_persistence_column"] in read("docs/04-database/table-catalog.json")[row["raw_persistence_table"]]["columns"]
        return {"requirement_dags": 36, "typed_model_branches": 34, "cycle_duplicate_wrong_capability_old_run_mock_rejections": "PASS", "live_workers_implemented": False}

    check("36_DAGs_34_model_response_snapshots_and_projection_sources", workflow)

    def historical():
        spec = read("docs/03-api/openapi.yaml")
        history = [o for methods in spec["paths"].values() for o in methods.values() if isinstance(o, dict) and "x-history-read-contract" in o]
        assert len(history) == 7
        for operation in history:
            parameter = next(p for p in operation["parameters"] if p["name"] == "history")
            assert parameter["style"] == "deepObject" and set(parameter["schema"]["required"]) == set(parameter["schema"]["properties"])
            assert operation["x-history-read-contract"]["fallback_to_latest"] is False
            Draft202012Validator(parameter["schema"], format_checker=FormatChecker()).validate(
                {"run_version": 1, "result_version": 1, **({"task_id": snapshot["binding"]["task_id"]} if "task_id" in parameter["schema"]["properties"] else {})})
            rejects(lambda: Draft202012Validator(parameter["schema"]).validate({"run_version": 1}))
        binding = snapshot["binding"]
        scope = dict(org_id=binding["org_id"], case_id=binding["case_id"], currently_authorized=True)
        selector = {"run_version": binding["run_version"], "result_version": binding["result_version"]}
        assert select_snapshot(selector, [snapshot], scope, binding["task_id"]) is snapshot
        rejects(lambda: select_snapshot(dict(selector, result_version=99), [snapshot], scope, binding["task_id"]))
        rejects(lambda: select_snapshot(selector, [snapshot], dict(scope, case_id="00000000-0000-4000-8000-000000000001"), binding["task_id"]))
        rejects(lambda: select_snapshot(selector, [snapshot], dict(scope, currently_authorized=False), binding["task_id"]))
        rejects(lambda: select_snapshot(selector, [snapshot, snapshot], scope, binding["task_id"]))
        event = read("tests/fixtures/stage-one-controls.json")["event"]
        current = dict(event["binding"], node_id=event["node_id"], attempt=event["attempt"], fencing_epoch=event["fencing_epoch"], cancelled=False)
        validate_event_commit(event, current)
        rejects(lambda: validate_event_commit(event, dict(current, fencing_epoch=99)))
        rejects(lambda: validate_event_commit(event, dict(current, cancelled=True)))
        bad = copy.deepcopy(event)
        bad["producer_role"] = "review_service"
        rejects(lambda: validate_event_commit(bad, current))
        return {"existing_history_read_operations": 7, "exact_version_scope_revocation_and_stale_fence_checks": "PASS", "new_HTTP_routes": 0}

    check("historical_read_parameter_groups_exact_scope_and_event_fencing", historical)

    def data():
        inventory = read("docs/07-datasets/actual-input-inventory.json")
        assert len(inventory["business_datasets"]) == 15 and inventory["all_actual_business_counts_unknown"]
        for card in inventory["business_datasets"]:
            assert card == read("docs/07-datasets/data-cards/" + card["dataset_id"] + ".json")
            assert card["catalog_sha256"] == digest(card["catalog_ref"])
            assert all(v is None for v in card["counts"].values()) and card["authorization_status"] == "pending"
        assert inventory["synthetic_evidence"]["samples"] == 64 and inventory["synthetic_evidence"]["business_training_or_acceptance_samples"] is False
        manifest = read("tests/fixtures/stage-one-controls.json")["dataset_manifest"]
        counted = count_authorized_manifest(manifest)
        assert counted["counts"]["samples"] == 3 and counted["counts"]["original_assets"] == 2
        assert counted["counts"]["derived_assets"] == 1 and counted["counts"]["sealed_test"] == 1
        bad = copy.deepcopy(manifest)
        bad["records"][1]["split"] = "validation"
        rejects(lambda: count_authorized_manifest(bad))
        bad = copy.deepcopy(manifest)
        bad["records"][2]["authorized_purpose"] = "training"
        rejects(lambda: count_authorized_manifest(bad))
        bad = copy.deepcopy(manifest)
        bad["records"].append(copy.deepcopy(bad["records"][0]))
        rejects(lambda: count_authorized_manifest(bad))
        bad = copy.deepcopy(manifest)
        bad["authorization_status"] = "pending"
        rejects(lambda: count_authorized_manifest(bad))
        return {"unknown_real_dataset_cards": 15, "synthetic_samples_separate": 64, "dedup_and_cross_split_holdout_rejections": "PASS", "real_samples_scanned": False}

    check("15_real_data_cards_aggregate_counting_and_no_leakage", data)

    def preflight():
        report = foundation_preflight()
        assert report["formal_freeze_readiness"] == "NOT_READY" and not report["formal_frozen"]
        assert len(report["unconfirmed_parameters"]) == 14
        assert len(report["acceptance_metrics"]) == 24 and all(r["status"] == "NOT_EVALUABLE" for r in report["acceptance_metrics"])
        assert len(report["unresolved_formal_questions"]) == 33 and report["business_dataset_counts_known"] == 0
        assert report["actual_calendar_status"] == "NOT_COMPUTABLE_ACTUAL_INPUTS_MISSING"
        assert "视觉版式未核验" not in (ROOT / "docs/00-project/freeze-checklist.md").read_text(encoding="utf-8")
        assert read("docs/00-project/review-decisions.yaml")["decisions"] == []
        assert len(read("docs/00-project/stage-one/review-resolution-inputs.json")["questions"]) == 33
        return {"metric_configs": 24, "review_input_rows": 33, "actual_calendar_or_formal_approval_invented": False, "freeze_status_text_corrected": True}

    check("formal_input_preflight_review_decisions_and_status_consistency", preflight)

    def placeholder():
        for path, content in placeholder_outputs().items():
            assert (ROOT / path).read_bytes() == content.encode(), path
        scenario = read("docs/00-project/execution-schedule-scenario.json")
        actual = read("docs/00-project/execution-planning-inputs.json")
        assert len(scenario["records"]) == 170 and scenario["actual_people_confirmed"] is False
        assert scenario["all_calendar_dates_assumed"] and scenario["scenario_capacity_plan"]["calendar_commitment_asserted"] is False
        assert actual["resources"] == [] and actual["actual_plan_start_date"] is None
        assert all(r["scenario_resource_name"].startswith("占位") and r["actual_start"] is None for r in scenario["records"])
        audit = read("docs/01-requirements/business-parameter-source-audit.json")
        assert len(audit["parameter_reviews"]) == 14 and audit["formal_parameters_approved"] is False
        for row in audit["parameter_reviews"]:
            lines = (ROOT / row["source"]).read_text(encoding="utf-8").splitlines()
            assert row["exact_source_lines"]
            assert all(lines[p["line"] - 1] == p["text"] for p in row["exact_source_lines"])
        return {"scenario_tasks": 170, "placeholder_resources": 10, "actual_people_or_dates_written": False,
                "source_parameter_line_reviews": 14, "source_target_month_conflict_visible": scenario["exceeds_source_target_month_under_assumptions"]}

    check("user_requested_placeholder_scenario_and_14_actual_source_reviews", placeholder)
    report = {"status": "FAIL" if errors else "PASS", "scope": "first_stage_engineering_controls_on_synthetic_fixtures_no_live_business_or_formal_approval",
              "checks": checks, "errors": errors, "source_originals_modified": False, "real_data_read_or_trained": False,
              "business_API_or_workers_implemented": False, "formal_frozen": False, "source_hashes": {p: digest(p) for p in [
                  "scripts/stage_one_controls.py", "scripts/validate_stage_one_controls.py", "tests/fixtures/stage-one-controls.json"]}}
    (ROOT / "docs/00-project/validation/stage-one-controls-report.json").write_bytes((json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode())
    print(json.dumps({"status": report["status"], "checks": len(checks), "errors": errors}, ensure_ascii=False))
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
