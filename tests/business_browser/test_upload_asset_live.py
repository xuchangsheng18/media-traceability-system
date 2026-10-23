"""Real browser/HTTP/PG/Rabbit/object bytes; explicitly synthetic trust only.

Run separately, serially, with the existing locked browser tools and a fresh UI
build. This does not install a test identity or policy in the shared application.
"""

import hashlib
import io
import json
import os
import socket
import subprocess
import threading
import time
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from uuid import UUID

import psycopg
import uvicorn
from business_app.main import create_app
from business_app.types import Scope
from business_app.uploads.messaging import pump_outbox_once, validation_queue_name
from kombu import Connection, Exchange, Queue
from PIL import Image

from scripts.business_demo_gateway import create_app as gateway
from tests.business.test_upload_worker_process import broker_url

ROOT = Path(__file__).resolve().parents[2]


@contextmanager
def listening(app):
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, log_level="error", access_log=False))
    thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
    thread.start()
    try:
        deadline = time.monotonic() + 10
        while not server.started and thread.is_alive() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert server.started, "isolated HTTP server did not start"
        yield port
    finally:
        server.should_exit = True
        thread.join(timeout=10)
        sock.close()
        assert not thread.is_alive(), "isolated HTTP server did not stop"


def test_browser_upload_to_asset_uses_real_http_queue_and_download(business_context, tmp_path):
    c = business_context
    dist = ROOT / "frontend/dist"
    assert (dist / "index.html").is_file(), "build the current UI before live browser integration"
    raw = io.BytesIO()
    Image.new("RGB", (8, 8), "white").save(raw, format="PNG")
    data = raw.getvalue()
    image = tmp_path / "self-owned.png"
    image.write_bytes(data)
    permissions = ["identity.read", "case.read", "source.read", "asset.upload", "asset.read", "asset.download"]
    with psycopg.connect(c["admin_dsn"]) as connection:
        connection.execute(
            "UPDATE mt.source_registry SET purpose=array_append(purpose,'download') WHERE source_id=%s",
            (c["source_id"],),
        )

    class SyntheticDirectory:
        def current(self, actor):
            assert actor == c["actor"]
            return dict(
                user_id=str(actor.user_id),
                org_id=str(actor.org_id),
                roles=["explicit-browser-fixture"],
                permissions=permissions,
                case_ids=[str(c["case_id"])],
            )

    app = create_app(
        replace(c["settings"], part_size_bytes=32),
        c["authority"],
        identity_directory=SyntheticDirectory(),
        permission_authority=c["permission_authority"],
        conditional_permissions=c["conditional_permissions"],
        authorization_fence=c["authorization_fence"],
        work_authorization=c["work_authorization"],
    )
    scope = Scope(c["actor"], c["case_id"])
    url = broker_url()
    stopped = threading.Event()
    processed = []
    failures = []
    owned_uploads = []

    def worker():
        try:
            deadline = time.monotonic() + 60
            while not stopped.is_set() and time.monotonic() < deadline:
                with psycopg.connect(c["admin_dsn"]) as connection:
                    row = connection.execute(
                        "SELECT upload_id FROM mt.upload_session WHERE state='VALIDATING'"
                    ).fetchone()
                if row is not None:
                    identifier = UUID(str(row[0]))
                    owned_uploads.append(identifier)
                    processed.append(
                        pump_outbox_once(
                            app.state.upload_service,
                            c["authority"],
                            scope,
                            url,
                            work_authorization=c["work_authorization"],
                            upload_id=identifier,
                        )
                    )
                    return
                stopped.wait(0.05)
        except BaseException as error:
            failures.append(type(error).__name__)

    runner = threading.Thread(target=worker, daemon=True)
    try:
        with listening(app) as api_port, listening(gateway(dist, api_port, api_port)) as ui_port:
            runner.start()
            result = subprocess.run(
                [os.environ.get("MT_BROWSER_NODE", "node"), str(ROOT / "frontend/e2e-live/upload-asset.mjs")],
                input=json.dumps(
                    dict(
                        origin=f"http://127.0.0.1:{ui_port}",
                        case_id=str(c["case_id"]),
                        source_id=str(c["source_id"]),
                        image=str(image),
                        sha256=hashlib.sha256(data).hexdigest(),
                    )
                ),
                text=True,
                capture_output=True,
                timeout=75,
                cwd=ROOT,
            )
            assert result.returncode == 0, result.stderr
            receipt = json.loads(result.stdout)
            assert receipt["status"] == "PASS_REAL_TRANSPORT_SYNTHETIC_TRUST"
            assert receipt["download_sha256"] == hashlib.sha256(data).hexdigest()
            assert receipt["part_count"] == 3
            assert receipt["asset_id"]
        assert not failures, failures
        assert processed == [dict(published=1, consumed=1, confirmed=True)]
        with psycopg.connect(c["admin_dsn"]) as connection:
            assert connection.execute("SELECT state FROM mt.upload_session").fetchall() == [("COMPLETED",)]
            assert connection.execute("SELECT asset_id,state,sha256 FROM mt.media_asset").fetchall() == [
                (UUID(receipt["asset_id"]), "VALID", hashlib.sha256(data).hexdigest())
            ]
    finally:
        stopped.set()
        if runner.ident is not None:
            runner.join(timeout=20)
            assert not runner.is_alive(), "isolated worker did not stop"
        with Connection(url, connect_timeout=5) as connection:
            for identifier in owned_uploads:
                name = validation_queue_name(scope, identifier)
                Queue(
                    name,
                    exchange=Exchange("mt_business_validation", type="direct", durable=True),
                    routing_key=name,
                    durable=True,
                )(connection).delete(if_unused=False, if_empty=False)
