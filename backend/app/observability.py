"""Shared safe Problem responses and request tracing for API and inference."""
import json
import logging
import time
import uuid

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def configure(app, trust_request_id=False):
    logger = logging.getLogger("media_trace")
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    def problem(request, status, code):
        return JSONResponse({"type": "about:blank", "title": code, "status": status, "code": code,
                             "message": code, "request_id": request.state.request_id, "details": []},
                            status_code=status, media_type="application/problem+json")

    @app.middleware("http")
    async def trace(request: Request, call_next):
        request.state.request_id = str(uuid.uuid4())
        if trust_request_id:
            try:
                request.state.request_id = str(uuid.UUID(request.headers.get("X-Request-ID", "")))
            except ValueError:
                pass
        started = time.monotonic()
        try:
            response = await call_next(request)
        except Exception:
            response = problem(request, 500, "DEPENDENCY_FAILURE")
        response.headers["X-Request-ID"] = request.state.request_id
        logger.info(json.dumps({"request_id": request.state.request_id, "method": request.method,
                               "route": getattr(request.scope.get("route"), "path", "unmatched"),
                               "status": response.status_code, "elapsed_ms": int((time.monotonic()-started)*1000)}))
        return response

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, error: HTTPException):
        return problem(request, error.status_code, str(error.detail))

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, _):
        return problem(request, 422, "REQUEST_INVALID")
