import copy
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from uuid import UUID, uuid4

import yaml
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from sqlalchemy.exc import SQLAlchemyError

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
) -> FastAPI:
    database = Database(settings.database_dsn)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        database.close()

    app = FastAPI(title="Independent business development", lifespan=lifespan)
    app.state.business_database = database
    app.state.business_authority = authority
    app.state.business_settings = settings
    app.state.upload_service = UploadService(
        database, UploadRepository(database, settings), FileObjectStore(settings.object_root)
    )
    app.state.result_repository = ResultRepository(database, app.state.upload_service.store, authority)
    app.state.control_receipts = ControlReceipts(database, settings)
    app.state.approvals = Approvals(database, app.state.control_receipts, rules, authority)
    app.state.reviews = Reviews(database, app.state.control_receipts, app.state.result_repository, rules)
    app.state.exports = Exports(
        database, app.state.control_receipts, app.state.approvals, app.state.upload_service.store, rules, authority
    )
    app.state.imports = Imports(
        database, app.state.control_receipts, app.state.upload_service.store, authority, settings
    )
    app.state.execution = Execution(database, authority, settings.node_lease_seconds)
    app.state.identity_directory = identity_directory
    app.state.definition_provider = definition_provider
    app.state.deployment_operations = deployment_operations
    app.state.source_synchronization = source_synchronization
    app.state.inference_gateway = InferenceGateway(
        database, app.state.upload_service.store, authority, service_authority, inference_backends
    )
    app.include_router(upload_router)
    app.include_router(history_router)
    app.include_router(control_router)
    app.include_router(inference_router)

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
        identifiers = request.headers.getlist("X-Request-Id")
        try:
            if len(identifiers) > 1:
                raise ValueError()
            identifier = UUID(identifiers[0]) if identifiers else uuid4()
        except ValueError:
            return await business_error(request, BusinessError("REQUEST_ID_INVALID", 422))
        request.state.request_id = identifier
        request.state.client_request_id_provided = bool(identifiers)
        request.scope["headers"] = [
            (key, value) for key, value in request.scope["headers"] if key.lower() != b"x-request-id"
        ] + [(b"x-request-id", str(identifier).encode("ascii"))]
        response = await call_next(request)
        response.headers["X-Request-Id"] = str(request.state.request_id)
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
            headers={"X-Request-Id": str(request_id)},
        )

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request: Request, _: SQLAlchemyError) -> JSONResponse:
        return await business_error(request, BusinessError("DATABASE_UNAVAILABLE", 503))

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, _: RequestValidationError) -> JSONResponse:
        return await business_error(request, BusinessError("INPUT_INVALID", 422))

    return app
