"""Cancellation-only writes against fresh PostgreSQL and explicit synthetic authority."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import replace
from uuid import uuid4

import psycopg
import pytest
from business_app.data_scope import TaskBinding
from business_app.errors import BusinessError
from business_app.permissions.context import protected_work
from business_app.scope_context import bind_data_scope, current_data_scope
from business_app.types import Scope
from sqlalchemy import event

from tests.business.http_fixtures import synthetic_case_evidence
from tests.business.test_adapters_and_execution import prepare_node
from tests.business.test_controls import AUTH
from tests.business.test_controls import control_context as control_context

REQUESTABLE = ("CREATED", "QUEUED", "RUNNING", "WAIT_REVIEW", "REVIEWING", "RETURNED")


def persisted(context):
    with psycopg.connect(context["admin_dsn"]) as connection:
        projection = connection.execute(
            "SELECT state,run_version,row_version FROM mt.analysis_task WHERE task_id=%s", (context["task_id"],)
        ).fetchone()
        assert projection is not None
        counts = []
        for table in ("task_event", "outbox_event", "idempotency_record", "audit_event"):
            value = connection.execute(f"SELECT count(*) FROM mt.{table}").fetchone()
            assert value is not None
            counts.append(value[0])
    return projection, tuple(counts)


@contextmanager
def transaction(context):
    service = context["control_app"].state.execution
    scope = Scope(context["actor"], context["case_id"])
    with (
        protected_work(service.work_authorization, scope, "task_cancellation", context["task_id"], "cancelTaskWork"),
        service.database.transaction(scope) as connection,
    ):
        yield service, scope, connection


def write(service, scope, connection, context, **changes):
    values = dict(
        task_id=context["task_id"],
        run_version=1,
        expected_version=1,
        before="CREATED",
        after="CANCEL_REQUESTED",
        request_id=uuid4(),
        reason="Self-owned cancellation writer regression; no algorithm result",
    )
    values.update(changes)
    service.cancel_transition(connection, scope, **values)
    return values


@pytest.mark.parametrize("before", REQUESTABLE)
def test_request_writer_updates_projection_and_exact_run_event_atomically(control_context, before):
    c = control_context
    with psycopg.connect(c["admin_dsn"]) as connection:
        connection.execute("UPDATE mt.analysis_task SET state=%s WHERE task_id=%s", (before, c["task_id"]))
    original = persisted(c)
    with transaction(c) as (service, scope, connection):
        values = write(service, scope, connection, c, before=before)
    assert persisted(c) == (("CANCEL_REQUESTED", 1, 2), tuple(n + d for n, d in zip(original[1], (1, 1, 0, 0))))
    with psycopg.connect(c["admin_dsn"]) as connection:
        item = connection.execute(
            "SELECT e.event_id,e.from_state,e.to_state,e.run_version,e.request_id,o.aggregate_version,o.payload "
            "FROM mt.task_event e JOIN mt.outbox_event o USING(event_id) WHERE e.task_id=%s",
            (c["task_id"],),
        ).fetchone()
    assert item is not None
    assert item[1:6] == (before, "CANCEL_REQUESTED", 1, values["request_id"], 2)
    assert item[6]["event_id"] == str(item[0])
    assert item[6]["event_type"] == "workflow.run.cancel_requested.v1"
    assert item[6]["binding"]["run_version"] == 1
    assert item[6]["binding"]["task_id"] == str(c["task_id"])


@pytest.mark.parametrize(
    "before,after",
    [(state, "CANCEL_REQUESTED") for state in ("SUCCEEDED", "FAILED", "CANCELLED", "ARCHIVED", "CANCEL_REQUESTED")]
    + [("CREATED", "QUEUED"), ("CANCEL_REQUESTED", "SUCCEEDED"), ("FAILED", "CANCELLED")],
)
def test_writer_cannot_be_used_as_generic_state_machine(control_context, before, after):
    c = control_context
    with psycopg.connect(c["admin_dsn"]) as connection:
        connection.execute("UPDATE mt.analysis_task SET state=%s WHERE task_id=%s", (before, c["task_id"]))
    original = persisted(c)
    with transaction(c) as (service, scope, connection), pytest.raises(BusinessError) as denied:
        write(service, scope, connection, c, before=before, after=after)
    assert denied.value.http_status == 409
    assert persisted(c) == original


@pytest.mark.parametrize("defect", ["run", "row", "before", "case", "unit", "actor", "task"])
def test_writer_rejects_stale_versions_and_mismatched_scope_without_writes(control_context, defect):
    c = control_context
    original = persisted(c)
    with transaction(c) as (service, scope, connection), pytest.raises(BusinessError) as denied:
        changes: dict[str, dict[str, object]] = {
            "run": dict(run_version=2),
            "row": dict(expected_version=2),
            "before": dict(before="QUEUED"),
        }
        if defect == "case":
            scope = replace(scope, case_id=c["other_case_id"])
        if defect == "unit":
            scope = replace(scope, actor=replace(scope.actor, org_id=uuid4()))
        if defect == "actor":
            scope = replace(scope, actor=replace(scope.actor, user_id=uuid4()))
        write(service, scope, connection, c, **(dict(task_id=uuid4()) if defect == "task" else changes.get(defect, {})))
    assert denied.value.code == {
        "run": "TASK_CONTROL_VERSION_CONFLICT",
        "row": "TASK_CONTROL_VERSION_CONFLICT",
        "before": "TASK_CONTROL_STATE_CONFLICT",
    }.get(defect, "AUTHORITY_SCOPE_INVALID")
    assert persisted(c) == original


@pytest.mark.parametrize("bound_run", [1, 2])
def test_writer_respects_preexisting_run_scope_when_newer_projection_exists(control_context, bound_run):
    c = control_context
    with psycopg.connect(c["admin_dsn"]) as connection:
        connection.execute(
            "INSERT INTO mt.task_run(task_run_id,org_id,case_id,task_id,run_version,input_sha256,dag_version,policy_version) "
            "SELECT %s,org_id,case_id,task_id,2,input_sha256,dag_version,policy_version "
            "FROM mt.task_run WHERE task_id=%s AND run_version=1",
            (uuid4(), c["task_id"]),
        )
        connection.execute("UPDATE mt.analysis_task SET run_version=2 WHERE task_id=%s", (c["task_id"],))
    original = persisted(c)
    with transaction(c) as (service, scope, connection):
        bound = current_data_scope()
        assert bound is not None
        with bind_data_scope(replace(bound, task_binding=TaskBinding(c["task_id"], bound_run))):
            if bound_run == 1:
                with pytest.raises(BusinessError) as denied:
                    write(service, scope, connection, c, run_version=2)
                assert denied.value.code == "AUTHORITY_SCOPE_INVALID"
            else:
                write(service, scope, connection, c, run_version=2)
    assert persisted(c) == (
        original
        if bound_run == 1
        else (("CANCEL_REQUESTED", 2, 2), tuple(n + d for n, d in zip(original[1], (1, 1, 0, 0))))
    )


@pytest.mark.parametrize("table", ["task_event", "outbox_event"])
def test_writer_savepoint_rolls_back_even_when_caller_catches_injected_failure(control_context, table):
    c = control_context
    original = persisted(c)
    service = c["control_app"].state.execution

    def fail(connection, cursor, statement, parameters, context, executemany):
        if f"INSERT INTO mt.{table}(" in statement:
            raise RuntimeError("self-owned injected write failure")

    event.listen(service.database.engine, "before_cursor_execute", fail)
    try:
        with transaction(c) as (service, scope, connection):
            with pytest.raises(RuntimeError, match="self-owned injected write failure"):
                write(service, scope, connection, c)
            # The caller deliberately continues its outer transaction after the failure.
            assert connection.exec_driver_sql("SELECT 1").scalar_one() == 1
    finally:
        event.remove(service.database.engine, "before_cursor_execute", fail)
    assert persisted(c) == original


@pytest.mark.parametrize("with_read_authority", [False, True])
def test_writer_requires_cancellation_operation_authority(control_context, with_read_authority):
    c = control_context
    original = persisted(c)
    service = c["control_app"].state.execution
    scope = Scope(c["actor"], c["case_id"])
    with pytest.raises(BusinessError) as denied:
        if with_read_authority:
            with synthetic_case_evidence(c["actor"], c["case_id"]), service.database.transaction(scope) as connection:
                write(service, scope, connection, c)
        else:
            with service.database.engine.begin() as connection:
                write(service, scope, connection, c)
    assert denied.value.code == "AUTHORITY_SCOPE_INVALID"
    assert persisted(c) == original


@pytest.mark.parametrize("node_state", ["PENDING", "READY", "RUNNING", "DEFERRED"])
def test_final_writer_rejects_nodes_not_yet_stopped(control_context, node_state):
    c = control_context
    node = prepare_node(c)
    with psycopg.connect(c["admin_dsn"]) as connection:
        connection.execute("UPDATE mt.analysis_task SET state='CANCEL_REQUESTED' WHERE task_id=%s", (c["task_id"],))
        connection.execute("UPDATE mt.task_node_run SET state=%s WHERE run_id=%s", (node_state, node))
    original = persisted(c)
    with transaction(c) as (service, scope, connection), pytest.raises(BusinessError) as denied:
        write(service, scope, connection, c, before="CANCEL_REQUESTED", after="CANCELLED")
    assert denied.value.code == "CANCEL_REQUEST_STALE"
    assert persisted(c) == original


@pytest.mark.parametrize("table", ["task_event", "outbox_event", "idempotency_record", "audit_event"])
def test_http_cancel_rolls_back_projection_events_receipt_and_audit(control_context, table):
    c = control_context
    original = persisted(c)
    service = c["control_app"].state.execution

    def fail(connection, cursor, statement, parameters, context, executemany):
        if f"INSERT INTO mt.{table}(" in statement:
            raise RuntimeError("self-owned HTTP cancellation fault")

    event.listen(service.database.engine, "before_cursor_execute", fail)
    try:
        path = f"/api/v1/analysis/tasks/{c['task_id']}"
        current = c["control_http"].get(path + "/execution", headers=AUTH)
        headers = dict(AUTH, **{"If-Match": current.headers["ETag"], "Idempotency-Key": uuid4().hex})
        body = dict(reason="self-owned HTTP fault", expected_run_version=1, expected_version=1, approval_id=None)
        failed = c["control_http"].post(path + "/cancel", json=body, headers=headers)
        assert failed.status_code == 500 and failed.json()["code"] == "INTERNAL_ERROR"
        assert "self-owned HTTP cancellation fault" not in failed.text
    finally:
        event.remove(service.database.engine, "before_cursor_execute", fail)
    assert persisted(c) == original
    retry = c["control_http"].post(path + "/cancel", json=body, headers=headers)
    assert retry.status_code == 202
    assert c["control_http"].post(path + "/cancel", json=body, headers=headers).json() == retry.json()
    assert persisted(c) == (("CANCEL_REQUESTED", 1, 2), tuple(n + 1 for n in original[1]))


def test_transaction_end_authority_rejection_rolls_back_entire_http_cancel(control_context):
    c = control_context
    original = persisted(c)
    app = c["control_app"]
    old = app.state.authorization_fence
    observed = []

    class Revoked:
        def hold(self, connection, evidence):
            old.hold(connection, evidence)

        def finish(self, connection, evidence):
            old.finish(connection, evidence)
            state = connection.exec_driver_sql(
                "SELECT state FROM mt.analysis_task WHERE task_id=%s", (c["task_id"],)
            ).scalar_one_or_none()
            if state == "CANCEL_REQUESTED":
                observed.append(state)
                raise BusinessError("PERMISSION_REQUIRED", 403)

    path = f"/api/v1/analysis/tasks/{c['task_id']}"
    current = c["control_http"].get(path + "/execution", headers=AUTH)
    app.state.authorization_fence = Revoked()
    try:
        response = c["control_http"].post(
            path + "/cancel",
            headers=dict(AUTH, **{"If-Match": current.headers["ETag"], "Idempotency-Key": uuid4().hex}),
            json=dict(
                reason="self-owned final fence fault", expected_run_version=1, expected_version=1, approval_id=None
            ),
        )
        assert response.status_code == 403
    finally:
        app.state.authorization_fence = old
    assert observed == ["CANCEL_REQUESTED"]
    assert persisted(c) == original


@pytest.mark.parametrize("same_key", [False, True])
def test_concurrent_http_cancel_emits_one_event_and_preserves_idempotency(control_context, same_key):
    c = control_context
    original = persisted(c)
    path = f"/api/v1/analysis/tasks/{c['task_id']}"
    current = c["control_http"].get(path + "/execution", headers=AUTH)
    key = uuid4().hex

    def send(index):
        return c["control_http"].post(
            path + "/cancel",
            headers=dict(
                AUTH, **{"If-Match": current.headers["ETag"], "Idempotency-Key": key if same_key else key + str(index)}
            ),
            json=dict(
                reason="self-owned concurrent request", expected_run_version=1, expected_version=1, approval_id=None
            ),
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        replies = list(pool.map(send, (0, 1)))
    assert sorted(r.status_code for r in replies) == ([202, 202] if same_key else [202, 412])
    if same_key:
        assert replies[0].json() == replies[1].json()
    assert persisted(c) == (("CANCEL_REQUESTED", 1, 2), tuple(n + 1 for n in original[1]))
