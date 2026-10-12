import datetime
import json
import os
import uuid
from pathlib import Path

import httpx
from celery import Celery
from sqlalchemy import text

from app.common import CASE_ID
from app.db import engine

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
        connection.execute(text("""UPDATE poc.jobs SET state='FAILED',error_code='ATTEMPTS_EXHAUSTED'
          WHERE state='RUNNING' AND lease_until<now() AND attempts>=3"""))
        recovered = connection.execute(text("""UPDATE poc.jobs SET state='QUEUED',lease_until=NULL
          WHERE state='RUNNING' AND lease_until<now() AND attempts<3 RETURNING job_id""")).all()
        for job in recovered:
            connection.execute(text("UPDATE poc.outbox SET sent_at=NULL WHERE job_id=:id"), {"id": job.job_id})
        rows = connection.execute(text("SELECT job_id FROM poc.outbox WHERE sent_at IS NULL ORDER BY created_at LIMIT 20 FOR UPDATE SKIP LOCKED")).all()
        for row in rows:
            celery.send_task("poc.analyze", args=[str(row.job_id)], task_id=str(row.job_id))
            connection.execute(text("UPDATE poc.outbox SET sent_at=now() WHERE job_id=:id"), {"id": row.job_id})
    Path("/tmp/mt-worker-heartbeat").touch()
    return len(rows)


@celery.task(name="poc.analyze", bind=True, max_retries=2, soft_time_limit=25, time_limit=30)
def analyze(self, job_id):
    with engine.begin() as connection:
        row = connection.execute(text("""UPDATE poc.jobs SET state='RUNNING',attempts=attempts+1,
          lease_until=now()+interval '35 seconds' WHERE job_id=:id AND
          (state='QUEUED' OR (state='RUNNING' AND lease_until<now())) AND attempts<3 RETURNING asset_id"""), {"id": job_id}).first()
        if not row:
            return "already handled"
        ref = connection.execute(text("SELECT analysis_ref FROM poc.assets WHERE asset_id=:id AND case_id=:case"),
                                 {"id": row.asset_id, "case": CASE_ID}).scalar_one()
    request = {"request_id": str(uuid.uuid4()), "case_id": CASE_ID, "task_id": job_id, "run_version": 1,
               "capability": "retrieval.image_embedding", "model_name": "synthetic-cpu-encoder", "model_version": "demo-1",
               "input_kind": "analysis_copy", "asset_ids": [str(row.asset_id)], "object_refs": [ref], "source_segment_ids": [],
               "preprocessing_version": "gray4x4-1", "mapping_version": "poc-analysis-copy-1", "missing_modalities": [],
               "deadline_at": (datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(seconds=20)).isoformat(),
               "authorization_version": "development-only-1"}
    try:
        response = httpx.post(os.environ["INFERENCE_URL"]+"/internal/v1/inference/retrieval.image_embedding", json=request,
                              headers={"Authorization": "Bearer "+os.environ["INTERNAL_TOKEN"]}, timeout=20)
        response.raise_for_status()
        result = response.json()
        with engine.begin() as connection:
            connection.execute(text("UPDATE poc.jobs SET state='SUCCEEDED',result=CAST(:r AS jsonb),lease_until=NULL WHERE job_id=:id AND state='RUNNING'"),
                               {"id": job_id, "r": json.dumps(result)})
    except Exception:
        with engine.begin() as connection:
            connection.execute(text("UPDATE poc.jobs SET state=:s,error_code='INFERENCE_FAILED',lease_until=NULL WHERE job_id=:id"),
                               {"id": job_id, "s": "QUEUED" if self.request.retries < 2 else "FAILED"})
        if self.request.retries < 2:
            raise self.retry(countdown=2)
        return "failed"
    return "complete"
