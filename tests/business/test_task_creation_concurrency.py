"""One isolated same-key race with two real engines, not a formal Proof issuer."""

import re
import time
from contextlib import ExitStack
from threading import Event, Thread
from typing import Any
from uuid import UUID, uuid4

import psycopg
from business_app.controls.common import etag
from business_app.db import Database
from sqlalchemy import event

from tests.business.test_task_creation_transaction import (
    TABLES,
    SyntheticMaterialsReader,
    SyntheticTransactionFence,
    authorized,
    counts,
    create,
    creation_environment,
    service,
    sha,
    sql_context,
    task_rows,
)

# Explicit fixture aliases make their actual upstream SQL fixture dependencies
# available without collecting or replacing any existing transaction tests.
creation_environment = creation_environment
sql_context = sql_context


def test_same_key_two_independent_connections_wait_and_keep_one_exact_acceptance(creation_environment, record_property):
    environment = creation_environment
    first_paused, release_first, second_attempted = Event(), Event(), Event()
    acquired_first, second_done = Event(), Event()
    pids: list[int | None] = [None, None]
    backend_starts: dict[int, Any] = {}
    second_issued_at: list[float] = []
    insertions: list[list[str]] = [[], []]
    results: list[dict[str, Any] | None] = [None, None]
    failures: list[BaseException | None] = [None, None]
    contexts: list[Any] = [None, None]
    request_ids = [uuid4(), uuid4()]
    key = "self-owned-concurrent-creation-" + uuid4().hex
    threads: list[Thread] = []

    def backend_pid(connection, index):
        driver = connection.connection.driver_connection
        assert driver is not None
        observed = driver.info.backend_pid
        assert type(observed) is int and observed > 0
        if pids[index] is None:
            pids[index] = observed
        assert pids[index] == observed, "One request unexpectedly changed its real connection"

    def before(index):
        def observe(connection, cursor, statement, parameters, execution_context, many):
            if statement.startswith("SELECT pg_advisory_xact_lock("):
                backend_pid(connection, index)
                if index == 1 and not second_attempted.is_set():
                    second_issued_at.append(time.monotonic())
                    second_attempted.set()
            match = re.match(r"\s*INSERT\s+INTO\s+mt\.([a-z_]+)\b", statement, re.IGNORECASE)
            if match:
                if index == 0 and match[1] == "analysis_task":
                    assert acquired_first.is_set(), "First pause must follow the actual advisory acquisition"
                    first_paused.set()
                    assert release_first.wait(8), "Controller did not release the first real transaction"
                insertions[index].append(match[1])

        return observe

    def after_first(connection, cursor, statement, parameters, execution_context, many):
        if statement.startswith("SELECT pg_advisory_xact_lock("):
            backend_pid(connection, 0)
            acquired_first.set()

    def perform(index, selected, instance):
        try:
            # ContextVars are bound in this thread, not copied from the parent.
            with authorized(selected) as identity:
                contexts[index] = identity
                results[index] = create(selected, key=key, request_id=request_ids[index], instance=instance)
        except BaseException as error:
            failures[index] = error
        finally:
            if index == 1:
                second_done.set()

    with ExitStack() as cleanup:
        selected_environments = []
        for _ in range(2):
            database = Database(environment["runtime_dsn"])
            cleanup.callback(database.close)
            selected = dict(environment, database=database)
            selected["fence"] = SyntheticTransactionFence(selected["actor"], selected["clock"])
            selected["reader"] = SyntheticMaterialsReader(selected)
            selected_environments.append(selected)
        first, second = selected_environments
        assert first["database"] is not second["database"]
        assert first["database"].engine is not second["database"].engine
        assert first["reader"].environment is first and second["reader"].environment is second
        assert first["reader"] is not second["reader"] and first["fence"] is not second["fence"]
        for selected in selected_environments:
            pool = selected["database"].engine.pool
            assert pool.size() == 1 and pool._max_overflow == 0

        for index, selected in enumerate(selected_environments):
            listener = before(index)
            event.listen(selected["database"].engine, "before_cursor_execute", listener)
            cleanup.callback(event.remove, selected["database"].engine, "before_cursor_execute", listener)
        event.listen(first["database"].engine, "after_cursor_execute", after_first)
        cleanup.callback(event.remove, first["database"].engine, "after_cursor_execute", after_first)

        # Establish the observer before the race; it only inspects these two
        # self-owned backends in this fixture's newly randomized database.
        with psycopg.connect(
            environment["admin_dsn"], autocommit=True, connect_timeout=2, options="-c statement_timeout=1000"
        ) as monitor:
            event_receipts_before = monitor.execute("SELECT count(*) FROM mt.event_receipt").fetchone()
            assert event_receipts_before is not None
            try:
                threads.append(Thread(target=perform, args=(0, first, service(first)), daemon=True))
                threads[0].start()
                assert first_paused.wait(5), "First worker never reached its post-lock, pre-INSERT boundary"
                assert insertions == [[], []] and not release_first.is_set()
                first_identity = monitor.execute(
                    "SELECT backend_start FROM pg_catalog.pg_stat_activity WHERE pid=%s AND datname=current_database()",
                    (pids[0],),
                ).fetchone()
                assert first_identity is not None and first_identity[0] is not None and pids[0] is not None
                backend_starts[pids[0]] = first_identity[0]
                threads.append(Thread(target=perform, args=(1, second, service(second)), daemon=True))
                threads[1].start()
                assert second_attempted.wait(5), "Second worker never issued its real advisory statement"
                assert pids[0] is not None and pids[1] is not None and pids[0] != pids[1]
                assert len(second_issued_at) == 1
                # The statement timeout remains the Database default 2000ms.
                # Polling yields for scheduling; only actual PostgreSQL lock
                # categories, holder identity and blocker edges prove the race.
                deadline = second_issued_at[0] + 1.5
                observed_real_wait = False
                while time.monotonic() < deadline:
                    row = monitor.execute(
                        """SELECT a.datname=current_database(),a.wait_event_type,a.wait_event,
                            %s=ANY(pg_catalog.pg_blocking_pids(a.pid)),
                            EXISTS(SELECT 1 FROM pg_catalog.pg_locks waiter
                                JOIN pg_catalog.pg_locks holder
                                ON holder.locktype=waiter.locktype
                                AND holder.database=waiter.database
                                AND holder.classid=waiter.classid AND holder.objid=waiter.objid
                                AND holder.objsubid=waiter.objsubid AND holder.mode=waiter.mode
                                JOIN pg_catalog.pg_stat_activity h ON h.pid=holder.pid
                                WHERE waiter.pid=a.pid AND waiter.locktype='advisory'
                                AND NOT waiter.granted AND holder.granted AND holder.pid=%s
                                AND h.datname=current_database()),a.backend_start
                            FROM pg_catalog.pg_stat_activity a WHERE a.pid=%s""",
                        (pids[0], pids[0], pids[1]),
                    ).fetchone()
                    if row is not None and row[0] is True and pids[1] is not None:
                        assert row[5] is not None
                        backend_starts[pids[1]] = row[5]
                    if row is not None and row[:5] == (True, "Lock", "advisory", True, True):
                        observed_real_wait = True
                        break
                    if second_done.is_set():
                        break
                    second_done.wait(0.005)
                assert observed_real_wait, "Second independent backend was not observed waiting on the first lock"
                assert not second_done.is_set() and results == [None, None]
                assert insertions == [[], []] and not release_first.is_set()
            finally:
                release_first.set()
                for thread in threads:
                    thread.join(timeout=8)
                alive = any(thread.is_alive() for thread in threads)
                if alive:
                    # A failed test may cancel only its observed runtime PIDs in
                    # this exact random target; cleanup never turns it green.
                    for pid, backend_start in backend_starts.items():
                        monitor.execute(
                            "SELECT pg_catalog.pg_cancel_backend(pid) FROM pg_catalog.pg_stat_activity "
                            "WHERE pid=%s AND backend_start=%s AND datname=current_database()",
                            (pid, backend_start),
                        )
                    for thread in threads:
                        thread.join(timeout=3)
                assert not alive, "A worker exceeded bounded join; attempted cancellation is not passing evidence"
                assert not any(thread.is_alive() for thread in threads), "A worker survived bounded failure cleanup"

            assert failures == [None, None], "The two real creation requests must both commit successfully"
            assert all(result is not None for result in results)
            assert results[0] == results[1]
            assert contexts[0] == contexts[1] and contexts[0] is not contexts[1]
            assert all(selected["reader"].calls >= 2 for selected in selected_environments)
            assert all(selected["fence"].finishes >= 1 for selected in selected_environments)
            event_receipts_after = monitor.execute("SELECT count(*) FROM mt.event_receipt").fetchone()
            assert event_receipts_after == event_receipts_before

        accepted = results[0]
        assert accepted is not None
        task_id = UUID(accepted["task_id"])
        assert accepted == {
            "task_id": str(task_id),
            "state": "QUEUED",
            "status_url": f"/api/v1/analysis/tasks/{task_id}/execution",
        }
        actual = task_rows(environment, task_id)
        material = first["reader"].observations[0]
        expected_nodes = material.materials.node_inputs
        actual_sizes = {table: len(rows) for table, rows in actual.items()}
        expected_sizes = {
            table: (0 if table == "task_result" else len(expected_nodes) if table == "task_node_run" else 1)
            for table in TABLES
        }
        assert actual_sizes == expected_sizes
        final_counts = counts(environment)
        expected_counts = {
            table: count + (0 if table == "task_result" else len(expected_nodes) if table == "task_node_run" else 1)
            for table, count in environment["initial_counts"].items()
        }
        assert final_counts == expected_counts
        for stored_rows in actual.values():
            for item in stored_rows:
                assert (item["org_id"], item["case_id"], item["created_by"]) == (
                    environment["org"],
                    environment["case"],
                    environment["user"],
                )
        assert insertions[0] == [
            "analysis_task",
            "task_run",
            "task_run_plan",
            *["task_node_run" for _ in expected_nodes],
            "task_event",
            "outbox_event",
            "audit_event",
            "idempotency_record",
        ]
        assert insertions[1] == [], "The actual advisory waiter must replay without a second write collection"
        stored = actual["idempotency_record"][0]
        receipt = stored["response_ref"]
        assert stored["idempotency_key"] == key and stored["request_sha256"] == contexts[0].request.request_sha256
        assert receipt["accepted"] == results[0] == results[1]
        assert receipt["etag"] == etag(results[0]) == etag(results[1])
        assert receipt["request_id"] == str(request_ids[0]) and receipt["request_id"] != str(request_ids[1])
        assert receipt["binding"]["revision_id"] == str(material.binding.revision_id)
        saved = actual["task_run_plan"][0]
        assert bytes(saved["request_body_bytes"]) == contexts[0].request.canonical_body
        assert saved["request_body_sha256"] == contexts[0].request.request_sha256
        assert saved["authorization_request_digest"] == contexts[0].authorization_request_digest
        assert saved["request_body_sha256"] != saved["authorization_request_digest"]
        assert (saved["revision_id"], saved["head_row_version"]) == (
            material.binding.revision_id,
            material.binding.head_row_version,
        )
        for kind in ("policy", "plan", "capability"):
            document = getattr(material.materials, kind)
            assert bytes(saved[kind + "_bytes"]) == document.canonical_bytes
            assert saved[kind + "_sha256"] == document.sha256
        assert bytes(saved["input_manifest_bytes"]) == environment["input_raw"]
        assert saved["input_sha256"] == sha(environment["input_raw"])
        assert bytes(saved["validation_receipt_bytes"]) == environment["receipt"]
        assert actual["task_event"][0]["request_id"] == request_ids[0]
        assert actual["audit_event"][0]["request_id"] == request_ids[0]
        outbox = actual["outbox_event"][0]
        assert outbox["event_id"] == actual["task_event"][0]["event_id"]
        assert outbox["payload"]["event_id"] == str(outbox["event_id"])
        assert outbox["payload"]["request_id"] == str(request_ids[0])
        assert outbox["topic"] == "workflow.run.accepted.v1" and outbox["published_at"] is None
        assert (outbox["aggregate_id"], outbox["aggregate_version"], outbox["attempts"]) == (task_id, 2, 0)
        assert actual["task_event"][0]["run_version"] == 1
        assert (actual["task_event"][0]["from_state"], actual["task_event"][0]["to_state"]) == ("CREATED", "QUEUED")
        assert outbox["payload"]["state"] == accepted["state"] == "QUEUED"
        task = actual["analysis_task"][0]
        assert (task["state"], task["progress"], task["row_version"], task["run_version"], task["result_version"]) == (
            "QUEUED",
            0,
            2,
            1,
            1,
        )
        assert task["report_eligibility"] == "draft_only" and task["missing_modalities"] == []
        assert actual["task_result"] == []
        assert {(row["node_code"], row["attempt"], row["input_hash"]) for row in actual["task_node_run"]} == {
            (node.document_id, 1, node.sha256) for node in expected_nodes
        }
        # Safe actual observations for the private JUnit receipt. No PID,
        # backend timestamp, database name, UUID, SQL or request is published.
        assert row is not None
        record_property("distinct_backend_connections", pids[0] is not None and pids[0] != pids[1])
        record_property("observed_same_lock_wait", observed_real_wait and row[1:3] == ("Lock", "advisory") and row[4])
        record_property("first_is_real_blocker", row[3] is True)
        record_property(
            "complete_collection_unique", actual_sizes == expected_sizes and final_counts == expected_counts
        )
        record_property("duplicate_writes_zero", insertions[1] == [] and final_counts == expected_counts)
