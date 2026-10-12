import copy
import datetime
import os
import uuid

import pytest
from jsonschema import ValidationError

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://unused:unused@127.0.0.1:1/unused")
from app.common import CASE_ID  # noqa: E402
from app.contracts import EVENT  # noqa: E402


def sample_event():
    return {"schema_version": "1.0.0", "event_type": "poc.analysis.requested.v1", "event_id": str(uuid.uuid4()),
            "occurred_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "request_id": str(uuid.uuid4()),
            "trace_origin": "api", "case_id": CASE_ID, "producer": "backend.poc",
            "payload": {"job_id": str(uuid.uuid4()), "asset_id": str(uuid.uuid4())}}


def test_complete_event_is_valid():
    EVENT.validate(sample_event())


@pytest.mark.parametrize("field,value", [("schema_version", "2.0.0"), ("event_type", "arbitrary.command"),
                                         ("request_id", "bad-id"), ("occurred_at", "not-a-time")])
def test_unknown_versions_types_and_invalid_trace_are_rejected(field, value):
    event = sample_event()
    event[field] = value
    with pytest.raises(ValidationError):
        EVENT.validate(event)


def test_unexpected_secret_field_is_rejected():
    event = sample_event()
    event["token"] = "synthetic-extra-field"
    with pytest.raises(ValidationError):
        EVENT.validate(event)


def test_missing_asset_identity_is_rejected():
    event = copy.deepcopy(sample_event())
    del event["payload"]["asset_id"]
    with pytest.raises(ValidationError):
        EVENT.validate(event)
