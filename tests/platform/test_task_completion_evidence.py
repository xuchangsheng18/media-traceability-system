"""Completion is possible only with complete, reviewed and untampered evidence."""

import copy
import hashlib
import importlib
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
progress = importlib.import_module("generate_task_progress")


@pytest.fixture
def completed_fixture(tmp_path, monkeypatch):
    source_bytes = (ROOT / "tasks/source-task-cards.json").read_bytes()
    source = json.loads(source_bytes)
    source_hash = hashlib.sha256(source_bytes).hexdigest()

    def write(path, value):
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((value if isinstance(value, str) else json.dumps(value)).encode("utf8"))

    write("tasks/source-task-cards.json", source_bytes.decode("utf8"))
    write("docs/confirmed-inputs.md", "Synthetic test only; not a human acceptance record.")
    write("README.md", "Synthetic source under verification.")
    write("docs/test-output.json", {"synthetic": True, "status": "PASS"})
    output_hash = hashlib.sha256((tmp_path / "docs/test-output.json").read_bytes()).hexdigest()
    ledger = copy.deepcopy(progress.read("tasks/execution-status.json"))
    planning = copy.deepcopy(progress.read("docs/00-project/execution-planning-inputs.json"))
    for row in ledger["tasks"]:
        row.update(
            status="NO_FULL_TASK_VERIFICATION_EVIDENCE",
            full_task_verified=False,
            actual_owner=None,
            completed_steps=[],
            remaining_steps=[{"category": "fixture", "description": "unexecuted"}],
        )
        for key in [
            "specific_validation_report",
            "development_validation_report",
            "acceptance_review_ref",
            "role_model_validation_report",
        ]:
            row.pop(key, None)
        write(row["card"], "# " + row["task_id"] + "\n")
    for row in planning["task_execution_inputs"]:
        row.update(
            verification_status="NO_FULL_TASK_VERIFICATION_EVIDENCE",
            resource_id=None,
            partial_scope_evidence=[],
            full_task_verification_refs=[],
            remaining_effort_hours=None,
            actual_start=None,
            actual_end=None,
            verified_by=None,
        )
    person = {
        "resource_id": "fixture-owner",
        "name": "Synthetic owner",
        "effective_hours_per_workday": None,
        "assignment_confirmed_by_user": True,
        "assigned_task_ids": ["T001"],
        "assignment_basis_ref": "docs/confirmed-inputs.md",
    }
    planning["resources"] = [person]
    evidence = {"path": "docs/test-output.json", "scope": "Synthetic fixture only"}
    ledger["tasks"][0].update(
        status="FULL_TASK_VERIFIED",
        full_task_verified=True,
        actual_owner=person["name"],
        completed_steps=[{"description": "Synthetic delivered scope", "kind": "DEVELOPMENT", "evidence": [evidence]}],
        remaining_steps=[],
        summary_remaining="无本任务内未关闭项",
    )
    planning["task_execution_inputs"][0].update(
        verification_status="FULL_TASK_VERIFIED",
        resource_id=person["resource_id"],
        partial_scope_evidence=[evidence],
        remaining_effort_hours=0,
        actual_start="2026-10-16",
        actual_end="2026-10-17",
        verified_by="Synthetic reviewer",
        full_task_verification_refs=[{"path": "docs/acceptance.json", "scope": "Synthetic fixture only"}],
    )
    fields = source["T001"]["fields"]
    criteria = [text.strip() for text in re.split(r"[；;。]", fields["验收标准"]) if text.strip()]
    record = {
        "task_id": "T001",
        "status": "PASS",
        "source_task_cards_sha256": source_hash,
        "source_acceptance": fields["验收标准"],
        "source_test_requirements": fields["测试要求"],
        "environment_scope": "Synthetic test only",
        "blockers": [],
        "source_file_sha256": {"README.md": hashlib.sha256((tmp_path / "README.md").read_bytes()).hexdigest()},
        "reviewed_by": "Synthetic reviewer",
        "review_basis_ref": "docs/confirmed-inputs.md",
        "criteria": [{"requirement": text, "status": "PASS", "check_ids": ["check-1"]} for text in criteria],
        "test_check_ids": ["check-1"],
        "checks": [
            {
                "id": "check-1",
                "status": "PASS",
                "exit_code": 0,
                "skipped": 0,
                "command": "synthetic verification",
                "source_commit": "1" * 40,
                "observed_at": "2026-10-17T00:00:00+00:00",
                "artifact_path": evidence["path"],
                "artifact_sha256": output_hash,
            }
        ],
    }
    write("docs/acceptance.json", record)
    write("tasks/execution-status.json", ledger)
    write("docs/00-project/execution-planning-inputs.json", planning)
    monkeypatch.setattr(progress, "ROOT", tmp_path)
    return ledger, source, planning, record, write


