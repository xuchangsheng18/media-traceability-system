"""Atomic claims and token-fenced writes; all state/audit effects share a transaction."""

import json
import uuid

from sqlalchemy import text

from app.common import CASE_ID
from app.db import engine


def audit(connection, job, kind, details=None):
    connection.execute(
        text("""INSERT INTO poc.job_events(event_id,job_id,request_id,event_type,run_version,details)
      VALUES(:event,:job,:request,:kind,:version,CAST(:details AS jsonb))"""),
        {
            "event": str(uuid.uuid4()),
            "job": str(job["job_id"]),
            "request": str(job["request_id"]),
            "kind": kind,
            "version": job.get("run_version", 1),
            "details": json.dumps(details or {}),
        },
    )


def claim_job(event):
    payload = event["payload"]
    with engine.begin() as connection:
        row = (
            connection.execute(
                text("""UPDATE poc.jobs SET state='RUNNING',attempts=attempts+1,
          run_version=attempts+1,lease_token=:lease,lease_until=now()+interval '35 seconds',error_code=NULL
          WHERE job_id=:job AND asset_id=:asset AND case_id=:case AND request_id=:request
          AND (state='QUEUED' OR (state='RUNNING' AND lease_until<now())) AND attempts<3
          RETURNING job_id,asset_id,case_id,request_id,run_version,lease_token,attempts"""),
                {
                    "job": payload["job_id"],
                    "asset": payload["asset_id"],
                    "case": CASE_ID,
                    "request": event["request_id"],
                    "lease": str(uuid.uuid4()),
                },
            )
            .mappings()
            .first()
            if event["case_id"] == CASE_ID
            else None
        )
        if row is None:
            return None
        claimed = dict(row)
        audit(connection, claimed, "job.claimed", {"attempt": claimed["attempts"]})
        return claimed


def finish_job(claim, result=None, error_code=None, retry=False):
    with engine.begin() as connection:
        state = "SUCCEEDED" if result is not None else "QUEUED" if retry else "FAILED"
        changed = connection.execute(
            text("""UPDATE poc.jobs SET state=:state,result=CAST(:result AS jsonb),
          error_code=:error,lease_until=NULL,lease_token=NULL WHERE job_id=:job AND case_id=:case
          AND state='RUNNING' AND lease_token=:lease AND run_version=:version AND lease_until>now()"""),
            {
                "state": state,
                "result": json.dumps(result) if result is not None else None,
                "error": error_code,
                "job": str(claim["job_id"]),
                "case": CASE_ID,
                "lease": str(claim["lease_token"]),
                "version": claim["run_version"],
            },
        ).rowcount
        if changed:
            kind = "job.succeeded" if state == "SUCCEEDED" else "job.retry_scheduled" if retry else "job.failed"
            audit(connection, claim, kind, {"error_code": error_code} if error_code else {})
        else:
            audit(connection, claim, "job.stale_result_rejected", {"lease_token": str(claim["lease_token"])})
        return changed == 1
