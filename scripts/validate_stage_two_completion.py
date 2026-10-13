"""Check second-stage delivery scope, operational guards and real report boundaries."""
import hashlib
import json
import tempfile
from pathlib import Path

import yaml
from stage_two_readiness import ROOT, storage_state, verify_artifacts


def main():
    checks = []

    def check(name, condition):
        assert condition, name
        checks.append({"name": name, "status": "PASS"})

    def rejected(action):
        try:
            action()
        except ValueError:
            return True
        return False

    candidate = json.loads((ROOT/"config/stage-two-operations.candidate.json").read_text())
    policy = candidate["storage"]
    check("capacity_ok_warning_critical_and_free_space_guards",
          [storage_state({"total_bytes": 1000, "used_bytes": x, "available_bytes": 1000-x},
                         dict(policy, minimum_free_bytes=40)) for x in [100, 900, 970]] == ["OK", "WARNING", "CRITICAL"]
          and storage_state({"total_bytes": 1000, "used_bytes": 800, "available_bytes": 30},
                            dict(policy, minimum_free_bytes=40)) == "CRITICAL")
    check("invalid_capacity_or_thresholds_rejected",
          rejected(lambda: storage_state({"total_bytes": 0, "used_bytes": 0, "available_bytes": 0}, policy))
          and rejected(lambda: storage_state({"total_bytes": 100, "used_bytes": 90, "available_bytes": 20}, policy)))
    with tempfile.TemporaryDirectory(prefix="mt-offline-probe-") as directory:
        path = Path(directory)/"synthetic.txt"
        path.write_bytes(b"self-made offline fixture\n")
        record = {"path": path.name, "size_bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        check("offline_artifact_digest_verification", verify_artifacts(directory, [record]) == 1)
        check("missing_tampered_and_unsafe_offline_artifacts_rejected",
              rejected(lambda: verify_artifacts(directory, [dict(record, sha256="0"*64)]))
              and rejected(lambda: verify_artifacts(directory, [dict(record, path="missing.txt")]))
              and rejected(lambda: verify_artifacts(directory, [dict(record, path="../outside.txt")]))
              and rejected(lambda: verify_artifacts(directory, [record, record]))
              and rejected(lambda: verify_artifacts(directory, [])))
    ledger = json.loads((ROOT/"docs/03-development/stage-two-completion-matrix.json").read_text(encoding="utf-8"))
    versions = yaml.safe_load((ROOT/"config/versions.yaml").read_text(encoding="utf-8"))
    selection = versions["production_python_selection"]
    actual = json.loads((ROOT/selection["actual_evidence_ref"]).read_text(encoding="utf-8"))["production_python_validation"]
    check("all_12_remaining_families_have_concrete_outputs_and_honest_boundaries",
          {item["id"] for item in ledger["items"]} == {f"S2-N{x:02}" for x in range(1, 13)}
          and all(item["completed_this_round"] and item["remaining_actual_requirements"]
                  and item["formal_complete"] is False
                  and all((ROOT/p).is_file() for p in item["evidence_refs"]) for item in ledger["items"]))
    check("formal_values_and_environment_preserved",
          candidate["production_frozen"] is False and candidate["formal_RPO_seconds"] is None
          and candidate["formal_RTO_seconds"] is None and candidate["identity_provider"] is None
          and ledger["stage_steps"] == 23 and ledger["original_business_tasks"] == 170
          and ledger["development_environment"] == "Miniforge py310"
          and versions["python"]["version"] == "3.10.22"
          and versions["not_selected"]["production_python"] is None
          and selection["status"] == "CANDIDATES_NOT_VALIDATED_NOT_APPROVED"
          and selection["candidate_priority"] == ["3.13", "3.12"]
          and [item["branch"] for item in selection["candidates"]] == selection["candidate_priority"]
          and all(item["project_compatibility_validated"] is False for item in selection["candidates"])
          and selection["selected_exact_version"] is None and selection["production_approved"] is False
          and selection["new_environment_installed_or_runtime_switched"] is False
          and selection["current_development_environment_preserved"] is True
          and selection["existing_py310_lock_reusable_as_production_candidate_lock"] is False
          and (ROOT/selection["decision_ref"]).is_file()
          and actual["decision_ref"] == selection["decision_ref"]
          and actual["machine_candidate_policy_ref"] == "config/versions.yaml"
          and selection["eol_310_production_exception"]["status"] == "NOT_REQUESTED_NOT_APPROVED"
          and all(value is None for key, value in selection["eol_310_production_exception"].items()
                  if key not in {"status", "upstream_support_ended_on"})
          and actual["status"] == "NOT_PERFORMED_NOT_APPROVED"
          and all(value is None for value in actual["actual_evidence"].values())
          and actual["python_310_eol_exception"]["status"] == "NOT_REQUESTED_NOT_APPROVED"
          and all(value is None for value in actual["python_310_eol_exception"]["actual_evidence"].values()))
    report = {"status": "PASS", "scope": "second_stage_technical_supplement_and_candidate_policy_consistency_not_production_authorization",
              "checks": checks, "full_business_or_production_completed": False, "formal_frozen": False}
    (ROOT/"docs/00-project/validation/stage-two-supplement-report.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({"status": "PASS", "checks": len(checks)}))


if __name__ == "__main__":
    main()
