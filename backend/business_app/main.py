import copy
import logging
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from types import MappingProxyType
from uuid import UUID, uuid4

import yaml
from app.tracing import safe_log, trace_context, trace_id
from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException

from .auth import AuthorityProvider
from .contracts import ROOT
from .controls.approvals import Approvals
from .controls.execution import Execution
from .controls.exports import Exports
from .controls.imports import Imports
from .controls.providers import (
    DefinitionProvider,
    DeploymentOperations,
    IdentityDirectory,
    RuleProvider,
    SourceSynchronization,
)
from .controls.receipts import ControlReceipts
from .controls.reviews import Reviews
from .controls.router import router as control_router
from .db import Database
from .errors import BusinessError
from .history.repository import ResultRepository
from .history.router import router as history_router
from .inference import BackendRegistration, InferenceGateway, ServiceAuthority
from .inference import router as inference_router
from .objects import FileObjectStore
from .permissions.catalog import load_catalog
from .permissions.conditional import ConditionalPort
from .permissions.context import FencePort, WorkPort
from .permissions.duties import IndependentDuties
from .permissions.guard import audit_protected_routes, authorize_business_route
from .permissions.types import PermissionAuthority
from .settings import BusinessSettings
from .uploads.repository import UploadRepository
from .uploads.router import router as upload_router
from .uploads.service import UploadService


