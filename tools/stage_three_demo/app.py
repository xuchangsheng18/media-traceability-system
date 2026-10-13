"""Loopback-only three-service connectivity fixture; no business data or models."""

import hmac
import os
import uuid
from pathlib import Path
from urllib.parse import urlsplit

import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from pydantic import BaseModel, ConfigDict

ROOT = Path(__file__).resolve().parents[2]
ROLE = os.environ.get("MT_DEMO_ROLE", "inference")
TOKEN = os.environ.get("MT_DEMO_INTERNAL_TOKEN", "")
app = FastAPI(title="Stage three connectivity fixture", docs_url=None)


class MockInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nonce: uuid.UUID


def authorize(value):
    if not TOKEN or not value or not hmac.compare_digest(value, "Bearer " + TOKEN):
        raise HTTPException(401, "AUTH_REQUIRED")


def target(variable):
    value = os.environ.get(variable, "")
    parsed = urlsplit(value)
    if (
        parsed.scheme != "http"
        or parsed.hostname != "127.0.0.1"
        or not parsed.port
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path
    ):
        raise HTTPException(503, "DEMO_TARGET_INVALID")
    return value


@app.middleware("http")
async def identity(request, call_next):
    try:
        request.state.request_id = str(uuid.UUID(request.headers.get("X-Request-ID", "")))
    except ValueError:
        request.state.request_id = str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


@app.exception_handler(HTTPException)
async def problem(request, exc):
    return JSONResponse(
        {"status": exc.status_code, "code": exc.detail, "request_id": request.state.request_id},
        status_code=exc.status_code,
        media_type="application/problem+json",
    )


@app.exception_handler(RequestValidationError)
async def invalid(request, _):
    return JSONResponse(
        {"status": 422, "code": "REQUEST_INVALID", "request_id": request.state.request_id},
        status_code=422,
        media_type="application/problem+json",
    )


@app.get("/api/v1/health")
def health(request: Request):
    return {
        "status": "ok",
        "role": ROLE,
        "request_id": request.state.request_id,
        "development_fixture": True,
        "business_acceptance": False,
    }


@app.get("/api/v1/ready")
def ready(request: Request):
    if ROLE in {"backend", "frontend"}:
        variable = "MT_DEMO_INFERENCE_URL" if ROLE == "backend" else "MT_DEMO_BACKEND_URL"
        try:
            response = httpx.get(target(variable) + "/api/v1/health", timeout=3)
            response.raise_for_status()
            if response.json().get("status") != "ok":
                raise ValueError("dependency status")
        except (httpx.HTTPError, ValueError):
            raise HTTPException(503, "DEMO_DEPENDENCY_NOT_READY") from None
    return {"status": "ready", "request_id": request.state.request_id, "role": ROLE, "development_fixture": True}


@app.post("/api/v1/mock")
def mock(body: MockInput, request: Request, authorization: str | None = Header(default=None)):
    authorize(authorization)
    if ROLE == "inference":
        return {
            "schema_version": "development-connectivity-v1",
            "nonce": str(body.nonce),
            "mock": True,
            "business_result": False,
            "model_name": "mock-connectivity",
            "model_version": "example-1",
            "request_id": request.state.request_id,
        }
    try:
        response = httpx.post(
            target("MT_DEMO_INFERENCE_URL") + "/api/v1/mock",
            headers={"Authorization": "Bearer " + TOKEN, "X-Request-ID": request.state.request_id},
            json={"nonce": str(body.nonce)},
            timeout=3,
        )
        response.raise_for_status()
        output = response.json()
        if (
            output.get("mock") is not True
            or output.get("business_result") is not False
            or output.get("nonce") != str(body.nonce)
        ):
            raise ValueError("invalid mock result")
        return output
    except (httpx.HTTPError, ValueError):
        raise HTTPException(502, "DEMO_INFERENCE_UNAVAILABLE") from None


@app.get("/")
def frontend():
    if ROLE != "frontend":
        raise HTTPException(404, "NOT_FOUND")
    return HTMLResponse((ROOT / "tools/stage_three_demo/index.html").read_text(encoding="utf-8"))


@app.get("/vue.js")
def vue():
    if ROLE != "frontend":
        raise HTTPException(404, "NOT_FOUND")
    return FileResponse(ROOT / "frontend/node_modules/vue/dist/vue.global.prod.js", media_type="text/javascript")


@app.post("/demo/check")
def check_frontend(request: Request):
    if ROLE != "frontend":
        raise HTTPException(404, "NOT_FOUND")
    try:
        url = target("MT_DEMO_BACKEND_URL")
        ready_response = httpx.get(url + "/api/v1/ready", timeout=5)
        ready_response.raise_for_status()
        nonce = str(uuid.uuid4())
        response = httpx.post(
            url + "/api/v1/mock",
            headers={"Authorization": "Bearer " + TOKEN, "X-Request-ID": request.state.request_id},
            json={"nonce": nonce},
            timeout=5,
        )
        response.raise_for_status()
        result = response.json()
        if result.get("nonce") != nonce or result.get("mock") is not True or result.get("business_result") is not False:
            raise ValueError("unsafe diagnostic result")
        return result
    except (httpx.HTTPError, ValueError):
        raise HTTPException(502, "DEMO_CHAIN_UNAVAILABLE") from None


@app.get("/api/v1/business-data")
def forbidden_business():
    return Response(status_code=404)