def test_complete_reviewed_task_is_accepted_and_counted(completed_fixture):
    ledger, source, planning, _, _ = completed_fixture
    progress.validate(ledger, source, planning)
    outputs = progress.outputs()
    assert "完整任务验收 **1/170**" in outputs["tasks/README.md"]
    card = outputs[ledger["tasks"][0]["card"]]
    assert "已通过本任务验收" in card
    assert "Synthetic reviewer" in card
    assert "整任务验收未登记" not in card
    assert "docs/acceptance.json" in card
    text = outputs["docs/00-project/task-execution-steps.txt"]
    assert "整任务验收完成1项" in text
    numbers = re.findall(r"^(\d+)\. \[", text, re.MULTILINE)
    assert [int(n) for n in numbers] == list(range(1, 171))
    assert "T001-C01" in text and "T170-R01" in text


def test_stage_one_summary_accepts_full_state_without_counting_it_as_partial(completed_fixture):
    ledger, _, _, _, _ = completed_fixture
    stage_one = importlib.import_module("validate_stage_one_completion")
    assert stage_one.partial_task_ids(ledger) == set()


def test_completion_requires_verified_prerequisites(completed_fixture):
    ledger, source, planning, _, _ = completed_fixture
    source["T001"]["fields"]["执行依赖候选"] = "T002"
    with pytest.raises(AssertionError):
        progress.validate(ledger, source, planning)


@pytest.mark.parametrize(
    "change",
    [
        "no_review",
        "no_dates",
        "open_work",
        "missing_criterion",
        "failed_check",
        "skipped_check",
        "tampered_artifact",
        "missing_evidence",
        "wrong_task",
        "changed_source",
        "stale_source",
        "outside_repo",
        "no_blockers_key",
        "open_blocker",
    ],
)
def test_unproven_completion_is_rejected(completed_fixture, change):
    ledger, source, planning, record, write = completed_fixture
    actual = planning["task_execution_inputs"][0]
    if change == "no_review":
        actual["verified_by"] = None
    elif change == "no_dates":
        actual["actual_end"] = None
    elif change == "open_work":
        ledger["tasks"][0]["remaining_steps"] = [{"description": "unfinished", "category": "test"}]
    elif change == "missing_criterion":
        record["criteria"].pop()
    elif change == "failed_check":
        record["checks"][0]["exit_code"] = 1
    elif change == "skipped_check":
        record["checks"][0]["skipped"] = 1
    elif change == "tampered_artifact":
        write("docs/test-output.json", "tampered")
    elif change == "missing_evidence":
        actual["full_task_verification_refs"] = []
    elif change == "wrong_task":
        record["task_id"] = "T002"
    elif change == "changed_source":
        record["source_acceptance"] = "weakened acceptance"
    elif change == "stale_source":
        write("README.md", "Source changed after verification.")
    elif change == "outside_repo":
        record["checks"][0]["artifact_path"] = "../outside.json"
    elif change == "no_blockers_key":
        record.pop("blockers")
    else:
        record["blockers"] = ["unfinished"]
    write("docs/acceptance.json", record)
    with pytest.raises((AssertionError, OSError, ValueError, KeyError)):
        progress.validate(ledger, source, planning)
