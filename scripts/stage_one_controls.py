"""Offline first-stage input controls. Never grants live permissions or executes workers."""
import argparse
import hashlib
import json
from pathlib import Path

from generate_interface_docs import ROOT, digest, read
from jsonschema import Draft202012Validator, FormatChecker
from plan_project_schedule import build_plan
from referencing import Registry, Resource


def registry():
    sources = [read(p.relative_to(ROOT).as_posix()) for p in (ROOT / "schemas").rglob("*.schema.json")]
    return Registry().with_resources((s["$id"], Resource.from_contents(s)) for s in sources)


def validate_schema(path, value):
    Draft202012Validator(read(path), registry=registry(), format_checker=FormatChecker()).validate(value)


def validate_dag(value):
    validate_schema("schemas/workflow/dag.schema.json", value)
    nodes = {n["node_id"]: n for n in value["nodes"]}
    assert len(nodes) == len(value["nodes"]), "duplicate node_id"
    models = {m["id"]: m for m in read("docs/06-algorithms/model-catalog.yaml")["models"]}
    pending, ordered = dict(nodes), []
    while pending:
        ready = sorted(nid for nid, n in pending.items() if set(n["dependencies"]) <= set(ordered))
        assert ready, "unknown dependency or cycle"
        for nid in ready:
            node = pending.pop(nid)
            assert (node["missing_policy"] == "FAIL_REQUIRED") == node["required"], "optional policy conflicts with required"
            if node["kind"] == "model":
                assert node["model_id"] in models
                model_id = node["model_id"]
                req = read(f"schemas/model/{model_id}.request.schema.json")
                res = read(f"schemas/model/{model_id}.response.schema.json")
                assert (node["request_schema_id"], node["response_schema_id"]) == (req["$id"], res["$id"])
                assert {r["field_path"] for r in node["input_bindings"]} == set(req["required"])
                assert len(node["input_bindings"]) == len(req["required"])
            else:
                assert node["model_id"] is None
            ordered.append(nid)
    assert sum(n["kind"] == "publish" for n in nodes.values()) == 1
    assert nodes[ordered[-1]]["kind"] == "response", "response must follow all selected projections"
    assert len({e["operation_id"] for e in value["entry_variants"]}) == len(value["entry_variants"])
    return ordered


def active_node_plan(value, operation_id):
    order = validate_dag(value)
    variant = next(v for v in value["entry_variants"] if v["operation_id"] == operation_id)
    nodes = {n["node_id"]: n for n in value["nodes"]}
    selected = [nid for nid in order if variant["mode"] in nodes[nid]["active_entry_modes"]]
    if variant["mode"] in {"READ_ONLY", "CONTROL_TRANSACTION"}:
        assert not any(nodes[nid]["kind"] in {"media", "model", "publish"} for nid in selected)
    return selected


def validate_snapshot(value):
    validate_schema("schemas/workflow/run-result.schema.json", value)
    model_ids = []
    for output in value["capability_outputs"]:
        response = output["response"]
        model_ids.append(output["model_id"])
        assert response["task_id"] == value["binding"]["task_id"] and response["run_version"] == value["binding"]["run_version"]
        assert response["request_id"] == value["request_id"]
        if response["status"] != "SUCCEEDED":
            assert response["payload"] is None and not response["findings"]
        if value["formal_eligibility"] == "formally_authorized":
            assert not response["mock"], "synthetic/mock output cannot qualify for formal acceptance"
    assert len(model_ids) == len(set(model_ids)), "duplicate capability output must be separately versioned"
    return True


