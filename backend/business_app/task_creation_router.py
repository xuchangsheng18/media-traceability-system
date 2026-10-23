"""Existing createTask contract; trust and material budgets require injection."""

from typing import Annotated, Any, cast
from uuid import UUID

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse

from .auth import authorize_request
from .contracts import validate_api
from .controls.common import reply
from .errors import BusinessError
from .task_creation_service import TaskCreationService

router = APIRouter(prefix="/api/v1")


@router.post("/analysis/tasks", status_code=202, operation_id="createTask")
def create_task(
    request: Request,
    body: dict[str, Any],
    idempotency_key: Annotated[str, Header(min_length=1, max_length=128)],
) -> JSONResponse:
    validate_api("TaskCreate", body)
    scope = authorize_request(request, UUID(body["case_id"]), "task.create")
    service = cast(TaskCreationService | None, request.app.state.task_creation_service)
    if service is None:
        raise BusinessError("CONDITIONAL_FACTS_UNAVAILABLE", 503)
    accepted = service.create(scope, body, idempotency_key=idempotency_key, request_id=request.state.request_id)
    return reply("Accepted", accepted, status=202)
