-- Incremental upgrade of the dedicated development schema. Never the 62-table business schema.
ALTER TABLE poc.jobs ADD COLUMN request_id uuid;
UPDATE poc.jobs SET request_id=job_id;
ALTER TABLE poc.jobs ALTER COLUMN request_id SET NOT NULL;
ALTER TABLE poc.jobs ADD COLUMN trace_origin text NOT NULL DEFAULT 'migration_job_id'
 CHECK(trace_origin IN ('api','migration_job_id'));
ALTER TABLE poc.jobs ADD COLUMN lease_token uuid;
ALTER TABLE poc.jobs ADD COLUMN run_version integer NOT NULL DEFAULT 1 CHECK(run_version>0);

ALTER TABLE poc.outbox ADD COLUMN event_id uuid;
ALTER TABLE poc.outbox ADD COLUMN event_payload jsonb;
UPDATE poc.outbox o SET event_id=o.job_id, event_payload=jsonb_build_object(
 'schema_version','1.0.0','event_type','poc.analysis.requested.v1',
 'event_id',o.job_id,'occurred_at',o.created_at,'request_id',j.request_id,
 'trace_origin',j.trace_origin,'case_id',j.case_id,'producer','migration.poc.v1',
 'payload',jsonb_build_object('job_id',j.job_id,'asset_id',j.asset_id))
 FROM poc.jobs j WHERE j.job_id=o.job_id;
ALTER TABLE poc.outbox ALTER COLUMN event_id SET NOT NULL;
ALTER TABLE poc.outbox ALTER COLUMN event_payload SET NOT NULL;
ALTER TABLE poc.outbox ADD CONSTRAINT outbox_event_id_unique UNIQUE(event_id);
ALTER TABLE poc.outbox ADD CONSTRAINT outbox_event_identity CHECK(
 jsonb_typeof(event_payload)='object'
 AND event_payload ?& ARRAY['schema_version','event_type','event_id','payload']
 AND event_payload->>'schema_version'='1.0.0'
 AND event_payload->>'event_type'='poc.analysis.requested.v1'
 AND (event_payload->>'event_id')::uuid=event_id
 AND (event_payload->'payload'->>'job_id')::uuid=job_id);

CREATE TABLE poc.job_events (
 event_id uuid PRIMARY KEY,
 job_id uuid NOT NULL REFERENCES poc.jobs(job_id),
 request_id uuid NOT NULL,
 event_type text NOT NULL CHECK(event_type IN (
  'job.created','job.claimed','job.succeeded','job.retry_scheduled','job.failed',
  'job.lease_expired','job.stale_result_rejected')),
 run_version integer NOT NULL CHECK(run_version>0),
 occurred_at timestamptz NOT NULL DEFAULT now(),
 details jsonb NOT NULL CHECK(jsonb_typeof(details)='object')
);
CREATE INDEX job_events_job_time ON poc.job_events(job_id,occurred_at,event_id);
CREATE INDEX jobs_expired_lease ON poc.jobs(lease_until) WHERE state='RUNNING';
