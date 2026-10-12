-- Dedicated CPU development database only. Separate from the 62-table mt proposal.
CREATE SCHEMA IF NOT EXISTS poc;
CREATE TABLE IF NOT EXISTS poc.assets (
 asset_id uuid PRIMARY KEY, case_id uuid NOT NULL, filename text NOT NULL,
 object_ref jsonb NOT NULL, analysis_ref jsonb NOT NULL, size_bytes bigint NOT NULL CHECK(size_bytes>0),
 created_at timestamptz NOT NULL DEFAULT now(), UNIQUE(case_id,asset_id)
);
CREATE TABLE IF NOT EXISTS poc.jobs (
 job_id uuid PRIMARY KEY, case_id uuid NOT NULL, asset_id uuid NOT NULL,
 idempotency_key text NOT NULL, state text NOT NULL CHECK(state IN ('QUEUED','RUNNING','SUCCEEDED','FAILED')),
 result jsonb, error_code text, attempts integer NOT NULL DEFAULT 0, lease_until timestamptz,
 created_at timestamptz NOT NULL DEFAULT now(), UNIQUE(case_id,idempotency_key),
 FOREIGN KEY(case_id,asset_id) REFERENCES poc.assets(case_id,asset_id)
);
CREATE TABLE IF NOT EXISTS poc.outbox (
 job_id uuid PRIMARY KEY REFERENCES poc.jobs(job_id), sent_at timestamptz,
 created_at timestamptz NOT NULL DEFAULT now()
);
