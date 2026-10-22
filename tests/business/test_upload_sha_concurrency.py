"""Distinct upload deliveries use independent connections and real transactions."""

import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack, contextmanager
from copy import copy
from threading import Event
from uuid import UUID, uuid4

import psycopg
import pytest
from sqlalchemy import event as sql_event

from tests.business.test_upload_validation import (
    AUTH,
    complete,
    event,
    prepared_upload,
    worker,
)


@contextmanager
def prepared_pair(context, second_context=None, second_data=None):
    with ExitStack() as cleanup:
        pair = []
        for selected, data in [
            (context, None),
            (second_context or context, second_data),
        ]:
            app, http, upload, descriptor = prepared_upload(selected, data)
            cleanup.callback(http.__exit__, None, None, None)
            assert complete(http, upload, descriptor, key=uuid4().hex).status_code == 202
            pair.append((app, http, upload, event(selected, upload)))
        assert pair[0][0].state.upload_service.database is not pair[1][0].state.upload_service.database
        assert pair[0][2] != pair[1][2] and pair[0][3]["event_id"] != pair[1][3]["event_id"]
        yield pair


def result(http, upload):
    response = http.get(f"/api/v1/uploads/{upload}", headers=AUTH)
    assert response.status_code == 200
    value = response.json()
    assert value["session"]["state"] == "COMPLETED"
    payload = dict(value["result"])
    assert UUID(payload.pop("request_id"))
    return payload


def additional_source(context, *, other_case=False):
    from business_app.types import Scope

    selected = dict(context, source_id=uuid4())
    actor = context["actor"]
    if other_case:
        selected["case_id"] = uuid4()
        selected["authority"] = copy(context["authority"])
        original = context["authority"].authorize_case

        def authorize_case(current_actor, case_id, action):
            if current_actor == actor and case_id == selected["case_id"]:
                return Scope(actor, case_id)
            return original(current_actor, case_id, action)

        selected["authority"].authorize_case = authorize_case
    with psycopg.connect(context["admin_dsn"]) as connection:
        if other_case:
            connection.execute(
                "INSERT INTO mt.cases(case_id,org_id,display_code,status) VALUES(%s,%s,%s,'ACTIVE')",
                (selected["case_id"], actor.org_id, uuid4().hex),
            )
            connection.execute(
                "INSERT INTO mt.case_membership(membership_id,case_id,org_id,user_id) VALUES(%s,%s,%s,%s)",
                (uuid4(), selected["case_id"], actor.org_id, actor.user_id),
            )
        connection.execute(
            """INSERT INTO mt.source_registry(source_id,org_id,case_id,name,source_type,authorization_ref,purpose,authorization_status,authorization_version)
            VALUES(%s,%s,%s,'synthetic','synthetic','fixture-not-formal-authority',ARRAY['upload','analysis'],'verified','test-version-1')""",
            (selected["source_id"], actor.org_id, selected["case_id"]),
        )
    return selected


