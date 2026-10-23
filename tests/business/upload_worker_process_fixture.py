"""Private subprocess harness for isolated upload tests; never a runtime authority."""

import contextlib
import io
import json
import logging
import os
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from uuid import UUID

import psycopg
from business_app.db import Database
from business_app.errors import BusinessError
from business_app.objects import FileObjectStore
from business_app.settings import BusinessSettings
from business_app.types import Actor, Scope
from business_app.uploads.messaging import pump_outbox_once, validation_queue_name
from business_app.uploads.repository import UploadRepository
from business_app.uploads.service import UploadService
from kombu import Connection, Exchange, Producer, Queue
from kombu.message import Message
from psycopg.conninfo import conninfo_to_dict
from sqlalchemy import text

from tests.business.http_fixtures import FixtureWork


class ProcessAuthority:
    """Re-read current synthetic directory facts using the isolated runtime role."""

    def __init__(self, dsn, actor):
        self.dsn, self.actor = dsn, actor

    @contextlib.contextmanager
    def connection(self, case_id):
        with psycopg.connect(self.dsn) as connection:
            connection.execute(
                """SELECT set_config('app.actor_id',%s,true),set_config('app.org_id',%s,true),
                set_config('app.scope_mode','CASE',true),set_config('app.case_id',%s,true),
                set_config('app.operation_id','validateUploadWork',true)""",
                (str(self.actor.user_id), str(self.actor.org_id), str(case_id)),
            )
            yield connection

    def authenticate(self, bearer):
        raise BusinessError("AUTHENTICATION_REQUIRED", 401)

    def authorize_case(self, actor, case_id, action):
        if actor != self.actor or action != "asset.upload":
            raise BusinessError("CASE_NOT_FOUND", 404)
        with self.connection(case_id) as connection:
            row = connection.execute(
                """SELECT 1 FROM mt.users u JOIN mt.case_membership m
                ON m.user_id=u.user_id AND m.org_id=u.org_id
                WHERE u.user_id=%s AND u.org_id=%s AND u.enabled AND m.case_id=%s
                AND m.revoked_at IS NULL AND (m.expires_at IS NULL OR m.expires_at>now())""",
                (actor.user_id, actor.org_id, case_id),
            ).fetchone()
        if row is None:
            raise BusinessError("CASE_NOT_FOUND", 404)
        return Scope(actor, case_id)

    def authorize_source(self, scope, source_id, purpose):
        self.authorize_case(scope.actor, scope.case_id, "asset.upload")
        with self.connection(scope.case_id) as connection:
            row = connection.execute(
                """SELECT authorization_status,purpose,expires_at,authorization_version
                FROM mt.source_registry WHERE source_id=%s AND org_id=%s AND case_id=%s""",
                (source_id, scope.actor.org_id, scope.case_id),
            ).fetchone()
        if (
            row is None
            or row[0] != "verified"
            or purpose not in row[1]
            or not row[3]
            or (row[2] is not None and row[2] <= datetime.now(timezone.utc))
        ):
            raise BusinessError("SOURCE_AUTHORIZATION_REQUIRED", 403)


def run(config, mode):
    values = conninfo_to_dict(config["dsn"])
    name = values.get("dbname")
    assert isinstance(name, str) and name.startswith("mt_business_test_")
    assert values.get("host") in {"127.0.0.1", "localhost", "::1"}
    assert urlsplit(config["broker"]).hostname in {"127.0.0.1", "localhost", "::1"}
    requested_root = Path(config["object_root"])
    assert not any(path.is_symlink() for path in [requested_root, *requested_root.parents])
    root = requested_root.resolve()
    assert root.is_absolute() and root.name == "objects" and root.parent == Path(config["fixture_root"]).resolve()
    actor = Actor(UUID(config["actor"]), UUID(config["org"]))
    scope = Scope(actor, UUID(config["case"]))
    upload = UUID(config["upload"])
    authority = ProcessAuthority(config["dsn"], actor)
    work = FixtureWork(frozenset({actor}))
    database = Database(config["dsn"])
    settings = BusinessSettings(config["dsn"], root, 1_048_576, 256_000, 3600, "t" * 64)
    service = UploadService(
        database,
        UploadRepository(database, settings),
        FileObjectStore(root),
        authority=authority,
    )
    try:
        if mode == "publish":
            exchange = Exchange("mt_business_validation", type="direct", durable=True)
            # Only the private test publisher may deliberately misroute a
            # persisted event to exercise the unchanged delivery boundary.
            target = UUID(config.get("misroute_to_upload", str(upload)))
            name = validation_queue_name(scope, target)
            queue = Queue(name, exchange=exchange, routing_key=name, durable=True)
            with (
                work.open(scope, "upload_validation", upload, "validateUploadWork"),
                database.transaction(scope) as sql,
            ):
                row = (
                    sql.execute(
                        text("SELECT event_id,payload FROM mt.outbox_event WHERE aggregate_id=:id AND case_id=:case"),
                        dict(id=upload, case=scope.case_id),
                    )
                    .mappings()
                    .one()
                )
                with Connection(config["broker"], transport_options={"confirm_publish": True}) as broker:
                    Producer(broker).publish(
                        row["payload"],
                        exchange=exchange,
                        routing_key=name,
                        serializer="json",
                        delivery_mode=2,
                        mandatory=True,
                        declare=[queue],
                    )
                sql.execute(
                    text("UPDATE mt.outbox_event SET published_at=now(),attempts=attempts+1 WHERE event_id=:id"),
                    dict(id=row["event_id"]),
                )
            return {"published": 1}
        if mode == "crash":
            # Actual consume/DB commit happens before this test-only ACK boundary.
            def crash_before_ack(self, *args, **kwargs):
                os._exit(73)

            Message.ack = crash_before_ack
        return pump_outbox_once(
            service,
            authority,
            scope,
            config["broker"],
            work_authorization=work,
            upload_id=upload,
        )
    finally:
        database.close()


def main():
    logging.disable(logging.CRITICAL)
    outcome = {"error": "PROCESS_FIXTURE_FAILED"}
    status = 2
    try:
        path = Path(sys.argv[1])
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
        config = json.loads(path.read_text())
        # Contain all imported application output; only the small result escapes.
        with (
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            outcome = run(config, sys.argv[2])
        status = 0
    except BusinessError as error:
        outcome = {"error": error.code}
        status = 3
    except BaseException:
        pass
    print(json.dumps(outcome))
    return status


if __name__ == "__main__":
    sys.exit(main())
