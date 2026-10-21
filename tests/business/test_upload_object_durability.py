"""Failed object directory barriers cannot publish business references."""

import errno
import hashlib
import os
import stat
from pathlib import Path
from uuid import UUID

import psycopg
import pytest
from business_app.types import Scope

from tests.business.http_fixtures import synthetic_upload_evidence
from tests.business.test_upload_validation import AUTH, complete, event, prepared_upload, worker
from tests.business.test_uploads import create, part
from tests.business.test_uploads import upload_client as upload_client


def fail_root_sync(root, monkeypatch):
    original = os.fsync

    def fail(descriptor):
        if stat.S_ISDIR(os.fstat(descriptor).st_mode):
            selected = Path(os.readlink(f"/proc/self/fd/{descriptor}"))
            if selected == root:
                raise OSError(errno.EIO, "synthetic-object-root-sync-failure")
        original(descriptor)

    monkeypatch.setattr(os, "fsync", fail)


def test_failed_part_durability_has_no_receipt_and_same_request_can_retry(upload_client, business_context, monkeypatch):
    context, http = business_context, upload_client
    upload = create(http, context)
    bound = Scope(context["actor"], context["case_id"])
    with monkeypatch.context() as fault:
        fail_root_sync(context["settings"].object_root, fault)
        with synthetic_upload_evidence(bound.actor, bound.case_id, UUID(upload)):
            with pytest.raises(OSError, match="synthetic-object-root-sync-failure"):
                http.app.state.upload_service.put_part(
                    bound, UUID(upload), 1, b"ABC", hashlib.sha256(b"ABC").hexdigest(), "part-1"
                )
    with psycopg.connect(context["admin_dsn"]) as connection:
        assert connection.execute("SELECT count(*) FROM mt.upload_part").fetchone() == (0,)
        assert connection.execute("SELECT count(*) FROM mt.object_version").fetchone() == (0,)
        assert connection.execute(
            "SELECT count(*) FROM mt.idempotency_record WHERE operation='putUploadPart'"
        ).fetchone() == (0,)
    assert http.get(f"/api/v1/uploads/{upload}", headers=AUTH).json()["received_parts_count"] == 0
    assert len(list(context["settings"].object_root.rglob("*.orphan.json"))) == 1
    assert part(http, upload, 1, b"ABC").status_code == 200
    assert http.get(f"/api/v1/uploads/{upload}", headers=AUTH).json()["received_parts_count"] == 1


def test_failed_merged_object_durability_keeps_validation_pending_then_retries(business_context, monkeypatch):
    context = business_context
    app, http, upload, descriptor = prepared_upload(context)
    try:
        assert complete(http, upload, descriptor).status_code == 202
        message = event(context, upload)
        with monkeypatch.context() as fault:
            fail_root_sync(context["settings"].object_root, fault)
            with pytest.raises(OSError, match="synthetic-object-root-sync-failure"):
                worker(app, context).consume_validation(message)
        with psycopg.connect(context["admin_dsn"]) as connection:
            assert connection.execute("SELECT count(*) FROM mt.media_asset").fetchone() == (0,)
            assert connection.execute("SELECT count(*) FROM mt.object_version").fetchone() == (1,)
        result = http.get(f"/api/v1/uploads/{upload}", headers=AUTH).json()
        assert result["session"]["state"] == "VALIDATING" and result["result"]["asset_id"] is None
        assert len(list(context["settings"].object_root.rglob("*.orphan.json"))) == 1
        worker(app, context).consume_validation(message)
        result = http.get(f"/api/v1/uploads/{upload}", headers=AUTH).json()
        assert result["session"]["state"] == "COMPLETED" and result["result"]["asset_id"] is not None
        with psycopg.connect(context["admin_dsn"]) as connection:
            assert connection.execute("SELECT count(*) FROM mt.media_asset").fetchone() == (1,)
    finally:
        http.__exit__(None, None, None)
