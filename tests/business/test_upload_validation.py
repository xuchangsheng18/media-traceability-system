import hashlib
import io
import json
import os
from dataclasses import replace
from pathlib import Path
from uuid import UUID, uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient
from PIL import Image

AUTH = {"Authorization": "Bearer test-only-valid-token"}


def test_truncated_jpeg_never_becomes_valid():
    from business_app.uploads.validator import inspect_uploaded_media

    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), "white").save(buffer, format="JPEG")
    data = buffer.getvalue()[:-2]
    assert inspect_uploaded_media(data, hashlib.sha256(data).hexdigest(), "image/jpeg") is None


def test_corrupted_fixed_part_is_rejected_not_retried_forever(business_context):
    app, http, upload, descriptor = prepared_upload(business_context)
    assert complete(http, upload, descriptor).status_code == 202
    file = next(business_context["settings"].object_root.rglob("*.bin"))
    file.write_bytes(b"corrupted-self-owned-test")
    worker(app, business_context).consume_validation(event(business_context, upload))
    response = http.get(f"/api/v1/uploads/{upload}", headers=AUTH).json()
    assert response["session"]["state"] == "REJECTED" and response["result"]["asset_id"] is None
    http.__exit__(None, None, None)


def test_worker_database_failure_records_private_orphan(business_context):
    from sqlalchemy.exc import SQLAlchemyError

    app, http, upload, descriptor = prepared_upload(business_context)
    assert complete(http, upload, descriptor).status_code == 202
    with psycopg.connect(business_context["admin_dsn"]) as connection:
        connection.execute("REVOKE INSERT ON mt.media_asset FROM mt_runtime")
    with pytest.raises(SQLAlchemyError):
        worker(app, business_context).consume_validation(event(business_context, upload))
    with psycopg.connect(business_context["admin_dsn"]) as connection:
        connection.execute("GRANT INSERT ON mt.media_asset TO mt_runtime")
        assert scalar(connection, "SELECT count(*) FROM mt.media_asset") == 0
    assert len(list(business_context["settings"].object_root.rglob("*.orphan.json"))) == 1
    http.__exit__(None, None, None)


def test_duplicate_source_revocation_hides_reference(business_context):
    previous_source = uuid4()
    with psycopg.connect(business_context["admin_dsn"]) as connection:
        connection.execute(
            """INSERT INTO mt.source_registry(source_id,org_id,case_id,name,source_type,authorization_ref,purpose,authorization_status,authorization_version)
        VALUES(%s,%s,%s,'test-only','test-only','test-only',ARRAY['upload','analysis'],'verified','test-version-1')""",
            (previous_source, business_context["actor"].org_id, business_context["case_id"]),
        )
    previous = dict(business_context, source_id=previous_source)
    app, http, upload, descriptor = prepared_upload(previous)
    assert complete(http, upload, descriptor, key=uuid4().hex).status_code == 202
    worker(app, previous).consume_validation(event(previous, upload))
    asset = http.get(f"/api/v1/uploads/{upload}", headers=AUTH).json()["result"]["asset_id"]
    http.__exit__(None, None, None)
    app, http, upload, descriptor = prepared_upload(business_context)
    assert complete(http, upload, descriptor, key=uuid4().hex).status_code == 202
    worker(app, business_context).consume_validation(event(business_context, upload))
    assert http.get(f"/api/v1/uploads/{upload}", headers=AUTH).json()["result"]["duplicate_of"] == asset
    with psycopg.connect(business_context["admin_dsn"]) as connection:
        connection.execute(
            "UPDATE mt.source_registry SET authorization_status='revoked' WHERE source_id=%s", (previous_source,)
        )
    assert http.get(f"/api/v1/uploads/{upload}", headers=AUTH).json()["result"]["duplicate_of"] is None
    http.__exit__(None, None, None)


def scalar(connection, statement, parameters=None):
    row = connection.execute(statement, parameters).fetchone()
    assert row is not None
    return row[0]


