"""Apply checksum-bound business migrations atomically to explicitly isolated databases."""

import hashlib
from pathlib import Path

import psycopg
from psycopg.conninfo import conninfo_to_dict


def apply_migrations(dsn: str, directory: Path) -> list[str]:
    database = conninfo_to_dict(dsn).get("dbname", "")
    if not database.startswith("mt_business_"):
        raise RuntimeError("EXPLICIT_ISOLATED_BUSINESS_DATABASE_REQUIRED")
    files = sorted(directory.glob("*.sql"))
    if not files:
        raise RuntimeError("BUSINESS_MIGRATION_DIRECTORY_EMPTY")
    versions = [file.name.split("_", 1)[0] for file in files]
    if len(set(versions)) != len(files) or any(not value.isdigit() for value in versions):
        raise RuntimeError("BUSINESS_MIGRATION_VERSIONS_INVALID")
    applied: list[str] = []
    with psycopg.connect(dsn) as connection:
        connection.execute("SELECT pg_advisory_xact_lock(hashtext('media_trace_business_migrations'))")
        mt_exists = connection.execute("SELECT to_regnamespace('mt') IS NOT NULL").fetchone()
        ledger_exists = connection.execute("SELECT to_regclass('mt_meta.schema_migrations') IS NOT NULL").fetchone()
        assert mt_exists is not None and ledger_exists is not None
        if mt_exists[0] and not ledger_exists[0]:
            raise RuntimeError("UNTRACKED_EXISTING_BUSINESS_SCHEMA")
        connection.execute("CREATE SCHEMA IF NOT EXISTS mt_meta")
        connection.execute("REVOKE ALL ON SCHEMA mt_meta FROM PUBLIC")
        connection.execute("""CREATE TABLE IF NOT EXISTS mt_meta.schema_migrations (
            version text PRIMARY KEY, sha256 text NOT NULL, applied_at timestamptz NOT NULL DEFAULT now())""")
        rows = connection.execute("SELECT version,sha256 FROM mt_meta.schema_migrations ORDER BY version").fetchall()
        registered = dict(rows)
        if set(registered) - set(versions):
            raise RuntimeError("UNKNOWN_APPLIED_BUSINESS_MIGRATION")
        if mt_exists[0] and not registered:
            raise RuntimeError("UNTRACKED_EXISTING_BUSINESS_SCHEMA")
        for version, file in zip(versions, files):
            raw = file.read_bytes()
            digest = hashlib.sha256(raw).hexdigest()
            if version in registered:
                if registered[version] != digest:
                    raise RuntimeError("BUSINESS_MIGRATION_DIGEST_CHANGED")
                continue
            connection.execute(raw.decode("utf-8"))
            connection.execute("INSERT INTO mt_meta.schema_migrations(version,sha256) VALUES(%s,%s)", (version, digest))
            applied.append(version)
    return applied
