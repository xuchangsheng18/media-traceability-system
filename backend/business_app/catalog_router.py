"""Only the three implemented catalog operations; immutable bytes are a separate API."""

from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from .auth import authorize_request
from .catalog_reads import CatalogReads
from .controls.common import reply
from .errors import BusinessError
from .history.router import current_scope
from .permissions.conditional import ConditionalPort

router = APIRouter(prefix="/api/v1")


def validate_query(request: Request, *, collection: bool) -> None:
    allowed = {"case_id", "limit", "cursor"} if collection else set()
    values = request.query_params
    if set(values) - allowed or any(len(values.getlist(key)) != 1 for key in values):
        raise BusinessError("READ_PARAMETER_UNSUPPORTED", 422)


@router.get("/assets/{id}", operation_id="getAsset")
def get_asset(request: Request, id: UUID) -> JSONResponse:
    validate_query(request, collection=False)
    scope = current_scope(request, id, "asset", "asset.read")
    service = cast(CatalogReads, request.app.state.catalog_reads)
    with service.database.transaction(scope) as connection:
        value = service.asset(connection, scope, id)
    return reply("Asset", value)


@router.get("/assets", operation_id="listAssets")
def list_assets(
    request: Request,
    case_id: UUID,
    cursor: Annotated[str | None, Query(min_length=1, max_length=128)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> JSONResponse:
    validate_query(request, collection=True)
    scope = authorize_request(request, case_id, "asset.read")
    return reply(
        "AssetPage",
        cast(CatalogReads, request.app.state.catalog_reads).list(
            scope, "listAssets", cursor, limit, cast(ConditionalPort, request.app.state.conditional_permissions)
        ),
    )


@router.get("/analysis/tasks", operation_id="listTasks")
def list_tasks(
    request: Request,
    case_id: UUID,
    cursor: Annotated[str | None, Query(min_length=1, max_length=128)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> JSONResponse:
    validate_query(request, collection=True)
    scope = authorize_request(request, case_id, "task.read")
    return reply(
        "TaskPage",
        cast(CatalogReads, request.app.state.catalog_reads).list(
            scope, "listTasks", cursor, limit, cast(ConditionalPort, request.app.state.conditional_permissions)
        ),
    )
