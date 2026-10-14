import importlib.util
from pathlib import Path

import psycopg
import pytest

ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS = ROOT / "backend/business_migrations"


def migrate(dsn, directory=MIGRATIONS):
    source = MIGRATIONS / "runner.py"
    assert source.is_file(), "independent versioned business migrations are not implemented"
    spec = importlib.util.spec_from_file_location("business_migration_runner", source)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.apply_migrations(dsn, directory)


def test_empty_database_migrates_and_replay_noops(database_dsn):
    assert migrate(database_dsn) == ["0001", "0002"]
    assert migrate(database_dsn) == []
    with psycopg.connect(database_dsn) as connection:
        assert (
            connection.execute(
                "SELECT count(*) FROM information_schema.tables WHERE table_schema='mt' AND table_type='BASE TABLE'"
            ).fetchone()[0]
            == 62
        )
        assert (
            connection.execute("SELECT count(*) FROM information_schema.columns WHERE table_schema='mt'").fetchone()[0]
            == 825
        )
        assert (
            connection.execute("SELECT rolbypassrls OR rolsuper FROM pg_roles WHERE rolname='mt_runtime'").fetchone()[0]
            is False
        )


def test_changed_migration_digest_rejected(database_dsn, tmp_path):
    migrate(database_dsn)
    for original in MIGRATIONS.glob("*.sql"):
        (tmp_path / original.name).write_bytes(original.read_bytes() + b"\n-- modified\n")
    with pytest.raises(RuntimeError, match="DIGEST"):
        migrate(database_dsn, tmp_path)


def test_untracked_existing_mt_schema_rejected(database_dsn):
    with psycopg.connect(database_dsn) as connection:
        connection.execute("CREATE SCHEMA mt")
    with pytest.raises(RuntimeError, match="UNTRACKED"):
        migrate(database_dsn)


def test_mid_migration_failure_is_atomic(database_dsn, tmp_path):
    (tmp_path / "0001_marker.sql").write_text("CREATE SCHEMA mt; CREATE TABLE mt.marker(id integer);")
    (tmp_path / "0002_failure.sql").write_text("CREATE TABLE mt.partial(id integer); SELECT no_such_function();")
    with pytest.raises(psycopg.Error):
        migrate(database_dsn, tmp_path)
    with psycopg.connect(database_dsn) as connection:
        assert connection.execute("SELECT to_regnamespace('mt')").fetchone()[0] is None
        assert connection.execute("SELECT to_regclass('mt_meta.schema_migrations')").fetchone()[0] is None
