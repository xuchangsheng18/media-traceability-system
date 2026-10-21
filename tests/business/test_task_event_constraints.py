"""Run identity and state vocabulary, not approval of state transitions."""

from uuid import uuid4

import psycopg
import pytest

from tests.business.test_controls import control_context as control_context

TASK_STATES = (
    "CREATED",
    "QUEUED",
    "RUNNING",
    "WAIT_REVIEW",
    "REVIEWING",
    "SUCCEEDED",
    "FAILED",
    "RETURNED",
    "CANCEL_REQUESTED",
    "CANCELLED",
    "ARCHIVED",
)


def append_event(connection, context, **changes):
    values = dict(
        event_id=uuid4(),
        org_id=context["actor"].org_id,
        case_id=context["case_id"],
        task_id=context["task_id"],
        run_version=1,
        from_state="RUNNING",
        to_state="CANCEL_REQUESTED",
        reason="self-owned constraint fixture only",
        request_id=uuid4(),
    )
    values.update(changes)
    connection.execute(
        "INSERT INTO mt.task_event(event_id,org_id,case_id,task_id,run_version,from_state,to_state,reason,request_id) "
        "VALUES(%(event_id)s,%(org_id)s,%(case_id)s,%(task_id)s,%(run_version)s,%(from_state)s,%(to_state)s,%(reason)s,%(request_id)s)",
        values,
    )
    return values["event_id"]


@pytest.mark.parametrize(
    "invalid", ["missing_run", "foreign_run", "other_case", "other_unit", "from_state", "to_state"]
)
def test_task_events_reject_wrong_identity_or_state_without_partial_write(control_context, invalid):
    c = control_context
    changes = {
        "missing_run": dict(run_version=999),
        "foreign_run": dict(run_version=2),
        "other_case": dict(case_id=c["other_case_id"]),
        "other_unit": dict(org_id=uuid4()),
        "from_state": dict(from_state="NOT_SELECTED"),
        "to_state": dict(to_state="READY"),
    }[invalid]
    with psycopg.connect(c["admin_dsn"]) as connection:
        if invalid == "foreign_run":
            other_task = uuid4()
            connection.execute(
                "INSERT INTO mt.analysis_task(task_id,org_id,case_id,asset_id,scene,priority,state,policy_version,modules,report_eligibility) "
                "SELECT %s,org_id,case_id,asset_id,scene,priority,state,policy_version,modules,report_eligibility FROM mt.analysis_task WHERE task_id=%s",
                (other_task, c["task_id"]),
            )
            connection.execute(
                "INSERT INTO mt.task_run(task_run_id,org_id,case_id,task_id,run_version,input_sha256,dag_version,policy_version) "
                "SELECT %s,org_id,case_id,%s,2,input_sha256,dag_version,policy_version FROM mt.task_run WHERE task_id=%s AND run_version=1",
                (uuid4(), other_task, c["task_id"]),
            )
        before = connection.execute("SELECT count(*) FROM mt.task_event").fetchone()
        error = psycopg.errors.CheckViolation if invalid.endswith("state") else psycopg.errors.ForeignKeyViolation
        with pytest.raises(error), connection.transaction():
            append_event(connection, c, **changes)
        assert connection.execute("SELECT count(*) FROM mt.task_event").fetchone() == before


@pytest.mark.parametrize("destination", TASK_STATES)
def test_task_event_vocabulary_preserves_every_existing_state_and_nullable_initial_state(control_context, destination):
    # Storage vocabulary only: these combinations do not grant a legal transition.
    c = control_context
    with psycopg.connect(c["admin_dsn"]) as connection:
        for source in (None, *TASK_STATES):
            identifier = append_event(connection, c, from_state=source, to_state=destination)
            assert connection.execute(
                "SELECT from_state,to_state,run_version FROM mt.task_event WHERE event_id=%s", (identifier,)
            ).fetchone() == (source, destination, 1)


@pytest.mark.parametrize("table", ["task_run", "task_event"])
@pytest.mark.parametrize("action", ["UPDATE", "DELETE", "TRUNCATE"])
def test_fixed_run_and_event_history_remain_append_only(control_context, table, action):
    c = control_context
    with psycopg.connect(c["admin_dsn"]) as connection:
        append_event(connection, c)
        before = connection.execute(f"SELECT * FROM mt.{table} ORDER BY 1").fetchall()
        statement = {
            "UPDATE": f"UPDATE mt.{table} SET row_version=row_version+1",
            "DELETE": f"DELETE FROM mt.{table}",
            "TRUNCATE": f"TRUNCATE mt.{table} CASCADE",
        }[action]
        with (
            pytest.raises(psycopg.errors.ObjectNotInPrerequisiteState, match="append-only table"),
            connection.transaction(),
        ):
            connection.execute(statement)
        assert connection.execute(f"SELECT * FROM mt.{table} ORDER BY 1").fetchall() == before
