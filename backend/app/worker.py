import datetime
import json
import logging
import os
import uuid
from pathlib import Path

import httpx
from celery import Celery
from sqlalchemy import text

from app.common import CASE_ID
from app.contracts import EVENT, validate_model_result
from app.db import engine
from app.leases import audit, claim_job, finish_job

log = logging.getLogger("media_trace")
celery = Celery("media_trace_poc", broker=os.environ["BROKER_URL"])
celery.conf.update(task_acks_late=True, task_reject_on_worker_lost=True, worker_prefetch_multiplier=1,
                   worker_enable_remote_control=False, event_queue_exclusive=True,
                   worker_send_task_events=False, task_default_delivery_mode=2,
                   broker_transport_options={"confirm_publish": True},
                   task_serializer="json", accept_content=["json"], broker_connection_retry_on_startup=True,
                   beat_schedule={"recover-outbox": {"task": "poc.dispatch", "schedule": 5.0}})


@celery.task(name="poc.dispatch")
def dispatch_outbox():
    with engine.begin() as connection:
        expired = connection.execute(text("""SELECT job_id,request_id,run_version,attempts FROM poc.jobs
          WHERE case_id=:case AND state='RUNNING' AND lease_until<now() FOR UPDATE SKIP LOCKED"""),
          {"case": CASE_ID}).mappings().all()
        for row in expired:
            exhausted = row["attempts"] >= 3
            connection.execute(text("""UPDATE poc.jobs SET state=:state,lease_token=NULL,lease_until=NULL,error_code=:error
              WHERE job_id=:job"""), {"job": row["job_id"], "state": "FAILED" if exhausted else "QUEUED",
                                      "error": "ATTEMPTS_EXHAUSTED" if exhausted else None})
            audit(connection, row, "job.failed" if exhausted else "job.lease_expired", {"attempts": row["attempts"]})
            if not exhausted:
                connection.execute(text("UPDATE poc.outbox SET sent_at=NULL WHERE job_id=:job"), {"job": row["job_id"]})
        rows = connection.execute(text("""SELECT o.job_id,o.event_payload FROM poc.outbox o JOIN poc.jobs j ON j.job_id=o.job_id
          WHERE o.sent_at IS NULL AND j.state='QUEUED' AND j.case_id=:case ORDER BY o.created_at
          LIMIT 20 FOR UPDATE OF o SKIP LOCKED"""), {"case": CASE_ID}).mappings().all()
        for row in rows:
            event = row["event_payload"]
            EVENT.validate(event)
            celery.send_task("poc.analyze", args=[event], task_id=str(row["job_id"]),
                             argsrepr="[validated development event]", headers={"request_id": event["request_id"]})
            connection.execute(text("UPDATE poc.outbox SET sent_at=now() WHERE job_id=:id"), {"id": row["job_id"]})
    Path("/tmp/mt-worker-heartbeat").touch()
    return len(rows)


def resolve_event(event):
    # Transitional bridge for UUID-only messages queued by development baseline 1.0.
    if isinstance(event, str):
        job_id = str(uuid.UUID(event))
        with engine.connect() as connection:
            event = connection.execute(text("""SELECT o.event_payload FROM poc.outbox o JOIN poc.jobs j ON j.job_id=o.job_id
              WHERE o.job_id=:job AND j.case_id=:case"""), {"job": job_id, "case": CASE_ID}).scalar_one()
    try:
        EVENT.validate(event)
    except Exception:
        raise ValueError("EVENT_CONTRACT_INVALID") from None
    return event


@celery.task(name="poc.analyze", bind=True, max_retries=2, soft_time_limit=25, time_limit=30)
def analyze(self, event):
    event = resolve_event(event)
    claim = claim_job(event)
    if claim is None:
        return "already handled or scope mismatch"
    with engine.connect() as connection:
        ref = connection.execute(text("SELECT analysis_ref FROM poc.assets WHERE asset_id=:asset AND case_id=:case"),
                                 {"asset": claim["asset_id"], "case": CASE_ID}).scalar_one()
    request = {"request_id": str(claim["request_id"]), "case_id": CASE_ID, "task_id": str(claim["job_id"]),
               "run_version": claim["run_version"], "capability": "retrieval.image_embedding",
               "model_name": "synthetic-cpu-encoder", "model_version": "demo-1",
               "input_kind": "analysis_copy", "asset_ids": [str(claim["asset_id"])], "object_refs": [ref], "source_segment_ids": [],
               "preprocessing_version": "gray4x4-1", "mapping_version": "poc-analysis-copy-1", "missing_modalities": [],
               "deadline_at": (datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(seconds=20)).isoformat(),
               "authorization_version": "development-only-1"}
    try:
        response = httpx.post(os.environ["INFERENCE_URL"]+"/internal/v1/inference/retrieval.image_embedding", json=request,
                              headers={"Authorization": "Bearer "+os.environ["INTERNAL_TOKEN"], "X-Request-ID": request["request_id"]}, timeout=20)
        response.raise_for_status()
        result = response.json()
        validate_model_result(request, result)
        accepted = finish_job(claim, result=result)
        log.info(json.dumps({"event": "job.finished", "job_id": request["task_id"], "request_id": request["request_id"],
                             "run_version": request["run_version"], "accepted": accepted}))
        return "complete" if accepted else "stale lease rejected"
    except Exception:
        retry = self.request.retries < 2 and claim["attempts"] < 3
        accepted = finish_job(claim, error_code="INFERENCE_FAILED", retry=retry)
        if accepted and retry:
            raise self.retry(args=(event,), countdown=2)
        return "failed" if accepted else "stale lease rejected"
