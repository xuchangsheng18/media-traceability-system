from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID, uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .auth import AuthorityProvider
from .db import Database
from .errors import BusinessError
from .settings import BusinessSettings


def create_app(settings: BusinessSettings, authority: AuthorityProvider | None = None) -> FastAPI:
    database = Database(settings.database_dsn)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        database.close()

    app = FastAPI(title="Independent business development", lifespan=lifespan)
    app.state.business_database = database
    app.state.business_authority = authority
    app.state.business_settings = settings

    @app.exception_handler(BusinessError)
    async def business_error(request: Request, exception: BusinessError) -> JSONResponse:
        try:
            request_id = UUID(request.headers.get("X-Request-Id", ""))
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

    return app
