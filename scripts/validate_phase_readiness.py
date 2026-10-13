"""Validate remaining-work classification and candidate flow lineage, not accept it."""
import datetime
import json

from generate_interface_docs import ROOT, digest, read
from generate_phase_readiness import PREFIX, outputs


def main():
    checks, errors = [], []

    def check(name, action):
        try:
            checks.append({"name": name, "status": "PASS", "detail": action()})
        except Exception as exc:
            checks.append({"name": name, "status": "FAIL"})
            errors.append({"name": name, "error": str(exc)})

    def drift():
        derived = outputs()
        for path, text in derived.items():
            assert (ROOT / path).read_bytes() == text.encode(), "READINESS_DOCUMENT_DRIFT:" + path
        mapping = read(PREFIX + "requirement-processing-map.json")
        for path, expected in mapping["source_hashes"].items():
            assert digest(path) == expected, path
        return {"derived_files": len(derived), "source_hashes_match": True}

    check("readiness_views_and_flow_source_hashes_no_drift", drift)

    def lineage():
        trace = read(PREFIX + "requirement-traceability.yaml")["requirements"]
        mapping = read(PREFIX + "requirement-processing-map.json")
        business = [r for r in trace if r["type"] == "functional"]
        assert len(mapping["records"]) == len(business) == 36
        operation_ids = {r["id"] for r in read("docs/03-api/operation-index.json")}
        model_ids = {r["id"] for r in read("docs/06-algorithms/model-catalog.yaml")["models"]}
        source_keys = ["task_ids", "operation_ids", "model_ids", "dataset_ids", "table_names", "test_ids"]
        target_keys = ["declared_task_ids", "declared_operation_ids", "declared_model_ids", "declared_dataset_ids", "declared_table_names", "declared_test_ids"]
        for record in mapping["records"]:
            source = trace[int(record["source_pointer"].rsplit("/", 1)[1])]
            assert (record["requirement_id"], record["name"]) == (source["requirement_id"], source["name"])
            for original, projected in zip(source_keys, target_keys):
                assert source[original] == record[projected], record["requirement_id"] + ":" + original
            assert set(record["candidate_entry_operations"] + record["candidate_result_operations"]) <= operation_ids
            assert set(record["declared_model_ids"]) <= model_ids
            assert len(record["task_card_refs"]) == len(record["declared_task_ids"])
            assert all((ROOT / p).is_file() for p in record["task_card_refs"])
            assert {r["model_id"] for r in record["internal_contract_refs"]} == set(record["declared_model_ids"])
            assert all((ROOT / r[k]).is_file() for r in record["internal_contract_refs"] for k in ["request_schema", "response_schema"])
            assert record["new_HTTP_paths_created"] is False and record["full_business_implementation_asserted"] is False
            assert record["formal_approved"] is False and record["processing_and_reading_note"]
        unbound = [r["requirement_id"] for r in business if not r["operation_ids"]]
        assert mapping["direct_API_unbound_requirements"] == unbound and len(unbound) == 7
        assert len({r["module"] for r in mapping["records"]}) == 12 and mapping["formal_frozen"] is False
        return {"requirements": 36, "modules": 12, "source_API_unbound_kept": 7, "candidate_routes_do_not_rewrite_primary_trace": True}

    check("36_requirement_sources_and_7_unbound_processing_routes", lineage)

    def register():
        ledger = read(PREFIX + "phase-readiness-register.json")
        assert (ledger["original_stage_one_steps"], ledger["original_stage_two_steps"], ledger["source_tasks_preserved"]) == (24, 23, 170)
        assert len(ledger["items"]) == ledger["audit_item_count"] == 19
        assert sum(r["stage"] == 1 for r in ledger["items"]) == 7
        assert sum(r["stage"] == 2 for r in ledger["items"]) == 12
        known_gaps = {r["id"] for r in read("docs/03-api/interface-gap-register.json")["items"]}
        known_gaps.update(r["id"] for r in read("docs/03-development/stage-two-gap-register.json")["items"])
        assert len({r["id"] for r in ledger["items"]}) == 19
        for item in ledger["items"]:
            assert item["original_stage_steps"] and all(1 <= step <= (24 if item["stage"] == 1 else 23) for step in item["original_stage_steps"])
            assert set(item["source_gap_ids"]) <= known_gaps
            assert all((ROOT / path).is_file() for path in item["evidence_refs"]), item["evidence_refs"]
            assert item["signature_only"] is False and item["formal_approved"] is False
            if item["completion_asserted"]:
                assert item["id"] == "S1-N01" and item["technical_supplement_completed"]
                audit = read(PREFIX + "stage-one/visual-layout-audit.json")
                assert audit["all_pages_overview_reviewed"] and audit["total_pages_and_slides"] == 369
                assert len(audit["layout_findings"]) == 8 and audit["original_files_changed"] is False
                assert item["status"] == "COMPLETED_WITH_RECORDED_VISUAL_REVIEW_SCOPE"
            else:
                assert item["completion_asserted"] is False
            assert item["owner_name"] is None and item["remaining_work"] and item["closure_criteria"] and item["phase_boundary"]
        assert ledger["decisions_or_task_states_changed"] is False and ledger["full_business_implementation_is_later_task_scope"] is True
        assert ledger["remaining_non_signature_items"] == sum(not r["completion_asserted"] for r in ledger["items"]) == 18
        return {"non_signature_items_audited": 19, "remaining_items": 18, "stage_one": 7, "stage_two": 12, "all_170_tasks_forced_into_stage_two": False}

    check("19_non_signature_items_and_correct_phase_boundaries", register)

    def observations():
        resource = read(PREFIX + "validation/resource-readiness-snapshot.json")
        governance = read(PREFIX + "validation/repository-governance-snapshot.json")
        assert resource["status"] == "OBSERVED_PROJECT_QUOTAS_UNCONFIRMED" and resource["actual_team_and_exclusive_quotas"] is None
        assert resource["gpu"]["device_absence_asserted"] is False
        assert resource["gpu"]["project_allocation_or_PyTorch_GPU_compatibility_asserted"] is False
        assert resource["services_restarted"] is False and resource["database_rows_read_or_changed"] is False
        assert resource["development_postgres_volume_filesystem"]["all_project_storage_quota_asserted"] is False
        assert governance["status"] == "OBSERVED_CONFIGURATION_NOT_GOVERNANCE_ACCEPTANCE"
        assert governance["rulesets"]["unavailable_does_not_mean_absent"] is True
        assert governance["branch_protection_or_workflows_changed"] is False
        return {"observed_volume_available_bytes": resource["development_postgres_volume_filesystem"]["available_bytes"],
                "provider_branch_protected_observed": governance["branch"]["protected_reported_by_provider"],
                "runtime_or_provider_requeried_by_this_check": False, "quota_or_governance_acceptance_asserted": False}

    check("snapshots_not_inferred_as_quotas_GPU_absence_or_approvals", observations)
    report = {"status": "FAIL" if errors else "PASS", "observed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "scope": "phase_gap_classification_and_requirement_flow_lineage_not_business_or_production_acceptance",
              "checks": checks, "errors": errors, "formal_stage_one_frozen": False, "formal_stage_two_frozen": False,
              "input_observation_hashes": {p: digest(p) for p in [PREFIX + "validation/resource-readiness-snapshot.json", PREFIX + "validation/repository-governance-snapshot.json"]}}
    (ROOT / (PREFIX + "validation/phase-readiness-report.json")).write_bytes((json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode())
    print(json.dumps({"status": report["status"], "checks": len(checks), "errors": errors}, ensure_ascii=False))
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
