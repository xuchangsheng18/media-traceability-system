"""Persisted report metadata; generating and downloading remain separate operations."""

from typing import cast
from uuid import UUID

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from .auth import authenticated_actor, authorize_request
from .controls.common import reply
from .db import Database
from .errors import BusinessError
from .registry_reads import RegistryReads

router = APIRouter(prefix="/api/v1")


@router.get("/reports/{id}", operation_id="getReport")
def get_report(request: Request, id: UUID) -> JSONResponse:
    if request.query_params:
        raise BusinessError("READ_PARAMETER_UNSUPPORTED", 422)
    actor = authenticated_actor(request)
    database = cast(Database, request.app.state.business_database)
    with database.identity_transaction(actor) as connection:
        case_id = connection.execute(
            text("SELECT case_id FROM mt.report WHERE org_id=:org AND report_id=:id"),
            dict(org=actor.org_id, id=id),
        ).scalar_one_or_none()
    if case_id is None:
        raise BusinessError("RESOURCE_NOT_FOUND", 404)
    scope = authorize_request(request, case_id, "report.read")
    if scope.actor != actor:
        raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
    service = cast(RegistryReads, request.app.state.registry_reads)
    with database.transaction(scope) as connection:
        value = service.report(connection, scope, id)
    return reply("Report", value)