def prepared_upload(context, data=None):
    from business_app.main import create_app

    if data is None:
        buffer = io.BytesIO()
        Image.new("RGB", (8, 8), "white").save(buffer, format="PNG")
        data = buffer.getvalue()
    settings = replace(context["settings"], part_size_bytes=len(data))
    app = create_app(settings, context["authority"])
    http = TestClient(app)
    http.__enter__()
    response = http.post(
        "/api/v1/uploads",
        json={
            "case_id": str(context["case_id"]),
            "source_id": str(context["source_id"]),
            "filename": "synthetic.png",
            "size_bytes": len(data),
            "mime": "image/png",
            "sha256": hashlib.sha256(data).hexdigest(),
        },
        headers={**AUTH, "Idempotency-Key": uuid4().hex},
    )
    assert response.status_code == 201
    upload = response.json()["upload_id"]
    descriptor = {"part_no": 1, "sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data)}
    assert (
        http.put(
            f"/api/v1/uploads/{upload}/parts/1",
            content=data,
            headers={
                **AUTH,
                "Idempotency-Key": uuid4().hex,
                "X-Part-Sha256": descriptor["sha256"],
                "Content-Length": str(len(data)),
            },
        ).status_code
        == 200
    )
    return app, http, upload, descriptor


def complete(http, upload, descriptor, key="complete-once"):
    return http.post(
        f"/api/v1/uploads/{upload}/complete", json={"parts": [descriptor]}, headers={**AUTH, "Idempotency-Key": key}
    )


def event(context, upload):
    with psycopg.connect(context["admin_dsn"]) as connection:
        row = connection.execute("SELECT payload FROM mt.outbox_event WHERE aggregate_id=%s", (upload,)).fetchone()
    assert row is not None
    return row[0]


def worker(app, context):
    from business_app.uploads.worker import UploadValidationWorker

    return UploadValidationWorker(app.state.upload_service, context["authority"])


def test_complete_enqueues_once(business_context):
    app, http, upload, descriptor = prepared_upload(business_context)
    try:
        first = complete(http, upload, descriptor)
        second = complete(http, upload, descriptor)
        assert first.status_code == second.status_code == 202
        assert first.json() == second.json()
        assert first.json()["validation"] == "VALIDATING" and first.json()["asset_id"] is None
        with psycopg.connect(business_context["admin_dsn"]) as connection:
            assert scalar(connection, "SELECT count(*) FROM mt.outbox_event WHERE aggregate_id=%s", (upload,)) == 1
    finally:
        http.__exit__(None, None, None)


def test_full_digest_mismatch_rejects_asset(business_context):
    app, http, upload, descriptor = prepared_upload(business_context)
    try:
        with psycopg.connect(business_context["admin_dsn"]) as connection:
            connection.execute("UPDATE mt.upload_session SET sha256=%s WHERE upload_id=%s", ("0" * 64, upload))
        assert complete(http, upload, descriptor).status_code == 202
        worker(app, business_context).consume_validation(event(business_context, upload))
        result = http.get(f"/api/v1/uploads/{upload}", headers=AUTH).json()
        assert result["session"]["state"] == "REJECTED" and result["result"]["asset_id"] is None
    finally:
        http.__exit__(None, None, None)


def test_duplicate_event_does_not_duplicate_asset(business_context):
    app, http, upload, descriptor = prepared_upload(business_context)
    try:
        assert complete(http, upload, descriptor).status_code == 202
        message = event(business_context, upload)
        consumer = worker(app, business_context)
        consumer.consume_validation(message)
        consumer.consume_validation(message)
        result = http.get(f"/api/v1/uploads/{upload}", headers=AUTH).json()
        assert result["session"]["state"] == "COMPLETED" and result["result"]["validation"] == "VALID"
        assert UUID(result["result"]["asset_id"])
        with psycopg.connect(business_context["admin_dsn"]) as connection:
            assert scalar(connection, "SELECT count(*) FROM mt.media_asset") == 1
    finally:
        http.__exit__(None, None, None)


def test_stale_version_cannot_overwrite_terminal(business_context):
    app, http, upload, descriptor = prepared_upload(business_context)
    try:
        assert complete(http, upload, descriptor).status_code == 202
        message = event(business_context, upload)
        consumer = worker(app, business_context)
        consumer.consume_validation(message)
        stale = dict(message, session_version=message["session_version"] + 1)
        from business_app.errors import BusinessError

        with pytest.raises(BusinessError):
            consumer.consume_validation(stale)
        assert http.get(f"/api/v1/uploads/{upload}", headers=AUTH).json()["session"]["state"] == "COMPLETED"
    finally:
        http.__exit__(None, None, None)


def test_source_revoked_before_validation(business_context):
    app, http, upload, descriptor = prepared_upload(business_context)
    try:
        assert complete(http, upload, descriptor).status_code == 202
        message = event(business_context, upload)
        with psycopg.connect(business_context["admin_dsn"]) as connection:
            connection.execute(
                "UPDATE mt.source_registry SET authorization_status='revoked' WHERE source_id=%s",
                (business_context["source_id"],),
            )
        from business_app.errors import BusinessError

        with pytest.raises(BusinessError):
            worker(app, business_context).consume_validation(message)
        with psycopg.connect(business_context["admin_dsn"]) as connection:
            assert scalar(connection, "SELECT count(*) FROM mt.media_asset") == 0
    finally:
        http.__exit__(None, None, None)


def test_authority_outage_keeps_pending(business_context):
    app, http, upload, descriptor = prepared_upload(business_context)
    try:
        assert complete(http, upload, descriptor).status_code == 202
        from business_app.errors import BusinessError
        from business_app.uploads.worker import UploadValidationWorker

        with pytest.raises(BusinessError):
            UploadValidationWorker(app.state.upload_service, None).consume_validation(event(business_context, upload))
        assert http.get(f"/api/v1/uploads/{upload}", headers=AUTH).json()["session"]["state"] == "VALIDATING"
    finally:
        http.__exit__(None, None, None)


def test_missing_part_rejects_complete(business_context):
    app, http, upload, descriptor = prepared_upload(business_context)
    try:
        wrong = dict(descriptor, part_no=2)
        assert complete(http, upload, wrong).status_code == 422
        with psycopg.connect(business_context["admin_dsn"]) as connection:
            assert scalar(connection, "SELECT count(*) FROM mt.outbox_event") == 0
    finally:
        http.__exit__(None, None, None)


def test_real_broker_receives_and_worker_commits(business_context):
    app, http, upload, descriptor = prepared_upload(business_context)
    try:
        assert complete(http, upload, descriptor).status_code == 202
        source = Path(__file__).resolve().parents[2] / "backend/business_app/uploads/messaging.py"
        assert source.is_file(), "confirmed actual broker delivery is not implemented"
        from business_app.types import Scope
        from business_app.uploads.messaging import pump_outbox_once

        url = os.environ.get("MT_BUSINESS_TEST_BROKER_URL")
        private = (
            Path(os.environ.get("MT_RUNTIME_DIR", "/workspace/glwy/runtime/media-traceability-system"))
            / "business-test-broker-private.json"
        )
        if not url and private.is_file():
            url = json.loads(private.read_text())["url"]
        assert url, "explicit isolated test broker is required"
        result = pump_outbox_once(
            app.state.upload_service,
            business_context["authority"],
            Scope(business_context["actor"], business_context["case_id"]),
            url,
        )
        assert result == {"published": 1, "consumed": 1, "confirmed": True}
        assert http.get(f"/api/v1/uploads/{upload}", headers=AUTH).json()["session"]["state"] == "COMPLETED"
    finally:
        http.__exit__(None, None, None)


def test_broker_recovers_after_confirmation_before_outbox_commit(business_context):
    from business_app.types import Scope
    from business_app.uploads.messaging import pump_outbox_once
    from sqlalchemy import event as sql_events

    app, http, upload, descriptor = prepared_upload(business_context)
    try:
        assert complete(http, upload, descriptor).status_code == 202
        private = (
            Path(os.environ.get("MT_RUNTIME_DIR", "/workspace/glwy/runtime/media-traceability-system"))
            / "business-test-broker-private.json"
        )
        url = os.environ.get("MT_BUSINESS_TEST_BROKER_URL") or json.loads(private.read_text())["url"]
        engine = app.state.business_database.engine

        def interrupt_receipt(connection, cursor, statement, parameters, context, executemany):
            if "UPDATE mt.outbox_event SET published_at" in statement:
                raise RuntimeError("injected-publisher-receipt-interruption")

        sql_events.listen(engine, "before_cursor_execute", interrupt_receipt)
        try:
            with pytest.raises(RuntimeError, match="injected-publisher"):
                pump_outbox_once(
                    app.state.upload_service,
                    business_context["authority"],
                    Scope(business_context["actor"], business_context["case_id"]),
                    url,
                )
        finally:
            sql_events.remove(engine, "before_cursor_execute", interrupt_receipt)
        result = pump_outbox_once(
            app.state.upload_service,
            business_context["authority"],
            Scope(business_context["actor"], business_context["case_id"]),
            url,
        )
        assert result["published"] == 1 and result["consumed"] == 2
        with psycopg.connect(business_context["admin_dsn"]) as connection:
            row = connection.execute("SELECT count(*) FROM mt.media_asset").fetchone()
            assert row is not None and row[0] == 1
    finally:
        http.__exit__(None, None, None)


def test_complete_key_is_bound_to_upload_id(business_context):
    app1, http1, upload1, descriptor1 = prepared_upload(business_context)
    app2, http2, upload2, descriptor2 = prepared_upload(business_context)
    try:
        assert complete(http1, upload1, descriptor1, "shared-key").status_code == 202
        assert complete(http2, upload2, descriptor2, "shared-key").status_code == 409
    finally:
        http1.__exit__(None, None, None)
        http2.__exit__(None, None, None)


def test_session_expiry_before_worker_does_not_create_asset(business_context):
    app, http, upload, descriptor = prepared_upload(business_context)
    try:
        assert complete(http, upload, descriptor).status_code == 202
        message = event(business_context, upload)
        with psycopg.connect(business_context["admin_dsn"]) as connection:
            connection.execute(
                "UPDATE mt.upload_session SET expires_at=now()-interval '1 second' WHERE upload_id=%s", (upload,)
            )
        worker(app, business_context).consume_validation(message)
        result = http.get(f"/api/v1/uploads/{upload}", headers=AUTH).json()
        assert result["session"]["state"] == "EXPIRED" and result["result"] is None
        with psycopg.connect(business_context["admin_dsn"]) as connection:
            assert scalar(connection, "SELECT count(*) FROM mt.media_asset") == 0
    finally:
        http.__exit__(None, None, None)
