"""The existing createSource operation, guarded by the shared function/scope fence."""

from typing import Annotated, Any, cast
from uuid import UUID

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse

from .auth import authorize_request
from .contracts import validate_api
from .controls.common import reply
from .errors import BusinessError
from .source_registration import SourceRegistration

router = APIRouter(prefix="/api/v1")


@router.post("/sources", status_code=201, operation_id="createSource")
def create_source(
    request: Request,
    body: dict[str, Any],
    idempotency_key: Annotated[str, Header(min_length=1, max_length=128)],
) -> JSONResponse:
    if request.query_params or len(request.headers.getlist("Idempotency-Key")) != 1:
        raise BusinessError("INPUT_INVALID", 422)
    validate_api("SourceCreate", body)
    scope = authorize_request(request, UUID(body["case_id"]), "source.manage")
    service = cast(SourceRegistration, request.app.state.source_registration)
    return reply("Source", service.create(scope, body, request, idempotency_key), 201)
