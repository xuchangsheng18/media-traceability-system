"""Shared safe Problem responses and request tracing for API and inference."""

import logging
import time
import uuid

from business_app.errors import ERROR_STATUS
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.tracing import safe_log, trace_context, trace_id


def configure(app, trust_request_id=False):
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("uvicorn.access").disabled = True

    def problem(request, status, code):
        return JSONResponse(
            {
                "type": "about:blank",
                "title": code,
                "status": status,
                "code": code,
                "message": code,
                "request_id": request.state.request_id,
                "details": [],
            },
            status_code=status,
            media_type="application/problem+json",
        )

    @app.middleware("http")
    async def trace(request: Request, call_next):
        request.state.request_id = str(uuid.uuid4())
        if trust_request_id:
            try:
                request.state.request_id = str(uuid.UUID(request.headers.get("X-Request-ID", "")))
            except ValueError:
                pass
        started = time.monotonic()
        with trace_context(request.state.request_id):
            try:
                response = await call_next(request)
            except Exception:
                response = problem(request, 500, "DEPENDENCY_FAILURE")
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["X-Trace-Id"] = trace_id(request.state.request_id)
        safe_log(
            "request.completed",
            request_id=request.state.request_id,
            method=request.method,
            route=getattr(request.scope.get("route"), "path", "unmatched"),
            status=response.status_code,
            elapsed_ms=int((time.monotonic() - started) * 1000),
        )
        return response

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, error: HTTPException):
        code = str(error.detail)
        if ERROR_STATUS.get(code) != error.status_code:
            code = {404: "RESOURCE_NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}.get(
                error.status_code, f"HTTP_STATUS_{error.status_code}"
            )
        response = problem(request, error.status_code, code)
        if error.status_code == 405:
            allowed = (error.headers or {}).get("Allow", "")
            methods = {value.strip() for value in allowed.split(",")}
            if methods and methods <= {"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "TRACE", "CONNECT"}:
                response.headers["Allow"] = ", ".join(sorted(methods))
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, _):
        return problem(request, 422, "REQUEST_INVALID")
