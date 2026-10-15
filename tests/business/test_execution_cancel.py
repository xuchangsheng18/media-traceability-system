from uuid import uuid4

import psycopg
from business_app.types import Scope

from tests.business.test_adapters_and_execution import prepare_node
from tests.business.test_controls import AUTH
from tests.business.test_controls import control_context as control_context


def cancel(context):
    http = context["control_http"]
    path = f"/api/v1/analysis/tasks/{context['task_id']}"
    current = http.get(path + "/execution", headers=AUTH)
    body = dict(
        reason="self-owned cancellation test",
        expected_run_version=current.json()["run_version"],
        expected_version=current.json()["version"],
        approval_id=None,
    )
    headers = dict(AUTH, **{"If-Match": current.headers["ETag"], "Idempotency-Key": uuid4().hex})
    response = http.post(path + "/cancel", json=body, headers=headers)
    assert response.status_code == 202, response.json()
    assert http.post(path + "/cancel", json=body, headers=headers).json() == response.json()
    return current, response


def test_cancel_is_transactional_and_preserves_immutable_history(control_context):
    c = control_context
    prepare_node(c)
    http = c["control_http"]
    path = f"/api/v1/analysis/tasks/{c['task_id']}"
    historical = http.get(path, headers=AUTH).json()
    previous, response = cancel(c)
    assert http.get(response.json()["status_url"], headers=AUTH).json()["state"] == "CANCEL_REQUESTED"
    scope = Scope(c["actor"], c["case_id"])
    execution = c["control_app"].state.execution
    assert execution.reconcile_cancel(scope, c["task_id"], 1, previous.json()["version"] + 1, uuid4()) is True
    assert execution.reconcile_cancel(scope, c["task_id"], 1, previous.json()["version"] + 1, uuid4()) is True
    current = http.get(response.json()["status_url"], headers=AUTH)
    assert current.json()["state"] == "CANCELLED" and current.json()["version"] == 3
    assert http.get(path, headers=AUTH).json() == historical
    with psycopg.connect(c["admin_dsn"]) as connection:
        values = connection.execute(
            "SELECT topic,payload FROM mt.outbox_event WHERE aggregate_id=%s ORDER BY aggregate_version",
            (c["task_id"],),
        ).fetchall()
        assert [v[0] for v in values] == ["workflow.run.cancel_requested.v1", "workflow.run.cancelled.v1"]
        assert all(v[1]["binding"]["run_version"] == 1 for v in values)
        assert all(v[1]["producer_role"] == "scheduler" for v in values)


def test_cancel_waits_for_running_worker_acknowledgement(control_context):
    c = control_context
    node = prepare_node(c)
    scope = Scope(c["actor"], c["case_id"])
    execution = c["control_app"].state.execution
    lease = execution.claim(scope, node)
    previous, response = cancel(c)
    assert execution.reconcile_cancel(scope, c["task_id"], 1, previous.json()["version"] + 1, uuid4()) is False
    assert c["control_http"].get(response.json()["status_url"], headers=AUTH).json()["state"] == "CANCEL_REQUESTED"
    execution.finish_without_result(scope, lease, "CANCELLED", "Self-owned worker confirms it stopped")
    assert execution.reconcile_cancel(scope, c["task_id"], 1, previous.json()["version"] + 1, uuid4()) is True


def test_expired_current_lease_can_acknowledge_stop_after_cancel_request(control_context):
    c = control_context
    node = prepare_node(c)
    scope = Scope(c["actor"], c["case_id"])
    execution = c["control_app"].state.execution
    lease = execution.claim(scope, node)
    previous, _ = cancel(c)
    with psycopg.connect(c["admin_dsn"]) as connection:
        connection.execute(
            "UPDATE mt.task_node_run SET started_at=now()-interval '31 seconds' WHERE run_id=%s", (node,)
        )
    execution.finish_without_result(
        scope, lease, "CANCELLED", "Current fenced worker confirms stopped after lease expiry"
    )
    assert execution.reconcile_cancel(scope, c["task_id"], 1, previous.json()["version"] + 1, uuid4()) is True
