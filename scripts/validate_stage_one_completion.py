"""Verify this four-item supplement and contract fix without inventing actual approvals."""
import copy
import json
import re

from evaluate_acceptance_metrics import latency, self_test
from generate_interface_docs import ROOT, digest, read
from jsonschema import Draft202012Validator, FormatChecker
from plan_project_schedule import build_plan
from plan_project_schedule import outputs as schedule_outputs


def main():
    checks, errors = [], []

    def check(name, action):
        try:
            detail = action()
            checks.append({"name": name, "status": "PASS", "detail": detail})
        except Exception as exc:
            checks.append({"name": name, "status": "FAIL"})
            errors.append({"name": name, "error": str(exc)})

    def visual():
        audit = read("docs/00-project/stage-one/visual-layout-audit.json")
        originals = {r["path"]: r["sha256"] for r in read("docs/00-project/source-inventory.json")}
        assert len(audit["documents"]) == 10 and audit["word_pages"] == 357 and audit["powerpoint_slides"] == 12
        assert audit["all_pages_overview_reviewed"] and audit["comments_visual_review_asserted"] is False
        assert audit["shipping_all_pages_at_100_percent_asserted"] is False
        assert set(originals) == {r["source"] for r in audit["documents"]}
        for record in audit["documents"]:
            assert record["source_sha256"] == originals[record["source"]] == digest(record["source"])
            assert len(record["pages"]) == record["page_count"]
            assert record["overview_reviewed_pages"] == list(range(1, record["page_count"] + 1))
            assert record["original_saved"] is False and re.fullmatch(r"[a-f0-9]{64}", record["pdf_sha256"])
            assert all(re.fullmatch(r"[a-f0-9]{64}", page["png_sha256"]) for page in record["pages"])
        assert audit["layout_findings"] and all(f["disposition"] and f["repository_refs"] for f in audit["layout_findings"])
        return {"source_documents": 10, "word_pages": 357, "slides": 12,
                "original_hashes_unchanged": True, "CI_re_rendered_Word_or_manually_reviewed_images": False}

    check("actual_visual_review_record_and_unchanged_originals", visual)

    def semantic():
        review = read("docs/00-project/requirement-semantic-review.json")
        proposals = read("docs/00-project/requirement-flow-proposals.json")
        business = {r["requirement_id"]: r for r in read("docs/00-project/requirement-traceability.yaml")["requirements"] if r["type"] == "functional"}
        assert len(review["records"]) == review["reviewed_requirements"] == len(business) == 36
        for row in review["records"]:
            source = business[row["requirement_id"]]
            proposal = proposals["overrides"][row["requirement_id"]]
            assert row["source_acceptance"] == source["acceptance"]
            assert row["reviewed_source_tasks"] == source["task_ids"] and row["reviewed_models"] == source["model_ids"]
            assert row["technical_review_completed"] and not row["business_approved"] and not row["runtime_verification_completed"]
            assert row["entry_operations"] == proposal["entry_operations"] and row["result_operations"] == proposal["result_operations"]
            assert row["result_identity"] and row["review_conclusion"]
        assert proposals["overrides"]["FR-CLAIM-001"]["result_operations"] == ["extractClaims"]
        assert proposals["overrides"]["FR-CLAIM-002"]["result_operations"] == ["verifyClaim"]
        assert "searchImage" not in proposals["overrides"]["FR-RESOURCE-001"]["entry_operations"]
        assert proposals["overrides"]["FR-ORIGIN-001"]["result_operations"] == []
        assert not {"cancelTask", "rerunTask"} & set(proposals["overrides"]["FR-OPS-002"]["entry_operations"])
        for path, expected in review["source_hashes"].items():
            assert digest(path) == expected, path
        return {"reviewed_requirements": 36, "specific_flow_corrections_checked": 5, "formal_business_approval": False}

    check("36_semantic_reviews_and_specific_wrong_route_corrections", semantic)

    def metrics():
        protocols = read("docs/09-testing/metric-protocols.json")
        assert len(protocols["metrics"]) == protocols["metric_count"] == 24
        assert not protocols["common"]["approved"]
        for path, expected_hash in protocols["source_hashes"].items():
            assert digest(path) == expected_hash, path
        expected = {"MP-A01": .95, "MP-A02": .85, "MP-A03": .85, "MP-A04": .95, "MP-A05": .90,
                    "MP-A06": .90, "MP-A07": 1., "MP-A08": .70, "MP-A09": .90, "MP-A10": .90, "MP-A11": 1.,
                    "MP-P01": 20, "MP-P02": 100, "MP-P03": 2000, "MP-P04": 10000, "MP-P05": 2000, "MP-D01": 200000}
        for record in protocols["metrics"]:
            assert record["approved_target"] is None and record["sample_size"] is None
            assert record["result_status"] == "NOT_EXECUTED_ON_REAL_ACCEPTANCE_DATA"
            assert all(record[k] for k in ["statistical_unit_and_denominator", "formula", "failure_unknown_zero_handling", "required_strata", "source_clause"])
            if record["id"] in expected:
                assert record["source_target"] == expected[record["id"]]
        self_test()
        report = read("docs/00-project/validation/acceptance-metric-reference-report.json")
        assert report["status"] == "PASS" and len(report["checks"]) == 8 and not report["formal_business_acceptance"]
        for invalid_seconds in [0, -1, float("inf")]:
            try:
                latency({"measurement_seconds": invalid_seconds, "requests": []})
            except AssertionError:
                pass
            else:
                raise AssertionError("invalid observation window accepted")
        return {"protocols": 24, "formula_reference_checks": 8, "invalid_observation_windows_rejected": 3, "actual_model_or_performance_verdict": False}

    check("24_metric_protocols_source_targets_and_8_failure_counting_fixtures", metrics)

    def schedule():
        for path, content in schedule_outputs().items():
            assert (ROOT / path).read_bytes() == content.encode(), path
        plan = read("docs/00-project/execution-schedule.json")
        assert plan["totals"]["tasks"] == 170
        assert (plan["totals"]["source_effort_low_person_days"], plan["totals"]["source_effort_high_person_days"]) == (397, 491)
        assert plan["actual_capacity_plan"]["calendar_commitment_asserted"] is False
        assert not plan["source_task_states_changed"] and plan["original_scope_modules"] == 12
        ledger = read("tasks/execution-status.json")
        partial_ids = {r["task_id"] for r in ledger["tasks"] if r["status"] == "PARTIAL_VERIFIED_SCOPE"}
        assert len(partial_ids) == 50
        assert plan["totals"]["full_tasks_verified"] == 0 and plan["totals"]["partial_scope_tasks"] == len(partial_ids)
        assert {r["task_id"] for r in plan["records"] if r["observed_verification_status"] == "PARTIAL_VERIFIED_SCOPE"} == partial_ids
        assert all(r["capacity_plan_start_date"] is None and r["capacity_plan_finish_date"] is None for r in plan["records"])
        tasks = [{"id": "T001", "name": "synthetic A", "source_role": "test", "status": "synthetic", "source_effort": "1～2人日", "execution_dependencies_candidate": []},
                 {"id": "T002", "name": "synthetic B", "source_role": "test", "status": "synthetic", "source_effort": "2人日", "execution_dependencies_candidate": ["T001"]},
                 {"id": "T003", "name": "synthetic C", "source_role": "test", "status": "synthetic", "source_effort": "2人日", "execution_dependencies_candidate": ["T001"]}]
        rows = [{"task_id": t["id"], "verification_status": "NO_FULL_TASK_VERIFICATION_EVIDENCE", "resource_id": "R1" if t["id"] != "T003" else "R2", "remaining_effort_hours": 8,
                 "full_task_verification_refs": [], "partial_scope_evidence": [], "actual_start": None, "actual_end": None,
                 "material_or_resource_dependencies": ["synthetic release"] if t["id"] == "T002" else [],
                 "external_release_date": "2026-10-16" if t["id"] == "T002" else None} for t in tasks]
        inputs = {"actual_plan_start_date": "2026-10-13", "resources": [{"resource_id": "R1", "name": "synthetic 1", "effective_hours_per_workday": 8},
                                                                                       {"resource_id": "R2", "name": "synthetic 2", "effective_hours_per_workday": 4}],
                  "calendar": {"working_weekdays": [0, 1, 2, 3, 4], "explicit_nonworking_dates": [], "weekday_assumption_confirmed": True}, "task_execution_inputs": rows}
        example = build_plan(tasks, inputs)
        records = {r["task_id"]: r for r in example["records"]}
        assert records["T001"]["capacity_plan_finish_date"] == "2026-10-13"
        assert records["T002"]["capacity_plan_start_date"] == "2026-10-16"
        assert (records["T003"]["capacity_plan_start_date"], records["T003"]["capacity_plan_finish_date"]) == ("2026-10-14", "2026-10-15")
        cycle = copy.deepcopy(tasks)
        cycle[0]["execution_dependencies_candidate"] = ["T003"]
        try:
            build_plan(cycle, inputs)
        except AssertionError:
            pass
        else:
            raise AssertionError("cycle incorrectly scheduled")
        return {"tasks": 170, "source_person_days": [397, 491], "partial_scope_evidence_tasks": len(partial_ids),
                "actual_people_or_dates_invented": False, "synthetic_capacity_dependency_and_release_tests": "PASS"}

    check("170_task_schedule_unknowns_capacity_and_cycle_rejection", schedule)

    def insufficient():
        public = read("docs/03-api/openapi.yaml")["components"]["schemas"]["Relation"]
        assert public == read("schemas/api/common.schema.json")["$defs"]["Relation"]
        model = read("schemas/model/M29.response.schema.json")["properties"]["payload"]["anyOf"][0]["properties"]["relations"]["items"]
        fixtures = read("tests/fixtures/claim-insufficient-cases.json")
        schemas = {"public": public, "M29_item": model}
        for fixture in fixtures["cases"]:
            validator = Draft202012Validator(schemas[fixture["schema"]], format_checker=FormatChecker())
            assert validator.is_valid(fixture["value"]) == fixture["valid"], fixture["name"]
        return {"actual_contract_cases": len(fixtures["cases"]), "insufficient_may_have_zero_evidence": True,
                "other_relations_still_require_evidence": True, "live_database_or_business_service_changed": False}

    check("insufficient_zero_evidence_allowed_other_relations_rejected", insufficient)
    report = {"status": "FAIL" if errors else "PASS", "scope": "visual_review_evidence_semantic_technical_review_metric_definitions_schedule_inputs_and_contract_fix",
              "checks": checks, "errors": errors, "formal_stage_one_approval": False,
              "actual_calendar_commitment_made": False, "actual_business_acceptance_completed": False}
    path = ROOT / "docs/00-project/validation/stage-one-completion-report.json"
    path.write_bytes((json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode())
    print(json.dumps({"status": report["status"], "checks": len(checks), "errors": errors}, ensure_ascii=False))
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