def select_snapshot(selector, snapshots, expected_scope, path_task_id=None, path_asset_id=None):
    """Exact version selection on supplied records; caller must supply current trusted scope."""
    properties = {"run_version": {"type": "integer", "minimum": 1}, "result_version": {"type": "integer", "minimum": 1}}
    if path_task_id is None:
        properties["task_id"] = {"type": "string", "format": "uuid"}
    Draft202012Validator({"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False},
                         format_checker=FormatChecker()).validate(selector)
    task_id = path_task_id or selector["task_id"]
    matches = []
    for snapshot in snapshots:
        validate_snapshot(snapshot)
        binding = snapshot["binding"]
        if (binding["task_id"], binding["run_version"], binding["result_version"]) != (task_id, selector["run_version"], selector["result_version"]):
            continue
        assert (binding["org_id"], binding["case_id"]) == (expected_scope["org_id"], expected_scope["case_id"]), "scope denied"
        assert expected_scope["currently_authorized"], "authorization revoked or absent"
        if path_asset_id is not None:
            assert path_asset_id in expected_scope.get("asset_ids_in_selected_snapshot", []), "path asset not in selected result"
        matches.append(snapshot)
    assert len(matches) <= 1, "duplicate published snapshot identity"
    if not matches:
        raise LookupError("exact historical snapshot not found; latest fallback forbidden")
    return matches[0]


def authorize_candidate_action(profile, action, context):
    validate_schema("schemas/controls/business-parameters.schema.json", profile)
    requirements = {
        "report": ["risk_label_version", "review_thresholds", "approval_purposes", "dual_approval_purposes"],
        "export": ["approval_purposes", "dual_approval_purposes"],
        "feedback": ["approval_purposes", "dual_approval_purposes", "feedback_allowed_purposes"],
        "delete": ["retention_days_by_data_class", "legal_hold_policy"],
        "returned": ["returned_mode"],
    }
    assert action in requirements
    reasons = []
    if profile["mode"] != "FORMAL" or not profile["formal_record_ref"]:
        reasons.append("FORMAL_POLICY_NOT_ESTABLISHED")
    for key in requirements[action]:
        if profile["parameters"][key]["status"] != "CONFIRMED":
            reasons.append("PARAMETER_UNCONFIRMED:" + key)
    for key in ["authenticated", "function_permission", "case_scope", "purpose_authorized", "current_authorization", "current_object_version"]:
        if context.get(key) is not True:
            reasons.append("DENIED:" + key)
    if action in {"report", "export", "feedback"}:
        if context.get("current_version_approved") is not True:
            reasons.append("CURRENT_VERSION_APPROVAL_MISSING")
        purposes = profile["parameters"]["approval_purposes"]
        if purposes["status"] == "CONFIRMED" and action not in purposes["value"]:
            reasons.append("PURPOSE_NOT_CONFIGURED")
        dual = profile["parameters"]["dual_approval_purposes"]
        if dual["status"] == "CONFIRMED" and action in dual["value"]:
            approvers = context.get("approver_ids", [])
            if len(set(approvers)) < 2 or context.get("approvers_currently_authorized") is not True:
                reasons.append("INDEPENDENT_CURRENT_TWO_APPROVERS_REQUIRED")
    if action == "feedback":
        if context.get("split") == "sealed_test":
            reasons.append("SEALED_TEST_FEEDBACK_FORBIDDEN")
        purposes = profile["parameters"]["feedback_allowed_purposes"]
        if purposes["status"] != "CONFIRMED" or context.get("feedback_purpose") not in (purposes["value"] or []):
            reasons.append("FEEDBACK_PURPOSE_NOT_AUTHORIZED")
    if action == "delete" and context.get("legal_hold") is not False:
        reasons.append("LEGAL_HOLD_NOT_RELEASED")
    return {"allowed_on_supplied_test_context": not reasons, "reasons": reasons, "live_authorization_granted": False}


def returned_plan(profile, context):
    decision = authorize_candidate_action(profile, "returned", context)
    if decision["reasons"]:
        return dict(decision, transition=None)
    mode = profile["parameters"]["returned_mode"]["value"]
    inputs_changed = context.get("input_or_model_or_policy_changed")
    assert isinstance(inputs_changed, bool)
    if mode == "supplement_same_run" and inputs_changed:
        return dict(decision, allowed_on_supplied_test_context=False, reasons=["RECOMPUTE_REQUIRED"], transition=None)
    recompute = mode == "recompute_new_run" or inputs_changed
    return dict(decision, transition={"state": "QUEUED" if recompute else "WAIT_REVIEW",
                "run_version": context["run_version"] + int(recompute), "result_version": 1 if recompute else context["result_version"] + 1,
                "old_snapshot_immutable": True, "old_approval_inherited": False})


def validate_event_commit(event, current):
    validate_schema("schemas/events/workflow.domain.v1.schema.json", event)
    for key in ["org_id", "case_id", "task_id", "run_version", "policy_version", "dag_version"]:
        assert event["binding"][key] == current[key], "event identity mismatch:" + key
    assert event["fencing_epoch"] == current["fencing_epoch"], "stale fencing"
    if event["node_id"] is not None:
        assert event["node_id"] == current["node_id"] and event["attempt"] == current["attempt"], "wrong node attempt"
    assert current["cancelled"] is False, "late event after cancellation"
    return True


def count_authorized_manifest(manifest):
    """Counts supplied metadata only. No file reads, data copying or training authorization."""
    validate_schema("schemas/dataset/authorized-inventory-manifest.schema.json", manifest)
    assert manifest["authorization_status"] == "verified" and manifest["authorization_record_ref"]
    assert manifest["label_version"] and manifest["quality_protocol_ref"]
    rows = manifest["records"]
    samples, seen_groups = {}, {}
    counts = {k: set() for k in ["original_assets", "derived_assets", "annotations", "content_clusters", "independent_source_groups"]}
    splits = {k: 0 for k in ["train", "validation", "calibration", "sealed_test"]}
    quality_passed = 0
    for row in rows:
        sid = row["sample_id"]
        assert sid not in samples, "duplicate sample_id"
        assert row["split"] in splits
        assert row["authorized_purpose"] in {"training", "validation", "calibration", "holdout", "annotation"}
        assert row["authorized_purpose"] == {"train": "training", "validation": "validation", "calibration": "calibration", "sealed_test": "holdout"}[row["split"]], "split purpose mismatch"
        groups = row["source_group_ids"] + row["person_group_ids"] + row["event_group_ids"]
        assert row["source_group_ids"], "independent source group missing"
        for key in ["source_group_ids", "person_group_ids", "event_group_ids"]:
            for gid in row[key]:
                identity = (key, gid)
                assert identity not in seen_groups or seen_groups[identity] == row["split"], "cross split group leakage"
                seen_groups[identity] = row["split"]
        assert groups
        samples[sid] = row
        splits[row["split"]] += 1
        for field, target in [("original_asset_ids", "original_assets"), ("derived_asset_ids", "derived_assets"),
                              ("annotation_ids", "annotations"), ("source_group_ids", "independent_source_groups")]:
            counts[target].update(row[field])
        if row["cluster_id"] is not None:
            counts["content_clusters"].add(row["cluster_id"])
        quality_passed += row["quality_passed"] is True
    for row in rows:
        for parent in row["parent_sample_ids"]:
            assert parent in samples and samples[parent]["split"] == row["split"], "parent missing or cross-split"
    return {"counts": dict({k: len(v) for k, v in counts.items()}, samples=len(samples), **splits),
            "quality_passed_count": quality_passed, "quality_failed_count": len(samples) - quality_passed,
            "business_release_or_training_authorized": False}


def foundation_preflight():
    profile = read("config/business-parameters.candidate.json")
    validate_schema("schemas/controls/business-parameters.schema.json", profile)
    protocols = read("docs/09-testing/metric-protocols.json")
    protocol_by_id = {m["id"]: m for m in protocols["metrics"]}
    execution_inputs = read("docs/09-testing/acceptance-execution-inputs.json")
    validate_schema("schemas/controls/acceptance-inputs.schema.json", execution_inputs)
    executions = execution_inputs["metrics"]
    assert {m["metric_id"] for m in executions} == set(protocol_by_id) and len(executions) == 24
    required = ["approval_record_ref", "dataset_manifest_sha256", "independent_group_count", "sample_size", "strata_counts",
                "label_or_truth_version", "code_commit", "mapping_version", "resource_snapshot_ref", "load_profile", "repetitions",
                "confidence_interval_method", "executor", "reviewer"]
    metric_rows = []
    for row in executions:
        missing = [key for key in required if not row[key]]
        if row["approved_target"] is None:
            missing.append("approved_target")
        if row["metric_id"].startswith("MP-A") or row["metric_id"] in {"MP-P03", "MP-P04"}:
            for key in ["model_bundle_sha256", "threshold_version"]:
                if row[key] is None:
                    missing.append(key)
        if row["metric_id"] in {"MP-A04", "MP-A05", "MP-A06", "MP-P05"} and row["index_manifest_sha256"] is None:
            missing.append("index_manifest_sha256")
        metric_rows.append({"metric_id": row["metric_id"], "status": "NOT_EVALUABLE" if missing else "READY_FOR_EXECUTION_NOT_A_RESULT",
                            "missing": missing, "real_acceptance_pass_asserted": False})
    inputs = read("docs/00-project/execution-planning-inputs.json")
    plan = build_plan(read("tasks/backlog.yaml")["tasks"], inputs)
    cards = read("docs/07-datasets/actual-input-inventory.json")["business_datasets"]
    for card in cards:
        validate_schema("schemas/controls/data-card.schema.json", card)
    source_register = read("docs/00-project/source-authority-register.json")
    review = read("docs/00-project/stage-one/review-resolution-inputs.json")
    unresolved = [q["question_id"] for q in review["questions"] if q["formal_decision_record_ref"] is None]
    return {"status": "TECHNICAL_CONTROLS_VALIDATED_EXTERNAL_INPUTS_PENDING", "formal_freeze_readiness": "NOT_READY",
            "source_authority_conflicts_pending": [r["document_id"] for r in source_register["documents"] if r["identity_conflict"]],
            "unconfirmed_parameters": [k for k, v in profile["parameters"].items() if v["status"] != "CONFIRMED"],
            "acceptance_metrics": metric_rows, "actual_dataset_cards": len(cards),
            "business_dataset_counts_known": sum(c["counts"]["samples"] is not None for c in cards),
            "actual_calendar_status": plan["actual_capacity_plan"]["status"],
            "actual_calendar_missing": plan["actual_capacity_plan"]["missing_inputs"],
            "placeholder_scenario_available": (ROOT / "docs/00-project/execution-schedule-scenario.json").exists(),
            "placeholder_scenario_is_actual_calendar": False,
            "unresolved_formal_questions": unresolved, "formal_decisions_applied": False, "formal_frozen": False,
            "source_hashes": {p: digest(p) for p in ["config/business-parameters.candidate.json", "docs/09-testing/acceptance-execution-inputs.json",
                      "docs/07-datasets/actual-input-inventory.json", "docs/00-project/execution-planning-inputs.json",
                      "docs/00-project/source-authority-register.json", "docs/00-project/stage-one/review-resolution-inputs.json", "scripts/stage_one_controls.py"]}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-manifest", help="Explicitly provided authorized metadata JSON; emits aggregate counts only")
    args = parser.parse_args()
    if args.dataset_manifest:
        path = Path(args.dataset_manifest)
        value = json.loads(path.read_text(encoding="utf-8"))
        print(json.dumps(dict(count_authorized_manifest(value), input_manifest_sha256=hashlib.sha256(path.read_bytes()).hexdigest()), ensure_ascii=False))
    else:
        report = foundation_preflight()
        (ROOT / "docs/00-project/validation/stage-one-input-preflight-report.json").write_bytes((json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode())
        print(json.dumps({"status": report["status"], "formal_freeze_readiness": report["formal_freeze_readiness"],
                          "unconfirmed_parameters": len(report["unconfirmed_parameters"]), "unknown_business_data_cards": report["actual_dataset_cards"] - report["business_dataset_counts_known"],
                          "actual_calendar_status": report["actual_calendar_status"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
