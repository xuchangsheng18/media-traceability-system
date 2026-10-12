import hmac
import io
import json
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from PIL import Image
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.common import CASE_ID, decode_image, put_object
from app.db import engine, health
from app.settings import validate_runtime


@asynccontextmanager
async def lifespan(_):
    validate_runtime()
    yield


app = FastAPI(title="Media Trace CPU PoC", version="0.1.0", docs_url="/poc/docs", openapi_url="/poc/openapi.json", lifespan=lifespan)
log = logging.getLogger("media_trace")
logging.basicConfig(level=logging.INFO, format="%(message)s")


def problem(request, status, code):
    return JSONResponse({"type": "about:blank", "title": code, "status": status, "code": code,
                         "message": code, "request_id": request.state.request_id, "details": []},
                        status_code=status, media_type="application/problem+json")


@app.middleware("http")
async def trace_request(request: Request, call_next):
    request.state.request_id = str(uuid.uuid4())
    started = time.monotonic()
    try:
        response = await call_next(request)
    except Exception:
        response = problem(request, 500, "DEPENDENCY_FAILURE")
    response.headers["X-Request-ID"] = request.state.request_id
    route = request.scope.get("route")
    log.info(json.dumps({"request_id": request.state.request_id, "method": request.method,
                        "route": getattr(route, "path", "unmatched"), "status": response.status_code,
                        "elapsed_ms": int((time.monotonic()-started)*1000)}))
    return response


@app.exception_handler(HTTPException)
async def http_error(request: Request, error: HTTPException):
    return problem(request, error.status_code, str(error.detail))


@app.exception_handler(RequestValidationError)
async def invalid_request(request: Request, _):
    return problem(request, 422, "REQUEST_INVALID")


def authorize(authorization: Annotated[str | None, Header()] = None):
    token = os.environ.get("POC_API_TOKEN", "")
    if not token or not authorization or not hmac.compare_digest(authorization, "Bearer " + token):
        raise HTTPException(401, "AUTH_REQUIRED")


class Upload(BaseModel):
    filename: str = Field(min_length=1, max_length=120)
    image_base64: str = Field(min_length=1, max_length=2 * 1024 * 1024)


class Analyze(BaseModel):
    asset_id: uuid.UUID


@app.get("/healthz")
def live():
    return {"status": "ok", "profile": "cpu-development"}


@app.get("/api/v1/health", dependencies=[Depends(authorize)])
def dependencies(request: Request):
    return {"status": "ok" if health() else "unavailable", "request_id": request.state.request_id}


@app.post("/poc/assets", status_code=201, dependencies=[Depends(authorize)])
def upload(body: Upload):
    try:
        raw = decode_image(body.image_base64)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    asset_id, object_id = str(uuid.uuid4()), str(uuid.uuid4())
    ref = put_object(object_id, raw)
    # Preserve original bytes; create a separate analysis copy.
    copy_buffer = io.BytesIO()
    with Image.open(io.BytesIO(raw)) as source:
        analysis_image = source.convert("RGB")
        analysis_image.thumbnail((512, 512))
        analysis_image.save(copy_buffer, format="PNG")
    analysis_ref = put_object(str(uuid.uuid4()), copy_buffer.getvalue(), "analysis")
    with engine.begin() as connection:
        connection.execute(text("""INSERT INTO poc.assets(asset_id,case_id,filename,object_ref,analysis_ref,size_bytes)
          VALUES(:asset,:case,:name,CAST(:ref AS jsonb),CAST(:analysis AS jsonb),:size)"""),
          {"asset": asset_id, "case": CASE_ID, "name": body.filename, "ref": json.dumps(ref), "analysis": json.dumps(analysis_ref), "size": len(raw)})
    return {"asset_id": asset_id, "object_ref": ref, "size_bytes": len(raw), "development_only": True}


@app.post("/poc/jobs", status_code=202, dependencies=[Depends(authorize)])
def analyze(body: Analyze, idempotency_key: Annotated[str, Header(min_length=1, max_length=128)]):
    asset = str(body.asset_id)
    with engine.begin() as connection:
        if not connection.execute(text("SELECT 1 FROM poc.assets WHERE asset_id=:id AND case_id=:case"),
                                  {"id": asset, "case": CASE_ID}).first():
            raise HTTPException(404, "ASSET_NOT_FOUND")
        job_id = str(uuid.uuid4())
        inserted = connection.execute(text("""INSERT INTO poc.jobs(job_id,case_id,asset_id,idempotency_key,state)
          VALUES(:job,:case,:asset,:key,'QUEUED') ON CONFLICT(case_id,idempotency_key) DO NOTHING RETURNING job_id"""),
          {"job": job_id, "case": CASE_ID, "asset": asset, "key": idempotency_key}).first()
        if not inserted:
            prior = connection.execute(text("SELECT job_id,asset_id FROM poc.jobs WHERE case_id=:case AND idempotency_key=:key"),
                                       {"case": CASE_ID, "key": idempotency_key}).mappings().one()
            if str(prior["asset_id"]) != asset:
                raise HTTPException(409, "IDEMPOTENCY_CONFLICT")
            job_id = str(prior["job_id"])
        else:
            connection.execute(text("INSERT INTO poc.outbox(job_id) VALUES(:job)"), {"job": job_id})
    # Broker failures leave a recoverable outbox row, not a lost database task.
    from app.worker import dispatch_outbox
    try:
        dispatch_outbox()
    except Exception:
        log.warning("outbox delivery deferred; no secrets logged")
    return {"job_id": job_id, "state": "QUEUED", "development_only": True}


@app.get("/poc/jobs/{job_id}", dependencies=[Depends(authorize)])
def job(job_id: uuid.UUID):
    with engine.connect() as connection:
        row = connection.execute(text("SELECT job_id,state,result,error_code,attempts FROM poc.jobs WHERE job_id=:id AND case_id=:case"),
                                 {"id": str(job_id), "case": CASE_ID}).mappings().first()
    if not row:
        raise HTTPException(404, "JOB_NOT_FOUND")
    return dict(row)