def create_app(
    settings: BusinessSettings,
    authority: AuthorityProvider | None = None,
    *,
    rules: RuleProvider | None = None,
    identity_directory: IdentityDirectory | None = None,
    definition_provider: DefinitionProvider | None = None,
    deployment_operations: DeploymentOperations | None = None,
    source_synchronization: SourceSynchronization | None = None,
    service_authority: ServiceAuthority | None = None,
    inference_backends: dict[str, BackendRegistration] | None = None,
    permission_authority: PermissionAuthority | None = None,
    conditional_permissions: ConditionalPort | None = None,
    independent_duties: IndependentDuties | None = None,
    authorization_fence: FencePort | None = None,
    work_authorization: WorkPort | None = None,
) -> FastAPI:
    logging.getLogger("uvicorn.access").disabled = True
    database = Database(settings.database_dsn)

    @asynccontextmanager
    async def lifespan(current: FastAPI) -> AsyncIterator[None]:
        try:
            audit_protected_routes(current)
            yield
        finally:
            database.close()

    app = FastAPI(title="Independent business development", lifespan=lifespan)
    app.state.permission_framework_routes = frozenset(id(route) for route in app.routes)
    app.state.permission_catalog = MappingProxyType(load_catalog(ROOT))
    app.state.permission_authority = permission_authority
    app.state.conditional_permissions = conditional_permissions
    app.state.authorization_fence = authorization_fence
    app.state.work_authorization = work_authorization
    app.state.business_database = database
    app.state.business_authority = authority
    app.state.business_settings = settings
    app.state.upload_service = UploadService(
        database, UploadRepository(database, settings), FileObjectStore(settings.object_root), authority=authority
    )
    app.state.result_repository = ResultRepository(database, app.state.upload_service.store, authority)
    app.state.control_receipts = ControlReceipts(database, settings)
    app.state.approvals = Approvals(database, app.state.control_receipts, rules, authority, independent_duties)
    app.state.reviews = Reviews(
        database, app.state.control_receipts, app.state.result_repository, rules, independent_duties
    )
    app.state.exports = Exports(
        database,
        app.state.control_receipts,
        app.state.approvals,
        app.state.upload_service.store,
        rules,
        authority,
        work_authorization,
    )
    app.state.imports = Imports(
        database, app.state.control_receipts, app.state.upload_service.store, authority, settings
    )
    app.state.execution = Execution(database, authority, settings.node_lease_seconds, work_authorization)
    app.state.identity_directory = identity_directory
    app.state.definition_provider = definition_provider
    app.state.deployment_operations = deployment_operations
    app.state.source_synchronization = source_synchronization
    app.state.inference_gateway = InferenceGateway(
        database,
        app.state.upload_service.store,
        authority,
        service_authority,
        inference_backends,
        work_authorization=work_authorization,
    )
    protected = [Depends(authorize_business_route)]
    app.include_router(upload_router, dependencies=protected)
    app.include_router(history_router, dependencies=protected)
    app.include_router(control_router, dependencies=protected)
    app.include_router(inference_router)
    audit_protected_routes(app)

    automatic = FastAPI.openapi(app)
    mounted = {operation["operationId"] for methods in automatic["paths"].values() for operation in methods.values()}

    def published_openapi() -> dict[str, object]:
        # Publish exact authoritative schemas only for actually mounted operations.
        business = yaml.safe_load((ROOT / "docs/03-api/openapi.yaml").read_text(encoding="utf-8"))
        internal = yaml.safe_load((ROOT / "docs/03-api/inference-openapi.yaml").read_text(encoding="utf-8"))
        result = copy.deepcopy(business)
        result["servers"] = [{"url": "/"}]
        result["paths"] = {}
        for document, prefix in [(business, "/api/v1"), (internal, "/internal/v1")]:
            for path, methods in document["paths"].items():
                selected = {
                    method: copy.deepcopy(operation)
                    for method, operation in methods.items()
                    if operation.get("operationId") in mounted
                }
                if selected:
                    result["paths"][prefix + path] = selected
        result["components"]["securitySchemes"].update(internal["components"]["securitySchemes"])
        result["paths"]["/internal/v1/inference/{capability}"]["post"]["security"] = internal["security"]
        result["info"]["description"] = (
            "Independent development implementation; authority adapters and production acceptance remain unfrozen."
        )
        return dict(result)

    setattr(app, "openapi", published_openapi)

    @app.middleware("http")
    async def request_trace(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        started = time.monotonic()
        request.state.request_id = uuid4()
        identifiers = request.headers.getlist("X-Request-Id")
        try:
            if len(identifiers) > 1:
                raise ValueError()
            identifier = UUID(identifiers[0]) if identifiers else uuid4()
        except ValueError:
            safe_log("request.rejected", request_id=str(request.state.request_id), status=422, route="unmatched")
            return await business_error(request, BusinessError("REQUEST_ID_INVALID", 422))
        request.state.request_id = identifier
        request.state.client_request_id_provided = bool(identifiers)
        request.scope["headers"] = [
            (key, value) for key, value in request.scope["headers"] if key.lower() != b"x-request-id"
        ] + [(b"x-request-id", str(identifier).encode("ascii"))]
        with trace_context(str(identifier)):
            try:
                response = await call_next(request)
            except Exception:
                response = await business_error(request, BusinessError("INTERNAL_ERROR", 500))
            safe_log(
                "request.completed",
                status=response.status_code,
                method=request.method,
                route=getattr(request.scope.get("route"), "path", "unmatched"),
                elapsed_ms=int((time.monotonic() - started) * 1000),
            )
        response.headers["X-Request-Id"] = str(request.state.request_id)
        response.headers["X-Trace-Id"] = trace_id(str(request.state.request_id))
        return response

    @app.exception_handler(BusinessError)
    async def business_error(request: Request, exception: BusinessError) -> JSONResponse:
        try:
            request_id = getattr(request.state, "request_id", None) or UUID(request.headers.get("X-Request-Id", ""))
        except ValueError:
            request_id = uuid4()
        return JSONResponse(
            status_code=exception.http_status,
            media_type="application/problem+json",
            content={
                "type": "urn:media-trace:error:" + exception.code,
                "title": "业务请求未满足执行条件",
                "status": exception.http_status,
                "code": exception.code,
                "message": "请核验访问范围及执行前置条件。",
                "request_id": str(request_id),
                "details": [],
            },
            headers={
                "X-Request-Id": str(request_id),
                "X-Trace-Id": trace_id(str(request_id)),
                **({"WWW-Authenticate": "Bearer"} if exception.http_status == 401 else {}),
            },
        )

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request: Request, _: SQLAlchemyError) -> JSONResponse:
        return await business_error(request, BusinessError("DATABASE_UNAVAILABLE", 503))

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, _: RequestValidationError) -> JSONResponse:
        return await business_error(request, BusinessError("INPUT_INVALID", 422))

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exception: HTTPException) -> JSONResponse:
        status = exception.status_code
        if not 400 <= status <= 599:
            status = 500
        code = {403: "HTTP_FORBIDDEN", 404: "RESOURCE_NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}.get(
            status, f"HTTP_STATUS_{status}"
        )
        response = await business_error(request, BusinessError(code, status))
        if status == 405:
            permitted = {"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "TRACE", "CONNECT"}
            methods = {value.strip() for value in (exception.headers or {}).get("Allow", "").split(",")}
            if methods and methods <= permitted:
                response.headers["Allow"] = ", ".join(sorted(methods))
        if status == 401:
            response.headers["WWW-Authenticate"] = "Bearer"
        return response

    return app