@pytest.mark.parametrize("different_source", [False, True], ids=["same-source", "authorized-other-source"])
@pytest.mark.parametrize("rollback_first", [False, True], ids=["commit", "rollback"])
def test_distinct_uploads_same_sha_associate_after_concurrent_transaction(
    business_context, rollback_first, different_source
):
    # Removing transaction-level serialization must leave both duplicate_of values
    # null in the commit case. A rollback must never expose the uncommitted asset.
    second_context = additional_source(business_context) if different_source else business_context
    with prepared_pair(business_context, second_context) as pair:
        first, second = pair
        first_paused, release_first, second_looked = Event(), Event(), Event()
        second_pid: list[int] = []
        engines = [item[0].state.upload_service.database.engine for item in pair]

        def pause_first(connection, cursor, statement, parameters, context, executemany):
            if statement.startswith("INSERT INTO mt.media_asset("):
                first_paused.set()
                assert release_first.wait(8), "controller did not release the first upload"
                if rollback_first:
                    raise RuntimeError("ISOLATED_TEST_ROLLBACK")

        def record_second(connection, cursor, statement, parameters, context, executemany):
            if not second_pid:
                second_pid.append(connection.connection.driver_connection.info.backend_pid)

        def observe_second(connection, cursor, statement, parameters, context, executemany):
            if statement.startswith("SELECT asset_id,source_id FROM mt.media_asset"):
                second_looked.set()

        sql_event.listen(engines[0], "before_cursor_execute", pause_first)
        sql_event.listen(engines[1], "before_cursor_execute", record_second)
        sql_event.listen(engines[1], "after_cursor_execute", observe_second)
        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                future_first = pool.submit(worker(first[0], business_context).consume_validation, first[3])
                try:
                    assert first_paused.wait(8), "first worker did not reach its real asset insert"
                    future_second = pool.submit(worker(second[0], second_context).consume_validation, second[3])
                    observed_overlap = False
                    deadline = time.monotonic() + 5
                    with psycopg.connect(business_context["admin_dsn"], autocommit=True) as monitor:
                        while time.monotonic() < deadline:
                            if second_looked.is_set():
                                observed_overlap = True
                                break
                            if second_pid:
                                state = monitor.execute(
                                    "SELECT wait_event_type,wait_event FROM pg_stat_activity WHERE pid=%s",
                                    (second_pid[0],),
                                ).fetchone()
                                if state == ("Lock", "advisory"):
                                    observed_overlap = True
                                    break
                            if future_second.done():
                                future_second.result()
                                break
                            second_looked.wait(0.01)
                    assert observed_overlap, "second independent worker never overlapped the first transaction"
                finally:
                    release_first.set()
                if rollback_first:
                    with pytest.raises(RuntimeError, match="ISOLATED_TEST_ROLLBACK"):
                        future_first.result(timeout=8)
                else:
                    future_first.result(timeout=8)
                future_second.result(timeout=8)
        finally:
            release_first.set()
            sql_event.remove(engines[0], "before_cursor_execute", pause_first)
            sql_event.remove(engines[1], "before_cursor_execute", record_second)
            sql_event.remove(engines[1], "after_cursor_execute", observe_second)

        second_result = result(second[1], second[2])
        if rollback_first:
            assert second_result["duplicate_of"] is None
            first_response = first[1].get(f"/api/v1/uploads/{first[2]}", headers=AUTH).json()
            assert first_response["session"]["state"] == "VALIDATING"
            assert first_response["result"]["asset_id"] is None
            assert len(list(business_context["settings"].object_root.rglob("*.orphan.json"))) == 1
            worker(first[0], business_context).consume_validation(first[3])
            first_result = result(first[1], first[2])
            assert first_result["duplicate_of"] == second_result["asset_id"]
        else:
            first_result = result(first[1], first[2])
            assert first_result["duplicate_of"] is None
            assert second_result["duplicate_of"] == first_result["asset_id"]
            assert not list(business_context["settings"].object_root.rglob("*.orphan.json"))

        # Both originals and their immutable object versions remain distinct;
        # replaying either durable event creates no extra asset or object.
        with psycopg.connect(business_context["admin_dsn"]) as connection:
            rows = connection.execute(
                "SELECT asset_id,object_id,source_id,sha256 FROM mt.media_asset ORDER BY asset_id"
            ).fetchall()
            objects_before = connection.execute(
                "SELECT object_id,version_id,sha256 FROM mt.object_version ORDER BY object_id"
            ).fetchall()
        files_before = {path: path.read_bytes() for path in business_context["settings"].object_root.rglob("*.bin")}
        assert len(rows) == 2 and len({row[1] for row in rows}) == 2 and len({row[3] for row in rows}) == 1
        assert {row[2] for row in rows} == {
            business_context["source_id"],
            second_context["source_id"],
        }
        assert first_result["asset_id"] != second_result["asset_id"]
        for (app, _, _, message), selected in zip(pair, [business_context, second_context]):
            worker(app, selected).consume_validation(message)
        assert result(first[1], first[2]) == first_result
        assert result(second[1], second[2]) == second_result
        with psycopg.connect(business_context["admin_dsn"]) as connection:
            assert connection.execute("SELECT count(*) FROM mt.media_asset").fetchone() == (2,)
            assert (
                connection.execute(
                    "SELECT object_id,version_id,sha256 FROM mt.object_version ORDER BY object_id"
                ).fetchall()
                == objects_before
            )
        assert {
            path: path.read_bytes() for path in business_context["settings"].object_root.rglob("*.bin")
        } == files_before


