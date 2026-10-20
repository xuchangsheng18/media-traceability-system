from typing import Any
from uuid import UUID

from app.tracing import trace_id
from kombu import Connection, Consumer, Exchange, Producer, Queue
from sqlalchemy import text

from ..auth import AuthorityProvider
from ..errors import BusinessError
from ..permissions.context import WorkPort, protected_work
from ..types import Scope
from .service import UploadService
from .worker import UploadValidationWorker


def pump_outbox_once(
    service: UploadService,
    authority: AuthorityProvider,
    scope: Scope,
    broker_url: str,
    *,
    work_authorization: WorkPort | None = None,
    upload_id: UUID | None = None,
) -> dict[str, int | bool]:
    if work_authorization is None:
        raise BusinessError("CONDITIONAL_POLICY_UNCONFIGURED", 503)
    if not isinstance(upload_id, UUID) or upload_id.int == 0:
        raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
    with (
        protected_work(work_authorization, scope, "upload_validation", upload_id, "validateUploadWork"),
        service.database.transaction(scope) as sql_connection,
    ):
        pending = (
            sql_connection.execute(
                text("""SELECT event_id,payload FROM mt.outbox_event WHERE case_id=:case
            AND aggregate_id=:upload AND topic='upload.validation.requested.v1' AND published_at IS NULL ORDER BY created_at,event_id"""),
                {"case": scope.case_id, "upload": upload_id},
            )
            .mappings()
            .all()
        )
    published, consumed = 0, 0
    exchange = Exchange("mt_business_validation", type="direct", durable=True)
    name = "mt_business_validation_" + scope.case_id.hex
    queue = Queue(name, exchange=exchange, routing_key=name, durable=True)
    worker = UploadValidationWorker(service, authority, work_authorization)
    with Connection(broker_url, transport_options={"confirm_publish": True}) as connection:
        bound = queue(connection)
        bound.declare()
        producer = Producer(connection)
        for item in pending:
            with (
                protected_work(work_authorization, scope, "upload_validation", upload_id, "validateUploadWork"),
                service.database.transaction(scope) as sql_connection,
            ):
                current = (
                    sql_connection.execute(
                        text(
                            "SELECT payload,published_at FROM mt.outbox_event WHERE case_id=:case AND event_id=:event AND aggregate_id=:upload FOR UPDATE"
                        ),
                        dict(case=scope.case_id, event=item["event_id"], upload=upload_id),
                    )
                    .mappings()
                    .one_or_none()
                )
                if current is None or current["payload"] != item["payload"]:
                    raise BusinessError("UPLOAD_EVENT_BINDING_INVALID", 409)
                if current["published_at"] is not None:
                    continue
                payload = item["payload"]
                if (
                    payload.get("upload_id"),
                    payload.get("org_id"),
                    payload.get("case_id"),
                    payload.get("actor_id"),
                    payload.get("event_id"),
                ) != (
                    str(upload_id),
                    str(scope.actor.org_id),
                    str(scope.case_id),
                    str(scope.actor.user_id),
                    str(item["event_id"]),
                ):
                    raise BusinessError("UPLOAD_EVENT_BINDING_INVALID", 409)
                producer.publish(
                    payload,
                    exchange=exchange,
                    routing_key=name,
                    serializer="json",
                    delivery_mode=2,
                    mandatory=True,
                    declare=[queue],
                    headers={
                        "request_id": payload["request_id"],
                        "trace_id": trace_id(payload["request_id"]),
                    },
                )
                sql_connection.execute(
                    text(
                        "UPDATE mt.outbox_event SET published_at=now(),attempts=attempts+1 WHERE case_id=:case AND event_id=:event"
                    ),
                    {"case": scope.case_id, "event": item["event_id"]},
                )
                published += 1

        def receive(body: dict[str, Any], message: Any) -> None:
            nonlocal consumed
            worker.consume_validation(body)
            message.ack()
            consumed += 1

        available = int(bound.queue_declare()[1])
        with Consumer(connection, queues=[queue], callbacks=[receive], accept=["json"]):
            while consumed < available:
                connection.drain_events(timeout=15)
    return {"published": published, "consumed": consumed, "confirmed": True}
