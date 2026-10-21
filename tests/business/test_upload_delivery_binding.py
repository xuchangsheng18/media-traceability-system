"""A selected upload pump must never execute or ACK another upload's delivery."""

from typing import Any, cast
from uuid import UUID

import pytest
from business_app.errors import BusinessError
from business_app.types import Actor, Scope
from business_app.uploads import messaging
from business_app.uploads.worker import UploadValidationWorker


def fixture():
    actor = Actor(
        UUID("10000000-0000-4000-8000-000000000001"),
        UUID("20000000-0000-4000-8000-000000000001"),
    )
    scope = Scope(actor, UUID("30000000-0000-4000-8000-000000000001"))
    upload = UUID("40000000-0000-4000-8000-000000000001")
    body = dict(
        actor_id=str(actor.user_id),
        org_id=str(actor.org_id),
        case_id=str(scope.case_id),
        upload_id=str(upload),
    )
    events: list[str] = []

    class Worker:
        def consume_validation(self, value: dict[str, Any]) -> None:
            assert value == body
            events.append("committed")

    class Delivery:
        def ack(self) -> None:
            assert events == ["committed"]
            events.append("acknowledged")

    return (
        scope,
        upload,
        body,
        events,
        cast(UploadValidationWorker, Worker()),
        Delivery(),
    )


def deliver(*args):
    function = getattr(messaging, "deliver_bound_upload", None)
    assert function is not None, "the upload-scoped delivery boundary is missing"
    return function(*args)


def test_matching_delivery_is_acknowledged_only_after_worker_returns():
    scope, upload, body, events, worker, message = fixture()
    deliver(worker, scope, upload, body, message)
    assert events == ["committed", "acknowledged"]


@pytest.mark.parametrize("field", ["actor_id", "org_id", "case_id", "upload_id"])
def test_other_delivery_binding_is_not_executed_or_acknowledged(field):
    scope, upload, body, events, worker, message = fixture()
    body = dict(body, **{field: "90000000-0000-4000-8000-000000000001"})
    with pytest.raises(BusinessError) as failure:
        deliver(worker, scope, upload, body, message)
    assert failure.value.code == "UPLOAD_EVENT_BINDING_INVALID"
    assert events == []


@pytest.mark.parametrize("body", [None, [], b"not-json-object", {}, "not-json-object"])
def test_malformed_delivery_has_no_worker_or_ack_side_effect(body):
    scope, upload, _, events, worker, message = fixture()
    with pytest.raises(BusinessError) as failure:
        deliver(worker, scope, upload, body, message)
    assert failure.value.code == "UPLOAD_EVENT_BINDING_INVALID"
    assert events == []


def test_worker_failure_leaves_delivery_unacknowledged():
    scope, upload, body, events, _, message = fixture()

    class Interrupted:
        def consume_validation(self, value):
            events.append("interrupted")
            raise RuntimeError("self-owned transient failure")

    with pytest.raises(RuntimeError, match="transient"):
        deliver(cast(UploadValidationWorker, Interrupted()), scope, upload, body, message)
    assert events == ["interrupted"]


def test_ack_failure_does_not_rerun_committed_worker_in_the_callback():
    scope, upload, body, events, worker, _ = fixture()

    class LostAck:
        def ack(self):
            events.append("ack-failed")
            raise RuntimeError("self-owned ack transport failure")

    with pytest.raises(RuntimeError, match="ack transport"):
        deliver(worker, scope, upload, body, LostAck())
    assert events == ["committed", "ack-failed"]
