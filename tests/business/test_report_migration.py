"""The 0013 report-read upgrade preserves 0012 tables, registries and privileges."""

import hashlib
import re

import psycopg
import pytest

from tests.business.test_migrations import MIGRATIONS, migrate


def schema_snapshot(connection):
    queries = {
        "columns": "SELECT table_name,column_name,data_type,column_default,is_nullable "
        "FROM information_schema.columns WHERE table_schema='mt' ORDER BY table_name,ordinal_position",
        "tables": "SELECT relname,relacl,relrowsecurity,relforcerowsecurity FROM pg_class "
        "WHERE relnamespace='mt'::regnamespace ORDER BY relname",
        "constraints": "SELECT conname,conrelid::regclass::text,pg_get_constraintdef(oid) "
        "FROM pg_constraint WHERE connamespace='mt'::regnamespace ORDER BY conrelid,conname",
        "policies": "SELECT tablename,policyname,permissive,roles,cmd,qual,with_check "
        "FROM pg_policies WHERE schemaname='mt' ORDER BY tablename,policyname",
        "function_acl": "SELECT oid::regprocedure::text,proacl,proowner,prosecdef,provolatile,proconfig "
        "FROM pg_proc WHERE pronamespace='mt'::regnamespace ORDER BY oid::regprocedure::text",
    }
    return {key: connection.execute(query).fetchall() for key, query in queries.items()}


@pytest.mark.parametrize("fail_after_functions", [False, True])
def test_report_upgrade_is_function_only_preserves_old_scope_and_replays_or_rolls_back(
    database_dsn, tmp_path, fail_after_functions
):
    previous = [file for file in sorted(MIGRATIONS.glob("*.sql")) if file.name[:4] <= "0012"]
    for file in previous:
        (tmp_path / file.name).write_bytes(file.read_bytes())
    assert migrate(database_dsn, tmp_path) == [f"{version:04d}" for version in range(1, 13)]
    with psycopg.connect(database_dsn) as connection:
        before = schema_snapshot(connection)
        function_row = connection.execute("SELECT pg_get_functiondef('mt.scope_operation()'::regprocedure)").fetchone()
        assert function_row is not None
        function = function_row[0]
        operations = sorted(set(re.findall(r"'([A-Za-z][A-Za-z0-9]+)'", function)) | {"getReport", "unknownOperation"})
        kinds = [
            "approval",
            "asset",
            "cluster",
            "evidence_package",
            "export",
            "feedback",
            "import",
            "operation",
            "policy",
            "report",
            "review",
            "source",
            "task",
            "upload",
            "user",
            "unknown",
        ]
        old_lookup = connection.execute(
            "SELECT kind,operation,mt.scope_lookup_kind_allowed(kind,operation) "
            "FROM unnest(%s::text[]) AS k(kind) CROSS JOIN unnest(%s::text[]) AS o(operation) ORDER BY 1,2",
            (kinds, operations),
        ).fetchall()
        old_operation = {}
        for name in operations:
            connection.execute("SELECT set_config('app.operation_id',%s,true)", (name,))
            operation_row = connection.execute("SELECT mt.scope_operation()").fetchone()
            assert operation_row is not None
            old_operation[name] = operation_row[0]
        old_functions = connection.execute(
            "SELECT oid::regprocedure::text,pg_get_functiondef(oid) "
            "FROM pg_proc WHERE pronamespace='mt'::regnamespace ORDER BY 1"
        ).fetchall()
    migration = MIGRATIONS / "0013_report_reads.sql"
    (tmp_path / migration.name).write_bytes(
        migration.read_bytes() + (b"\nSELECT missing_report_upgrade_function();\n" if fail_after_functions else b"")
    )
    if fail_after_functions:
        with pytest.raises(psycopg.Error):
            migrate(database_dsn, tmp_path)
    else:
        assert migrate(database_dsn, tmp_path) == ["0013"]
        assert migrate(database_dsn, tmp_path) == []
    with psycopg.connect(database_dsn) as connection:
        assert schema_snapshot(connection) == before
        assert connection.execute(
            "SELECT version,sha256 FROM mt_meta.schema_migrations WHERE version<='0012' ORDER BY version"
        ).fetchall() == [(file.name[:4], hashlib.sha256(file.read_bytes()).hexdigest()) for file in previous]
        for kind, operation, allowed in old_lookup:
            expected = True if not fail_after_functions and (kind, operation) == ("report", "getReport") else allowed
            assert connection.execute("SELECT mt.scope_lookup_kind_allowed(%s,%s)", (kind, operation)).fetchone() == (
                expected,
            )
        for name, value in old_operation.items():
            connection.execute("SELECT set_config('app.operation_id',%s,true)", (name,))
            expected = "getReport" if not fail_after_functions and name == "getReport" else value
            assert connection.execute("SELECT mt.scope_operation()").fetchone() == (expected,)
        changed = {
            "mt.scope_operation()",
            "mt.scope_lookup_kind_allowed(text,text)",
            "mt.lookup_scope_metadata(text,uuid)",
        }
        for signature, definition in old_functions:
            if fail_after_functions or signature not in changed:
                assert connection.execute("SELECT pg_get_functiondef(%s::regprocedure)", (signature,)).fetchone() == (
                    definition,
                )