@pytest.mark.parametrize("boundary", ["different-sha", "different-case"])
def test_unrelated_upload_completes_while_first_sha_transaction_is_open(business_context, boundary):
    # A global/case-only lock would block unrelated content; a SHA-only lock
    # would couple equal bytes across cases. Neither may publish a duplicate.
    import io

    from PIL import Image

    second_context = business_context
    data = None
    if boundary == "different-case":
        second_context = additional_source(business_context, other_case=True)
    else:
        buffer = io.BytesIO()
        Image.new("RGB", (8, 8), "black").save(buffer, format="PNG")
        data = buffer.getvalue()
    with prepared_pair(business_context, second_context, data) as pair:
        first, second = pair
        paused, release = Event(), Event()
        engine = first[0].state.upload_service.database.engine

        def pause(connection, cursor, statement, parameters, context, executemany):
            if statement.startswith("INSERT INTO mt.media_asset("):
                paused.set()
                assert release.wait(8), "first upload was not released"

        sql_event.listen(engine, "before_cursor_execute", pause)
        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                first_future = pool.submit(worker(first[0], business_context).consume_validation, first[3])
                try:
                    assert paused.wait(8)
                    second_future = pool.submit(worker(second[0], second_context).consume_validation, second[3])
                    second_future.result(timeout=5)
                    assert result(second[1], second[2])["duplicate_of"] is None
                finally:
                    release.set()
                first_future.result(timeout=8)
        finally:
            release.set()
            sql_event.remove(engine, "before_cursor_execute", pause)
        assert result(first[1], first[2])["duplicate_of"] is None
        assert result(second[1], second[2])["duplicate_of"] is None


def test_sha_lock_timeout_rolls_back_and_keeps_retry_and_orphan_recovery(
    business_context,
):
    # A lock timeout must propagate, never publish an unassociated success or
    # discard the already durable object that the orphan recovery path needs.
    from sqlalchemy.exc import DBAPIError

    with prepared_pair(business_context) as pair:
        first, second = pair
        paused, release = Event(), Event()
        first_engine = first[0].state.upload_service.database.engine
        second_engine = second[0].state.upload_service.database.engine
        configured = False

        def pause(connection, cursor, statement, parameters, context, executemany):
            if statement.startswith("INSERT INTO mt.media_asset("):
                paused.set()
                assert release.wait(8), "first upload was not released"

        def bounded_statement(connection, cursor, statement, parameters, context, executemany):
            nonlocal configured
            if not configured:
                cursor.execute("SET LOCAL statement_timeout='100ms'")
                configured = True

        sql_event.listen(first_engine, "before_cursor_execute", pause)
        sql_event.listen(second_engine, "before_cursor_execute", bounded_statement)
        try:
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(worker(first[0], business_context).consume_validation, first[3])
                try:
                    assert paused.wait(8)
                    with pytest.raises(DBAPIError) as failure:
                        worker(second[0], business_context).consume_validation(second[3])
                    assert isinstance(failure.value.orig, psycopg.errors.QueryCanceled)
                    assert failure.value.orig.sqlstate == "57014"
                finally:
                    release.set()
                future.result(timeout=8)
        finally:
            release.set()
            sql_event.remove(first_engine, "before_cursor_execute", pause)
            sql_event.remove(second_engine, "before_cursor_execute", bounded_statement)
        response = second[1].get(f"/api/v1/uploads/{second[2]}", headers=AUTH).json()
        assert response["session"]["state"] == "VALIDATING" and response["result"]["asset_id"] is None
        with psycopg.connect(business_context["admin_dsn"]) as connection:
            assert connection.execute("SELECT count(*) FROM mt.media_asset").fetchone() == (1,)
        assert len(list(business_context["settings"].object_root.rglob("*.orphan.json"))) == 1
        worker(second[0], business_context).consume_validation(second[3])
        assert result(second[1], second[2])["duplicate_of"] == result(first[1], first[2])["asset_id"]
