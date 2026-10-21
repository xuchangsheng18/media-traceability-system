"""Real RabbitMQ deliveries handled by a fresh Python worker process."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlsplit
from uuid import UUID

import psycopg
import pytest
from kombu import Connection, Exchange, Queue

from tests.business.test_upload_validation import complete, prepared_upload


def broker_url():
    private = (
        Path(os.environ.get("MT_RUNTIME_DIR", "/workspace/glwy/runtime/media-traceability-system"))
        / "business-test-broker-private.json"
    )
    url = os.environ.get("MT_BUSINESS_TEST_BROKER_URL")
    if not url and private.is_file():
        url = json.loads(private.read_text())["url"]
    assert url and urlsplit(url).hostname in {"127.0.0.1", "localhost", "::1"}, "isolated loopback broker required"
    return url


@pytest.fixture
def process_upload(business_context, tmp_path):
    context = business_context
    app, http, upload, descriptor = prepared_upload(context)
    config = tmp_path / "worker-private.json"
    url = broker_url()
    name = "mt_business_validation_" + context["case_id"].hex
    queue = Queue(
        name,
        exchange=Exchange("mt_business_validation", type="direct", durable=True),
        routing_key=name,
        durable=True,
    )
    payload = dict(
        dsn=str(context["settings"].database_dsn),
        broker=url,
        object_root=str(context["settings"].object_root),
        fixture_root=str(tmp_path),
        actor=str(context["actor"].user_id),
        org=str(context["actor"].org_id),
        case=str(context["case_id"]),
        upload=upload,
    )
    # business_context and this fixture share the test's tmp_path.
    descriptor_fd = os.open(config, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor_fd, "w") as stream:
        json.dump(payload, stream)
    os.chmod(config, 0o600)

    def child(mode, expected=0, upload_id=None):
        selected_config = config
        if upload_id is not None:
            selected_config = tmp_path / ("worker-private-" + UUID(str(upload_id)).hex + ".json")
            descriptor_fd = os.open(selected_config, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor_fd, "w") as stream:
                json.dump(dict(payload, upload=str(upload_id)), stream)
            os.chmod(selected_config, 0o600)
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "tests.business.upload_worker_process_fixture",
                str(selected_config),
                mode,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            try:
                stdout, stderr = process.communicate(timeout=40)
            except subprocess.TimeoutExpired:
                pytest.fail("isolated worker child timed out")
            diagnostic = "no sanitized error code"
            if stdout:
                try:
                    reported = json.loads(stdout)
                    code = reported.get("error") if isinstance(reported, dict) else None
                    if (
                        isinstance(code, str)
                        and code
                        and len(code) <= 96
                        and all(character in "ABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789" for character in code)
                    ):
                        diagnostic = code
                except (ValueError, TypeError):
                    pass
            assert process.returncode == expected, "isolated worker child returned unexpected status: " + diagnostic
            assert not stderr, "isolated worker emitted unexpected diagnostics"
            if expected == 73:
                assert not stdout
                return {}
            result = json.loads(stdout)
            assert set(result) <= {"published", "consumed", "confirmed", "error"}
            return result
        finally:
            if process.poll() is None:
                process.kill()
            process.communicate(timeout=10)
            if selected_config != config:
                selected_config.unlink(missing_ok=True)

    def count():
        with Connection(url, connect_timeout=5) as connection:
            return int(queue(connection).queue_declare(passive=True)[1])

    try:
        yield context, http, upload, descriptor, child, count
    finally:
        http.__exit__(None, None, None)
        config.unlink(missing_ok=True)
        # Delete this test's random case queue only; never shared exchange/queues.
        assert name == "mt_business_validation_" + UUID(payload["case"]).hex
        with Connection(url, connect_timeout=5) as connection:
            bound = queue(connection)
            bound.declare()
            bound.delete(if_unused=False, if_empty=False)


def state(context, upload):
    with psycopg.connect(context["admin_dsn"]) as connection:
        row = connection.execute(
            "SELECT state,asset_id FROM mt.upload_session WHERE upload_id=%s", (upload,)
        ).fetchone()
        assets = connection.execute("SELECT count(*) FROM mt.media_asset").fetchone()
        assert row is not None and assets is not None
        return row[0], row[1], assets[0]


def test_process_success_duplicate_completion_and_delivery(process_upload):
    context, http, upload, descriptor, child, count = process_upload
    first = complete(http, upload, descriptor)
    second = complete(http, upload, descriptor)
    assert first.status_code == second.status_code == 202 and first.json() == second.json()
    assert child("publish") == {"published": 1}
    assert count() == 1
    assert child("consume") == {"published": 0, "consumed": 1, "confirmed": True}
    initial = state(context, upload)
    assert initial[0] == "COMPLETED" and initial[1] is not None and initial[2] == 1
    # Republish the identical persisted event through the real broker.
    assert child("publish") == {"published": 1}
    assert child("consume")["consumed"] == 1 and count() == 0
    assert state(context, upload) == initial
    with psycopg.connect(context["admin_dsn"]) as connection:
        assert connection.execute(
            "SELECT count(*) FROM mt.outbox_event WHERE aggregate_id=%s", (upload,)
        ).fetchone() == (1,)
    assert len(list(context["settings"].object_root.rglob("*.bin"))) == 2


def test_process_rejects_other_upload_in_same_case_queue(process_upload):
    context, _, upload_a, _, child, count = process_upload
    _, http_b, upload_b, descriptor_b = prepared_upload(context)
    try:
        assert upload_a != upload_b
        before_a = state(context, upload_a)
        assert before_a[0] not in {"COMPLETED", "REJECTED", "EXPIRED"} and before_a[1:] == (None, 0)
        assert complete(http_b, upload_b, descriptor_b).status_code == 202
        assert child("publish", upload_id=upload_b) == {"published": 1}
        assert count() == 1
        assert child("consume", expected=3) == {"error": "UPLOAD_EVENT_BINDING_INVALID"}
        assert state(context, upload_a) == before_a
        assert state(context, upload_b) == ("VALIDATING", None, 0)
        deadline = time.monotonic() + 10
        while count() != 1 and time.monotonic() < deadline:
            time.sleep(0.1)
        assert count() == 1
        assert child("consume", upload_id=upload_b) == {
            "published": 0,
            "consumed": 1,
            "confirmed": True,
        }
        assert count() == 0
        result_b = state(context, upload_b)
        assert result_b[0] == "COMPLETED" and result_b[1] is not None and result_b[2] == 1
        assert state(context, upload_a) == (before_a[0], None, 1)
        assert len(list(context["settings"].object_root.rglob("*.bin"))) == 3
    finally:
        http_b.__exit__(None, None, None)


@pytest.mark.parametrize("damage", ["missing_part", "full_hash"])
def test_process_rejects_invalid_bytes(process_upload, damage):
    context, http, upload, descriptor, child, count = process_upload
    if damage == "full_hash":
        with psycopg.connect(context["admin_dsn"]) as connection:
            connection.execute(
                "UPDATE mt.upload_session SET sha256=%s WHERE upload_id=%s",
                ("0" * 64, upload),
            )
    assert complete(http, upload, descriptor).status_code == 202
    child("publish")
    if damage == "missing_part":
        parts = list(context["settings"].object_root.rglob("*.bin"))
        assert len(parts) == 1
        parts[0].unlink()
    assert child("consume")["consumed"] == 1
    assert state(context, upload) == ("REJECTED", None, 0) and count() == 0
    assert len(list(context["settings"].object_root.rglob("*.bin"))) == (0 if damage == "missing_part" else 1)


def test_process_commit_then_tcp_close_redelivers_without_second_asset(process_upload):
    context, http, upload, descriptor, child, count = process_upload
    assert complete(http, upload, descriptor).status_code == 202
    child("publish")
    child("crash", expected=73)
    committed = state(context, upload)
    assert committed[0] == "COMPLETED" and committed[1] is not None and committed[2] == 1
    deadline = time.monotonic() + 10
    while count() != 1 and time.monotonic() < deadline:
        time.sleep(0.1)
    assert count() == 1
    assert child("consume") == {"published": 0, "consumed": 1, "confirmed": True}
    assert count() == 0 and state(context, upload) == committed
    assert len(list(context["settings"].object_root.rglob("*.bin"))) == 2


@pytest.mark.parametrize("revocation", ["owner", "membership", "source"])
def test_process_rechecks_authority_after_publication(process_upload, revocation):
    context, http, upload, descriptor, child, count = process_upload
    assert complete(http, upload, descriptor).status_code == 202
    child("publish")
    with psycopg.connect(context["admin_dsn"]) as connection:
        if revocation == "owner":
            connection.execute(
                "UPDATE mt.users SET enabled=false WHERE user_id=%s",
                (context["actor"].user_id,),
            )
        elif revocation == "membership":
            connection.execute(
                "UPDATE mt.case_membership SET revoked_at=now() WHERE case_id=%s AND user_id=%s",
                (context["case_id"], context["actor"].user_id),
            )
        else:
            connection.execute(
                "UPDATE mt.source_registry SET authorization_status='revoked' WHERE source_id=%s",
                (context["source_id"],),
            )
    result = child("consume", expected=3)
    assert result == {"error": "SOURCE_AUTHORIZATION_REQUIRED" if revocation == "source" else "CASE_NOT_FOUND"}
    assert state(context, upload) == ("VALIDATING", None, 0)
    deadline = time.monotonic() + 10
    while count() != 1 and time.monotonic() < deadline:
        time.sleep(0.1)
    assert count() == 1
    assert len(list(context["settings"].object_root.rglob("*.bin"))) == 1
