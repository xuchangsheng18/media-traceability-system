from typing import cast
from uuid import UUID

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from ..auth import AuthorityProvider, authorize_request
from ..db import Database
from ..errors import BusinessError
from ..types import ResultKey, Scope
from .projection import project
from .repository import ResultRepository

router = APIRouter(prefix="/api/v1")


def parse_history(request: Request, resource_id: UUID, task_path: bool) -> ResultKey | None:
    values = request.query_params
    keys = [key for key in values if key.startswith("history")]
    if not keys:
        return None
    required = {"history[run_version]", "history[result_version]"}
    if not task_path:
        required.add("history[task_id]")
    if set(keys) != required or any(len(values.getlist(key)) != 1 for key in keys):
        raise BusinessError("HISTORY_SELECTION_INVALID", 422)
    try:
        versions = [values[key] for key in ["history[run_version]", "history[result_version]"]]
        if any(not value.isascii() or not value.isdecimal() or int(value) < 1 for value in versions):
            raise ValueError()
        task_id = resource_id if task_path else UUID(values["history[task_id]"])
        return ResultKey(task_id, int(versions[0]), int(versions[1]))
    except (ValueError, OverflowError):
        raise BusinessError("HISTORY_SELECTION_INVALID", 422) from None


def current_scope(request: Request, resource_id: UUID, kind: str, action: str) -> Scope:
    authority = cast(AuthorityProvider | None, request.app.state.business_authority)
    if authority is None:
        raise BusinessError("IDENTITY_AUTHORITY_UNAVAILABLE", 503)
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer ") or not header[7:]:
        raise BusinessError("AUTHENTICATION_REQUIRED", 401)
    actor = authority.authenticate(header[7:])
    database = cast(Database, request.app.state.business_database)
    statements = {
        "task": "SELECT case_id FROM mt.analysis_task WHERE task_id=:id",
        "asset": "SELECT case_id FROM mt.media_asset WHERE asset_id=:id",
        "cluster": "SELECT case_id FROM mt.content_cluster WHERE cluster_id=:id",
    }
    with database.identity_transaction(actor) as connection:
        case_id = connection.execute(text(statements[kind]), {"id": resource_id}).scalar_one_or_none()
    if case_id is None:
        raise BusinessError("RESOURCE_NOT_FOUND", 404)
    scope = authorize_request(request, case_id, action)
    if scope.actor != actor:
        raise BusinessError("AUTHORITY_SCOPE_INVALID", 503)
    return scope


def read_result(request: Request, id: UUID, operation: str, kind: str, action: str) -> JSONResponse:
    scope = current_scope(request, id, kind, action)
    key = parse_history(request, id, kind == "task")
    ranking: UUID | None = None
    allowed = {"history[run_version]", "history[result_version]"}
    if kind != "task":
        allowed.add("history[task_id]")
    if operation == "getFirstSource":
        allowed.add("ranking_id")
        raw = request.query_params.getlist("ranking_id")
        try:
            if len(raw) > 1:
                raise ValueError()
            ranking = UUID(raw[0]) if raw else None
        except ValueError:
            raise BusinessError("HISTORY_SELECTION_INVALID", 422) from None
    if set(request.query_params) - allowed:
        raise BusinessError("READ_PARAMETER_UNSUPPORTED", 422)
    repository = cast(ResultRepository, request.app.state.result_repository)
    if key is None:
        key, snapshot = repository.load_latest(scope, operation, id, ranking)
    else:
        snapshot = repository.load_exact(scope, key)
    body = project(snapshot, operation, id, ranking)
    return JSONResponse(
        body,
        headers={
            "X-Task-Id": str(key.task_id),
            "X-Run-Version": str(key.run_version),
            "X-Result-Version": str(key.result_version),
        },
    )


@router.get("/analysis/tasks/{id}", operation_id="getTask")
def task(request: Request, id: UUID) -> JSONResponse:
    return read_result(request, id, "getTask", "task", "task.read")


@router.get("/analysis/tasks/{id}/risk-findings", operation_id="getRiskFindings")
def risk(request: Request, id: UUID) -> JSONResponse:
    return read_result(request, id, "getRiskFindings", "task", "task.read")


@router.get("/analysis/tasks/{id}/forensics", operation_id="getForensics")
def forensics(request: Request, id: UUID) -> JSONResponse:
    return read_result(request, id, "getForensics", "task", "task.read")


@router.get("/analysis/tasks/{id}/evidence", operation_id="getTaskEvidence")
def evidence(request: Request, id: UUID) -> JSONResponse:
    return read_result(request, id, "getTaskEvidence", "task", "evidence.read")


@router.get("/assets/{id}/timeline", operation_id="getTimeline")
def timeline(request: Request, id: UUID) -> JSONResponse:
    return read_result(request, id, "getTimeline", "asset", "asset.read")


@router.get("/clusters/{id}/first-source", operation_id="getFirstSource")
def first_source(request: Request, id: UUID) -> JSONResponse:
    return read_result(request, id, "getFirstSource", "cluster", "origin.read")


@router.get("/propagation/{id}", operation_id="getPropagation")
def propagation(request: Request, id: UUID) -> JSONResponse:
    return read_result(request, id, "getPropagation", "cluster", "propagation.read")
