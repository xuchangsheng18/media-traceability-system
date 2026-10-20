from typing import Any

from app.tracing import trace_id
from kombu import Connection, Consumer, Exchange, Producer, Queue
from sqlalchemy import text

from ..auth import AuthorityProvider
from ..errors import BusinessError
from ..permissions.context import WorkPort
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
) -> dict[str, int | bool]:
    if work_authorization is None:
        raise BusinessError("CONDITIONAL_POLICY_UNCONFIGURED", 503)
    with service.database.transaction(scope) as sql_connection:
        pending = (
            sql_connection.execute(
                text("""SELECT event_id,payload FROM mt.outbox_event WHERE case_id=:case
            AND topic='upload.validation.requested.v1' AND published_at IS NULL ORDER BY created_at,event_id"""),
                {"case": scope.case_id},
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
            producer.publish(
                item["payload"],
                exchange=exchange,
                routing_key=name,
                serializer="json",
                delivery_mode=2,
                mandatory=True,
                declare=[queue],
                headers={
                    "request_id": item["payload"]["request_id"],
                    "trace_id": trace_id(item["payload"]["request_id"]),
                },
            )
            with service.database.transaction(scope) as sql_connection:
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
