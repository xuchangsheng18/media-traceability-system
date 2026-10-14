import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from tests.business.test_history import history_context as history_context
from tests.business.test_history import repository, scope


def pg_tool(command, dsn, *args):
    prefix = Path(
        os.environ.get(
            "MT_BUSINESS_PG_BIN", "/workspace/glwy/runtime/media-traceability-system/business-postgres-tools/bin"
        )
    )
    binary = prefix / command
    version = subprocess.check_output([str(binary), "--version"], text=True).strip()
    assert " 16." in version, "PostgreSQL16 recovery tools required"
    values = conninfo_to_dict(dsn)
    secret = str(values.pop("password", "") or "")
    result = subprocess.run(
        [
            str(binary),
            "--dbname",
            make_conninfo("", **{key: str(value) for key, value in values.items() if value is not None}),
            *args,
        ],
        env=dict(os.environ, PGPASSWORD=secret),
        capture_output=True,
    )
    assert result.returncode == 0, "Isolated recovery command failed; raw credentials and SQL logs withheld"
    return version


def test_real_backup_restores_uploads_objects_and_two_snapshots(history_context, tmp_path):
    assert history_context is not None
    from business_app.db import Database
    from business_app.history.repository import ResultRepository
    from business_app.objects import FileObjectStore
    from business_app.types import ResultKey

    from tests.business.history_fixtures import snapshot

    context = history_context
    source = repository(context)
    expected = [snapshot(context, run) for run in [1, 2]]
    for item in expected:
        source.append_snapshot(scope(context), item)
    name = "mt_business_restore_" + uuid4().hex
    restored_admin = make_conninfo(context["admin_dsn"], dbname=name)
    dump = tmp_path / "business.dump"
    tool_version = pg_tool("pg_dump", context["admin_dsn"], "-Fc", "--no-owner", "--file", str(dump))
    shutil.copytree(context["settings"].object_root, tmp_path / "restored-objects")
    with psycopg.connect(context["admin_dsn"], autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {} TEMPLATE template0").format(sql.Identifier(name)))
        database = None
        try:
            pg_tool("pg_restore", restored_admin, "--no-owner", "--exit-on-error", str(dump))
            counts = {}
            with psycopg.connect(restored_admin) as target, psycopg.connect(context["admin_dsn"]) as original:
                for table in [
                    "upload_session",
                    "upload_part",
                    "object_version",
                    "media_asset",
                    "task_run",
                    "task_result",
                ]:
                    statement = sql.SQL("SELECT count(*) FROM mt.{}").format(sql.Identifier(table))
                    left, right = original.execute(statement).fetchone(), target.execute(statement).fetchone()
                    assert left == right and right is not None
                    counts[table] = right[0]
                assert (
                    original.execute("SELECT version,sha256 FROM mt_meta.schema_migrations ORDER BY version").fetchall()
                    == target.execute(
                        "SELECT version,sha256 FROM mt_meta.schema_migrations ORDER BY version"
                    ).fetchall()
                )
            database = Database(make_conninfo(context["settings"].database_dsn, dbname=name))
            restored = ResultRepository(database, FileObjectStore(tmp_path / "restored-objects"), context["authority"])
            for run, item in enumerate(expected, 1):
                assert restored.load_exact(scope(context), ResultKey(context["task_id"], run, 1)) == item
            report = {
                "status": "PASS",
                "scope": "self_owned_isolated_batch_not_production_disaster_recovery",
                "dump_sha256": hashlib.sha256(dump.read_bytes()).hexdigest(),
                "tool_version": tool_version,
                "restored_row_counts": counts,
                "exact_historical_snapshots": 2,
                "private_object_digests_verified": True,
                "migration_ledger_match": True,
                "formal_accepted": False,
            }
            Path("docs/00-project/validation/business-recovery-report.json").write_text(
                json.dumps(report, indent=2) + "\n"
            )
        finally:
            if database is not None:
                database.close()
            assert name.startswith("mt_business_restore_")
            admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name)))
