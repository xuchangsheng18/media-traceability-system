"""A real post-write rollback releases one same-key waiter; synthetic trust only."""

import re
import time
from contextlib import ExitStack
from threading import Event, Thread
from typing import Any
from uuid import UUID, uuid4

import psycopg
from business_app.controls.common import etag
from business_app.db import Database
from sqlalchemy import event, text

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


def test_post_write_holder_rollback_allows_only_the_real_waiter_to_create(creation_environment, record_property):
    environment = creation_environment
    first_paused, release_first, second_attempted = Event(), Event(), Event()
    acquired_first, second_done, confirmed_wait, first_write_verified = Event(), Event(), Event(), Event()
    pids: list[int | None] = [None, None]
    backend_starts: dict[int, Any] = {}
    second_issued_at: list[float] = []
    successful_insertions: list[list[str]] = [[], []]
    rolled_back_task_ids: list[UUID] = []
    injected_failure = RuntimeError("SELF_OWNED_C02_POST_WRITE_ROLLBACK")
    failure_injections: list[BaseException] = []
    results: list[dict[str, Any] | None] = [None, None]
    failures: list[BaseException | None] = [None, None]
    contexts: list[Any] = [None, None]
    request_ids = [uuid4(), uuid4()]
    key = "self-owned-concurrent-rollback-" + uuid4().hex
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
            if index == 0 and statement.startswith("INSERT INTO mt.task_run("):
                assert first_write_verified.is_set() and successful_insertions[0] == ["analysis_task"]
                assert confirmed_wait.is_set() and release_first.is_set()
                assert len(rolled_back_task_ids) == 1 and not failure_injections
                failure_injections.append(injected_failure)
                raise injected_failure

        return observe

    def after(index):
        def observe(connection, cursor, statement, parameters, execution_context, many):
            if statement.startswith("SELECT pg_advisory_xact_lock("):
                backend_pid(connection, index)
                if index == 0:
                    acquired_first.set()
            match = re.match(r"\s*INSERT\s+INTO\s+mt\.([a-z_]+)\b", statement, re.IGNORECASE)
            if not match:
                return
            assert cursor.rowcount == 1, "Record successful real INSERTs, never just attempts"
            successful_insertions[index].append(match[1])
            if index == 0 and match[1] == "analysis_task":
                assert acquired_first.is_set(), "First pause must follow real advisory acquisition and a write"
                assert successful_insertions[0] == ["analysis_task"]
                identifier = parameters["task"]
                assert type(identifier) is UUID and identifier.int != 0
                rolled_back_task_ids.append(identifier)
                # Observe the real uncommitted row on its own writer root.
                written = connection.execute(
                    text("SELECT state,row_version,run_version FROM mt.analysis_task WHERE task_id=:task"),
                    {"task": identifier},
                ).one()
                assert tuple(written) == ("CREATED", 1, 1)
                first_write_verified.set()
                first_paused.set()
                assert release_first.wait(8), "Controller did not release the post-write real transaction"

        return observe

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
        for index, selected in enumerate(selected_environments):
            listener = after(index)
            event.listen(selected["database"].engine, "after_cursor_execute", listener)
            cleanup.callback(event.remove, selected["database"].engine, "after_cursor_execute", listener)

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
                assert first_paused.wait(5), "First worker never completed its real task INSERT before pausing"
                assert first_write_verified.is_set() and successful_insertions == [["analysis_task"], []]
                assert not release_first.is_set() and not failure_injections
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
                        confirmed_wait.set()
                        break
                    if second_done.is_set():
                        break
                    second_done.wait(0.005)
                assert observed_real_wait, "Second independent backend was not observed waiting on the first lock"
                assert not second_done.is_set() and results == [None, None]
                assert first_write_verified.is_set() and successful_insertions == [["analysis_task"], []]
                assert not release_first.is_set() and not failure_injections
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

            assert failure_injections == [injected_failure]
            assert failures[0] is injected_failure, "The exact injected post-write failure must propagate unchanged"
            assert results[0] is None and failures[1] is None and results[1] is not None
            assert first["reader"].calls == 1 and first["fence"].finishes == 0
            assert second["reader"].calls >= 2 and second["fence"].finishes >= 1
            assert contexts[0] == contexts[1] and contexts[0] is not contexts[1]
            event_receipts_after = monitor.execute("SELECT count(*) FROM mt.event_receipt").fetchone()
            assert event_receipts_after == event_receipts_before

        accepted = results[1]
        assert accepted is not None
        task_id = UUID(accepted["task_id"])
        assert len(rolled_back_task_ids) == 1 and task_id != rolled_back_task_ids[0]
        assert accepted == {
            "task_id": str(task_id),
            "state": "QUEUED",
            "status_url": f"/api/v1/analysis/tasks/{task_id}/execution",
        }
        actual = task_rows(environment, task_id)
        material = second["reader"].observations[0]
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
        assert successful_insertions[0] == ["analysis_task"]
        assert successful_insertions[1] == [
            "analysis_task",
            "task_run",
            "task_run_plan",
            *["task_node_run" for _ in expected_nodes],
            "task_event",
            "outbox_event",
            "audit_event",
            "idempotency_record",
        ]
        stored = actual["idempotency_record"][0]
        receipt = stored["response_ref"]
        assert stored["idempotency_key"] == key and stored["request_sha256"] == contexts[0].request.request_sha256
        assert receipt["accepted"] == results[1]
        assert receipt["etag"] == etag(results[1])
        assert receipt["request_id"] == str(request_ids[1]) and receipt["request_id"] != str(request_ids[0])
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
        assert actual["task_event"][0]["request_id"] == request_ids[1]
        assert actual["audit_event"][0]["request_id"] == request_ids[1]
        outbox = actual["outbox_event"][0]
        assert outbox["event_id"] == actual["task_event"][0]["event_id"]
        assert outbox["payload"]["event_id"] == str(outbox["event_id"])
        assert outbox["payload"]["request_id"] == str(request_ids[1])
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
        # A separate committed-state connection must find the actual failed
        # task and failed request absent from every related write set.
        with psycopg.connect(
            environment["admin_dsn"], autocommit=True, connect_timeout=2, options="-c statement_timeout=1000"
        ) as verifier:
            first_task = rolled_back_task_ids[0]
            failed_collection_counts = {}
            for table in ("analysis_task", "task_run", "task_run_plan", "task_node_run", "task_event", "task_result"):
                observed = verifier.execute(
                    "SELECT count(*) FROM mt." + table + " WHERE task_id=%s", (first_task,)
                ).fetchone()
                assert observed is not None
                failed_collection_counts[table] = observed[0]
            for table, column in (("outbox_event", "aggregate_id"), ("audit_event", "object_id")):
                observed = verifier.execute(
                    "SELECT count(*) FROM mt." + table + " WHERE " + column + "=%s", (first_task,)
                ).fetchone()
                assert observed is not None
                failed_collection_counts[table] = observed[0]
            observed = verifier.execute(
                "SELECT count(*) FROM mt.idempotency_record WHERE operation='createTask' "
                "AND case_id=%s AND actor_id=%s AND response_ref->>'task_id'=%s",
                (environment["case"], environment["user"], str(first_task)),
            ).fetchone()
            assert observed is not None
            failed_collection_counts["idempotency_record"] = observed[0]
            assert set(failed_collection_counts) == set(TABLES)
            assert all(value == 0 for value in failed_collection_counts.values())
            failed_request_counts = {}
            for table in ("task_event", "audit_event"):
                observed = verifier.execute(
                    "SELECT count(*) FROM mt." + table + " WHERE request_id=%s", (request_ids[0],)
                ).fetchone()
                assert observed is not None
                failed_request_counts[table] = observed[0]
            for table, json_column in (("outbox_event", "payload"), ("idempotency_record", "response_ref")):
                observed = verifier.execute(
                    "SELECT count(*) FROM mt." + table + " WHERE " + json_column + "->>'request_id'=%s",
                    (str(request_ids[0]),),
                ).fetchone()
                assert observed is not None
                failed_request_counts[table] = observed[0]
            assert all(value == 0 for value in failed_request_counts.values())

        # Fixed booleans only: never expose the private backend or request IDs.
        assert row is not None
        record_property("distinct_backend_connections", pids[0] is not None and pids[0] != pids[1])
        record_property("observed_same_lock_wait", observed_real_wait and row[1:3] == ("Lock", "advisory") and row[4])
        record_property("first_is_real_blocker", row[3] is True)
        record_property(
            "holder_real_write_observed",
            first_write_verified.is_set() and successful_insertions[0] == ["analysis_task"],
        )
        record_property(
            "holder_failure_propagated", failures[0] is injected_failure and failure_injections == [injected_failure]
        )
        record_property(
            "failed_holder_collection_absent",
            all(value == 0 for value in failed_collection_counts.values())
            and all(value == 0 for value in failed_request_counts.values()),
        )
        record_property(
            "waiter_complete_collection_unique", actual_sizes == expected_sizes and final_counts == expected_counts
        )
        record_property(
            "waiter_request_owns_acceptance",
            receipt["request_id"] == str(request_ids[1])
            and receipt["accepted"] == results[1]
            and receipt["etag"] == etag(results[1]),
        )
