"""Read persisted model and evaluation metadata using only authenticated organization."""

from typing import Annotated, cast

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from .auth import authenticated_actor
from .controls.common import reply
from .errors import BusinessError
from .model_catalog import ModelCatalog
from .permissions.conditional import ConditionalPort

router = APIRouter(prefix="/api/v1")


def validate_query(request: Request) -> None:
    values = request.query_params
    if set(values) - {"limit", "cursor"} or any(len(values.getlist(key)) != 1 for key in values):
        raise BusinessError("READ_PARAMETER_UNSUPPORTED", 422)


def _list(request: Request, operation: str, schema: str, cursor: str | None, limit: int) -> JSONResponse:
    validate_query(request)
    actor = authenticated_actor(request)
    service = cast(ModelCatalog, request.app.state.model_catalog)
    return reply(
        schema,
        service.list(actor, operation, cursor, limit, cast(ConditionalPort, request.app.state.conditional_permissions)),
    )


@router.get("/models", operation_id="listModels")
def list_models(
    request: Request,
    cursor: Annotated[str | None, Query(min_length=1, max_length=128)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> JSONResponse:
    return _list(request, "listModels", "ModelPage", cursor, limit)


@router.get("/model-evaluations", operation_id="listEvaluations")
def list_evaluations(
    request: Request,
    cursor: Annotated[str | None, Query(min_length=1, max_length=128)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> JSONResponse:
    return _list(request, "listEvaluations", "EvaluationPage", cursor, limit)
