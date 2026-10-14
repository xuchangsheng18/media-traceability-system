import datetime
import hmac
import io
import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from PIL import Image
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text

from app.common import CASE_ID, decode_image, put_object
from app.contracts import EVENT
from app.db import engine, health
from app.leases import audit
from app.observability import configure
from app.settings import validate_runtime


@asynccontextmanager
async def lifespan(_):
    validate_runtime()
    yield


app = FastAPI(
    title="Media Trace CPU PoC",
    version="0.1.0",
    docs_url="/poc/docs",
    openapi_url="/poc/openapi.json",
    lifespan=lifespan,
)
log = logging.getLogger("media_trace")
configure(app)


def authorize(authorization: Annotated[str | None, Header()] = None):
    token = os.environ.get("POC_API_TOKEN", "")
    if not token or not authorization or not hmac.compare_digest(authorization, "Bearer " + token):
        raise HTTPException(401, "AUTH_REQUIRED")


class Upload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    filename: str = Field(min_length=1, max_length=120)
    image_base64: str = Field(min_length=1, max_length=2 * 1024 * 1024)


class Analyze(BaseModel):
    model_config = ConfigDict(extra="forbid")
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
        connection.execute(
            text("""INSERT INTO poc.assets(asset_id,case_id,filename,object_ref,analysis_ref,size_bytes)
          VALUES(:asset,:case,:name,CAST(:ref AS jsonb),CAST(:analysis AS jsonb),:size)"""),
            {
                "asset": asset_id,
                "case": CASE_ID,
                "name": body.filename,
                "ref": json.dumps(ref),
                "analysis": json.dumps(analysis_ref),
                "size": len(raw),
            },
        )
    return {"asset_id": asset_id, "object_ref": ref, "size_bytes": len(raw), "development_only": True}


@app.post("/poc/jobs", status_code=202, dependencies=[Depends(authorize)])
def analyze(body: Analyze, request: Request, idempotency_key: Annotated[str, Header(min_length=1, max_length=128)]):
    asset = str(body.asset_id)
    with engine.begin() as connection:
        if not connection.execute(
            text("SELECT 1 FROM poc.assets WHERE asset_id=:id AND case_id=:case"), {"id": asset, "case": CASE_ID}
        ).first():
            raise HTTPException(404, "ASSET_NOT_FOUND")
        job_id = str(uuid.uuid4())
        inserted = connection.execute(
            text("""INSERT INTO poc.jobs(job_id,case_id,asset_id,idempotency_key,state,request_id,trace_origin)
          VALUES(:job,:case,:asset,:key,'QUEUED',:request,'api') ON CONFLICT(case_id,idempotency_key) DO NOTHING RETURNING job_id"""),
            {
                "job": job_id,
                "case": CASE_ID,
                "asset": asset,
                "key": idempotency_key,
                "request": request.state.request_id,
            },
        ).first()
        if not inserted:
            prior = (
                connection.execute(
                    text("SELECT job_id,asset_id FROM poc.jobs WHERE case_id=:case AND idempotency_key=:key"),
                    {"case": CASE_ID, "key": idempotency_key},
                )
                .mappings()
                .one()
            )
            if str(prior["asset_id"]) != asset:
                raise HTTPException(409, "IDEMPOTENCY_CONFLICT")
            job_id = str(prior["job_id"])
        else:
            event_id = str(uuid.uuid4())
            event = {
                "event_id": event_id,
                "schema_version": "1.0.0",
                "event_type": "poc.analysis.requested.v1",
                "occurred_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "request_id": request.state.request_id,
                "trace_origin": "api",
                "case_id": CASE_ID,
                "producer": "backend.poc",
                "payload": {"job_id": job_id, "asset_id": asset},
            }
            EVENT.validate(event)
            connection.execute(
                text(
                    "INSERT INTO poc.outbox(job_id,event_id,event_payload) VALUES(:job,:event,CAST(:payload AS jsonb))"
                ),
                {"job": job_id, "event": event_id, "payload": json.dumps(event)},
            )
            audit(connection, {"job_id": job_id, "request_id": request.state.request_id}, "job.created")
    # Broker failures leave a recoverable outbox row, not a lost database task.
    from app.worker import dispatch_outbox

    try:
        dispatch_outbox()
    except Exception:
        log.warning(json.dumps({"event": "outbox.deferred", "request_id": request.state.request_id, "job_id": job_id}))
    with engine.connect() as connection:
        current = (
            connection.execute(
                text("SELECT state,request_id FROM poc.jobs WHERE job_id=:job AND case_id=:case"),
                {"job": job_id, "case": CASE_ID},
            )
            .mappings()
            .one()
        )
    return {
        "job_id": job_id,
        "state": current["state"],
        "task_request_id": str(current["request_id"]),
        "development_only": True,
    }


@app.get("/poc/jobs/{job_id}", dependencies=[Depends(authorize)])
def job(job_id: uuid.UUID):
    with engine.connect() as connection:
        row = (
            connection.execute(
                text(
                    "SELECT job_id,state,result,error_code,attempts,run_version,request_id,trace_origin FROM poc.jobs WHERE job_id=:id AND case_id=:case"
                ),
                {"id": str(job_id), "case": CASE_ID},
            )
            .mappings()
            .first()
        )
    if not row:
        raise HTTPException(404, "JOB_NOT_FOUND")
    return dict(row)
