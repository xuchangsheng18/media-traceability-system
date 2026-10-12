"""Validate stage-one material lineage and declared references without touching services."""
import datetime
import hashlib
import json
import re
from functools import lru_cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=None)
def read(path):
    text = (ROOT/path).read_text(encoding="utf-8")
    return yaml.safe_load(text) if Path(path).suffix in {".yaml", ".yml"} else json.loads(text)


def digest(path):
    return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()


def main():
    checks, errors = [], []

    def check(name, action):
        try:
            detail = action()
            checks.append({"name": name, "status": "PASS", "detail": detail})
        except Exception as exc:
            checks.append({"name": name, "status": "FAIL"})
            errors.append({"name": name, "error": str(exc)})

    prefix = "docs/00-project/stage-one/"
    deliverables = read(prefix+"deliverables.json")
    imports = read(prefix+"materials-manifest.json")
    usage = read("docs/04-database/table-task-usage.json")

    def steps():
        actual = re.findall(r"^## 第(\d+)步 ([^\n]+)", (ROOT/deliverables["source_guide"]).read_text(encoding="utf-8"), re.M)
        assert actual == [(str(s["step"]), s["title"]) for s in deliverables["steps"]]
        assert [s["step"] for s in deliverables["steps"]] == list(range(1, 25))
        assert digest(deliverables["source_guide"]) == deliverables["source_guide_sha256"]
        for item in deliverables["steps"]:
            assert item["operation"] and item["remaining"] and item["outputs"]
            for path in item["outputs"]:
                assert (ROOT/path).exists(), path
        return {"source_steps": 24, "output_refs": sum(len(s["outputs"]) for s in deliverables["steps"])}

    check("24_original_steps_and_actual_outputs", steps)

    def archives():
        assert len(imports["records"]) == 14
        for record in imports["records"]:
            assert record["identity"] == "historical_reference_not_current_execution_status"
            assert digest(record["archived_path"]) == record["sha256"], record["archived_path"]
        assert "docs/00-project/stage-one/history/** -text" in (ROOT/".gitattributes").read_text()
        return {"missing_package_files_archived": 10, "paired_review_files_archived": 4, "raw_bytes_preserved": True}

    check("14_historical_materials_byte_hashes", archives)

    def sources():
        originals = read("docs/00-project/source-inventory.json")
        for item in originals:
            assert digest(item["path"]) == item["sha256"], item["path"]
        return {"protected_originals": len(originals), "source_hashes_unchanged": True}

    check("business_originals_and_guides_unchanged", sources)

    def prototype():
        current = ROOT/"docs/_converted/original/短视频与图片智能识别溯源系统功能模块界面原型图.md"
        archive = ROOT/(prefix+"history/input-package/docs/_converted/original/短视频与图片智能识别溯源系统功能模块界面原型图.md")
        assert current.read_text(encoding="utf-8") == archive.read_text(encoding="utf-8")
        ppt = next(x for x in read("docs/00-project/source-inventory.json") if x["path"].endswith(".pptx"))
        assert ppt["sha256"] in current.read_text(encoding="utf-8")
        return {"restored_text_matches_archive": True, "source_PPT_hash_matches": True, "visual_fidelity_asserted": False}

    check("prototype_text_source_identity", prototype)

    def tables():
        catalog = read("docs/04-database/table-catalog.json")
        tasks = set(read("tasks/source-task-cards.json"))
        assert set(usage["bindings"]) == set(catalog)
        assert {r["table"] for r in usage["records"]} == set(catalog)
        assert len(tasks) == 170
        for record in usage["records"]:
            assert record["task_ids"] and set(record["task_ids"]) <= tasks
            assert record["responsibility_approved"] is False and record["implemented_usage_asserted"] is False
        return {"business_tables": len(catalog), "fields": sum(len(t["columns"]) for t in catalog.values()), "task_ids_valid": True}

    check("62_table_declared_task_coverage", tables)

    def pointers():
        resolved = 0
        for path, expected in usage["source_hashes"].items():
            assert digest(path) == expected, path
        for record in usage["records"]:
            collected = set()
            for source in record["sources"]:
                document = read(source["path"])
                value = document
                parts = source["pointer"].lstrip("/").split("/")
                for part in parts:
                    key = part.replace("~1", "/").replace("~0", "~")
                    value = value[int(key)] if isinstance(value, list) else value[key]
                assert value == source["task_ids"]
                if source["relation"] == "declared_requirement_reference":
                    assert record["table"] in document["requirements"][int(parts[1])]["table_names"]
                elif source["relation"] == "declared_API_reference":
                    assert record["table"] in document[int(parts[0])]["tables"]
                else:
                    assert source["relation"] == "inherited_responsibility_proposal" and parts[-1] == record["table"]
                collected.update(value)
                resolved += 1
            assert collected == set(record["task_ids"])
        return {"source_pointers_resolved": resolved, "no_invented_usage_or_owner_approval": True}

    check("table_task_source_pointers_resolve", pointers)

    def boundaries():
        assert deliverables["formal_frozen"] is False
        assert all(s["formal_completion_asserted"] is False and s["owner_name"] is None for s in deliverables["steps"])
        assert "NOT_FROZEN" in (ROOT/"docs/00-project/baseline-1.0.md").read_text(encoding="utf-8")
        stage_two = read("docs/03-development/stage-two-deliverables.json")
        assert len(stage_two["steps"]) == 23 and all(s["formal_completion_asserted"] is False for s in stage_two["steps"])
        assert read("docs/00-project/review-decisions.yaml")["decisions"] == []
        return {"stage_one_steps": 24, "stage_two_steps": 23, "source_tasks": 170, "both_formal_baselines_not_frozen": True}

    check("stage_counts_and_no_false_approval", boundaries)

    def sql_evidence():
        report = read("docs/00-project/validation/database-foundation-report.json")
        assert report["status"] == "PASS"
        hashed = [c for c in report["checks"] if "sha256" in c]
        assert hashed
        for item in hashed:
            assert digest(item["name"]) == item["sha256"], item["name"]
        return {"prior_SQL_evidence_matches_current_sources": True, "SQL_executed_by_this_check": False}

    check("retained_SQL_evidence_source_hashes", sql_evidence)

    def content_audit():
        from stage_one_source_audit import audit

        recorded = read(prefix+"source-content-audit.json")
        assert audit() == recorded, "OOXML audit differs from current originals/conversions/task fields"
        assert recorded["summary"]["unexplained_body_text_gaps"] == 0
        assert recorded["summary"]["task_cards_checked"] == 170
        assert recorded["summary"]["task_fields_checked"] == 1700
        assert all(t["name_matches"] and t["fields_match"] for t in recorded["task_source_field_checks"])
        for document in recorded["documents"]:
            assert not document["visual_layout_verified"]
            assert all(m["exact_repository_copies"] for m in document["media"])
            if document["kind"] == "WORD":
                assert all(c["present_in_markdown"] for c in document["comments"])
                assert all(c["targets_present_in_markdown"] for c in document["hyperlink_field_instructions"])
                assert all(c["present_in_markdown"] for t in document["tables"] for c in t["cells"])
            else:
                assert document["slide_count"] == 12
                assert all(s["all_xml_text_present_in_markdown"] for s in document["slides"])
        return recorded["summary"]

    check("OOXML_content_and_1700_task_fields_recomputed", content_audit)

    def section_routes():
        audit = read(prefix+"source-content-audit.json")
        mapping = read(prefix+"source-section-map.json")
        assert digest(prefix+"source-content-audit.json") == mapping["source_audit_sha256"]
        expected = {(d["source"], h["locator"], h["text"], d["source_sha256"]) for d in audit["documents"] for h in d["headings"]}
        actual = {(r["source"], r["locator"], r["heading"], r["source_sha256"]) for r in mapping["records"]}
        assert actual == expected and len(actual) == len(mapping["records"])
        assert mapping["formal_approved"] is False
        for record in mapping["records"]:
            assert record["approved"] is False and record["target_refs"]
            assert all((ROOT/path).is_file() for path in record["target_refs"])
        return {"source_heading_routes": len(actual), "semantic_or_implementation_equivalence_asserted": False}

    check("exact_source_heading_locations_and_candidate_routes", section_routes)

    def review_packets():
        registry = read(prefix+"review-register.json")
        questions = read(registry["source_questions"])["questions"]
        backlog = read("tasks/backlog.yaml")["tasks"]
        assert digest(registry["source_questions"]) == registry["source_questions_sha256"]
        assert digest("tasks/backlog.yaml") == registry["task_backlog_sha256"]
        assert len(registry["questions"]) == 33
        assert {r["question_id"] for r in registry["questions"]} == {q["id"] for q in questions}
        task_ids = {t["id"] for t in backlog}
        packets = set()
        for record in registry["questions"]:
            question = questions[int(record["source_pointer"].split("/")[-1])]
            assert (question["id"], question["source_text"], question["status"], question["owner"], question["decision"]) == (
                record["question_id"], record["source_text"], record["source_status"], record["owner_name"], record["decision"])
            assert record["approved"] is False and record["source_question_closed"] is False
            assert record["declared_blocking_task_ids"] == [t["id"] for t in backlog if question["id"] in t["blocking_questions"]]
            assert set(record["candidate_impact_task_ids"]) <= task_ids
            assert record["required_decision_inputs"] and len(record["closure_criteria"]) == 4
            assert all((ROOT/path).is_file() for path in record["input_refs"])
            packet = (ROOT/record["primary_review"]).read_text(encoding="utf-8")
            assert question["id"] in packet and question["source_text"] in packet and record["required_decision_inputs"] in packet
            packets.add(record["primary_review"])
        assert len(packets) == 7 and registry["formal_frozen"] is False
        return {"questions": 33, "primary_packets": 7, "decisions_fabricated": False, "candidate_impacts_change_task_dependencies": False}

    check("33_source_questions_in_7_concrete_review_packets", review_packets)

    def candidate_snapshot():
        from build_stage_one_candidate import build

        candidate = read(prefix+"input-baseline-candidate.json")
        assert candidate == build(), "candidate input set or source hashes changed; regenerate after review"
        assert candidate["status"] == "NOT_FROZEN" and candidate["formal_frozen"] is False
        assert candidate["approval_record"] is None and candidate["owner_name"] is None
        return {"candidate_files": candidate["file_count"], "historical_snapshots": 2, "formal_frozen": False}

    check("current_candidate_input_set_and_exact_hashes", candidate_snapshot)
    report = {"status": "FAIL" if errors else "PASS", "observed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "scope": "first_stage_material_lineage_navigation_and_declared_references_not_business_acceptance",
              "checks": checks, "errors": errors, "services_or_database_modified": False,
              "formal_stage_one_frozen": False, "formal_stage_two_frozen": False}
    (ROOT/"docs/00-project/validation/stage-one-validation-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "checks": len(checks), "errors": errors}, ensure_ascii=False))
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
