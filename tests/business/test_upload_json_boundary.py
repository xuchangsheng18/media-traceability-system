"""Real JSON decoding and worker schema boundary; no broker, DB or business success."""

import json
from typing import Any, NoReturn, cast

import pytest
from business_app.auth import AuthorityProvider
from business_app.errors import BusinessError
from business_app.uploads.service import UploadService
from business_app.uploads.worker import UploadValidationWorker
from kombu.utils.json import loads


class StopAtAuthority(RuntimeError):
    pass


class TrapAuthority:
    def __init__(self) -> None:
        self.calls = 0

    def authorize_case(self, *_args: object) -> NoReturn:
        self.calls += 1
        raise StopAtAuthority("owned fixture stops before database")


def event_fixture() -> dict[str, Any]:
    identifier = "00000000-0000-4000-8000-000000000001"
    event: dict[str, Any] = {
        key: identifier for key in ("event_id", "org_id", "case_id", "actor_id", "upload_id", "request_id")
    }
    event.update(
        schema_version="1.0.0",
        event_type="upload.validation.requested.v1",
        session_version=1,
        source_authorization_version="owned-fixture-1",
    )
    return event


@pytest.mark.parametrize("field", ["request_id", "actor_id", "source_authorization_version", "extra_unexpected"])
def test_decoded_byte_envelope_rejected_before_authority_or_database(field: str) -> None:
    event = event_fixture()
    event[field] = {"__type__": "base64", "__value__": "YQ==EXTRA"}
    decoded = loads(json.dumps(event))
    assert decoded[field] == b"a"
    authority = TrapAuthority()
    worker = UploadValidationWorker(cast(UploadService, object()), cast(AuthorityProvider, authority))
    with pytest.raises(BusinessError) as error:
        worker.consume_validation(decoded)
    assert error.value.code == "UPLOAD_EVENT_INVALID"
    assert error.value.http_status == 422
    assert authority.calls == 0


def test_ordinary_json_control_reaches_authority_and_stops_before_database() -> None:
    authority = TrapAuthority()
    worker = UploadValidationWorker(cast(UploadService, object()), cast(AuthorityProvider, authority))
    with pytest.raises(StopAtAuthority):
        worker.consume_validation(loads(json.dumps(event_fixture())))
    assert authority.calls == 1
