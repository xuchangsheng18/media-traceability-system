"""Checksummed, transaction-locked migrations for the dedicated development database."""

import hashlib

from psycopg import sql

from app.common import ROOT


def run_migrations(connection, migration_dir=None):
    directory = migration_dir or ROOT / "backend/migrations"
    assert connection.execute("SELECT current_database()").fetchone()[0] == "media_trace_poc", (
        "WRONG_DEVELOPMENT_DATABASE"
    )
    with connection.transaction():
        connection.execute("SELECT pg_advisory_xact_lock(2026101201)")
        connection.execute("CREATE SCHEMA IF NOT EXISTS poc")
        connection.execute("""CREATE TABLE IF NOT EXISTS poc.schema_migrations(
          version text PRIMARY KEY,sha256 text NOT NULL CHECK(sha256 ~ '^[a-f0-9]{64}$'),
          applied_at timestamptz NOT NULL DEFAULT now())""")
        applied = dict(connection.execute("SELECT version,sha256 FROM poc.schema_migrations").fetchall())
        files = sorted(directory.glob("[0-9][0-9][0-9][0-9]_*.sql"))
        assert not set(applied) - {p.name for p in files}, "APPLIED_MIGRATION_MISSING"
        changes = []
        for path in files:
            raw = path.read_bytes()
            digest = hashlib.sha256(raw).hexdigest()
            if path.name in applied:
                if applied[path.name] != digest:
                    raise RuntimeError("APPLIED_MIGRATION_CHECKSUM_CHANGED")
                continue
            if path.name == "0001_poc.sql" and connection.execute("SELECT to_regclass('poc.jobs')").fetchone()[0]:
                # Explicitly check the known legacy layout before adopting its version record.
                expected = {
                    "assets": {
                        "asset_id",
                        "case_id",
                        "filename",
                        "object_ref",
                        "analysis_ref",
                        "size_bytes",
                        "created_at",
                    },
                    "jobs": {
                        "job_id",
                        "case_id",
                        "asset_id",
                        "idempotency_key",
                        "state",
                        "result",
                        "error_code",
                        "attempts",
                        "lease_until",
                        "created_at",
                    },
                    "outbox": {"job_id", "sent_at", "created_at"},
                }
                for table, columns in expected.items():
                    actual = {
                        row[0]
                        for row in connection.execute(
                            "SELECT column_name FROM information_schema.columns WHERE table_schema='poc' AND table_name=%s",
                            (table,),
                        )
                    }
                    if actual != columns:
                        raise RuntimeError("LEGACY_SCHEMA_REQUIRES_REVIEW")
            connection.execute(raw.decode("utf-8"))
            connection.execute("INSERT INTO poc.schema_migrations(version,sha256) VALUES(%s,%s)", (path.name, digest))
            changes.append(path.name)
    return changes


def configure_application_grants(connection):
    connection.execute("GRANT USAGE ON SCHEMA poc TO poc_app")
    connection.execute("REVOKE ALL ON ALL TABLES IN SCHEMA poc FROM poc_app")
    connection.execute("GRANT SELECT,INSERT ON poc.assets,poc.jobs,poc.outbox,poc.job_events TO poc_app")
    connection.execute(
        "GRANT UPDATE(state,result,error_code,attempts,lease_until,lease_token,run_version) ON poc.jobs TO poc_app"
    )
    connection.execute("GRANT UPDATE(sent_at) ON poc.outbox TO poc_app")
    # No ordinary update/delete of input references, event envelopes, audit rows or migration history.
    connection.execute(sql.SQL("ALTER ROLE {} NOSUPERUSER NOBYPASSRLS").format(sql.Identifier("poc_app")))
