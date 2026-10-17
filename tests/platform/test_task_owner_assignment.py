"""Confirmed task responsibility must not fabricate capacity or formal acceptance."""

import copy
import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
progress = importlib.import_module("generate_task_progress")
schedule = importlib.import_module("plan_project_schedule")


def assigned_inputs():
    ledger = progress.read("tasks/execution-status.json")
    planning = progress.read("docs/00-project/execution-planning-inputs.json")
    ledger = copy.deepcopy(ledger)
    planning = copy.deepcopy(planning)
    person = {
        "resource_id": "test-confirmed-owner",
        "name": "synthetic confirmed person",
        "effective_hours_per_workday": None,
        "assignment_confirmed_by_user": True,
        "assigned_task_ids": ["T001"],
        "assignment_basis_ref": "docs/03-development/repository-access-control.md",
    }
    planning["resources"] = [person]
    for row in ledger["tasks"]:
        row["actual_owner"] = person["name"] if row["task_id"] == "T001" else None
    for row in planning["task_execution_inputs"]:
        row["resource_id"] = person["resource_id"] if row["task_id"] == "T001" else None
    return ledger, planning


def test_user_confirmed_name_with_unknown_hours_is_a_valid_partial_input():
    ledger, planning = assigned_inputs()
    progress.validate(ledger, progress.read("tasks/source-task-cards.json"), planning)
    assert not ledger["tasks"][0]["full_task_verified"]
    assert planning["task_execution_inputs"][0]["remaining_effort_hours"] is None


@pytest.mark.parametrize("mutation", ["different_name", "unknown_resource", "unconfirmed", "wrong_scope", "no_owner"])
def test_task_owner_and_confirmed_person_record_must_agree(mutation):
    ledger, planning = assigned_inputs()
    if mutation == "different_name":
        ledger["tasks"][0]["actual_owner"] = "another person"
    elif mutation == "unknown_resource":
        planning["task_execution_inputs"][0]["resource_id"] = "missing-person"
    elif mutation == "unconfirmed":
        planning["resources"][0]["assignment_confirmed_by_user"] = False
    elif mutation == "wrong_scope":
        planning["resources"][0]["assigned_task_ids"] = ["T002"]
    else:
        ledger["tasks"][0]["actual_owner"] = None
    with pytest.raises(AssertionError):
        progress.validate(ledger, progress.read("tasks/source-task-cards.json"), planning)


def test_assignment_without_capacity_keeps_dates_unknown_and_records_missing_hours():
    _, planning = assigned_inputs()
    tasks = schedule.read("tasks/backlog.yaml")["tasks"]
    plan = schedule.build_plan(tasks, planning)
    actual = plan["actual_capacity_plan"]
    assert actual["status"] == "NOT_COMPUTABLE_ACTUAL_INPUTS_MISSING"
    assert "test-confirmed-owner:effective_hours_per_workday" in actual["missing_inputs"]
    assert "T001:actual_assignee" not in actual["missing_inputs"]
    row = next(row for row in plan["records"] if row["task_id"] == "T001")
    assert row["actual_assignee_name"] == "synthetic confirmed person"
    assert row["capacity_plan_start_date"] is row["capacity_plan_finish_date"] is None
    assert not actual["calendar_commitment_asserted"]


@pytest.mark.parametrize("hours", [0, -1, 25, True, "8", float("nan"), float("inf")])
def test_invalid_capacity_is_rejected_without_inventing_a_default(hours):
    _, planning = assigned_inputs()
    planning["resources"][0]["effective_hours_per_workday"] = hours
    with pytest.raises(AssertionError):
        schedule.build_plan(schedule.read("tasks/backlog.yaml")["tasks"], planning)


def test_placeholder_scenario_never_exports_a_name_as_actual_assignment():
    import json

    placeholder = importlib.import_module("plan_placeholder_schedule")
    outputs = placeholder.outputs()
    plan = json.loads(outputs["docs/00-project/execution-schedule-scenario.json"])
    assert plan["actual_people_confirmed"] is False
    for row in plan["records"]:
        assert "actual_assignee_name" not in row
        assert row["scenario_resource_name"].startswith("占位")
