"""0013→0014 upgrade invariants; execute only against a new isolated database."""

import hashlib
import re

import psycopg
import pytest

from tests.business.test_migrations import MIGRATIONS, migrate
from tests.business.test_report_migration import schema_snapshot

NEW_OPERATIONS = {"downloadAsset", "createSource", "listModels", "listEvaluations"}
NEW_KIND_PAIRS = {
    ("asset", "downloadAsset"),
    ("operation", "createSource"),
    ("user", "listModels"),
    ("user", "listEvaluations"),
    ("model", "listModels"),
    ("model_evaluation", "listEvaluations"),
}
CHANGED_FUNCTIONS = {
    "mt.scope_operation()",
    "mt.scope_lookup_kind_allowed(text,text)",
    "mt.lookup_scope_metadata(text,uuid)",
}
ARTIFACT_FUNCTION = "mt.model_evaluation_artifact_metadata(uuid)"


def function_definitions(connection):
    return dict(
        connection.execute(
            "SELECT oid::regprocedure::text,pg_get_functiondef(oid) FROM pg_proc "
            "WHERE pronamespace='mt'::regnamespace ORDER BY 1"
        ).fetchall()
    )


def operation_literals(definition):
    return set(re.findall(r"'([A-Za-z][A-Za-z0-9]+)'", definition))


def operation_value(connection, name):
    connection.execute("SELECT set_config('app.operation_id',%s,true)", (name,))
    return connection.execute("SELECT mt.scope_operation()").fetchone()[0]


@pytest.mark.parametrize("fail_at_end", [False, True])
def test_0014_resource_registry_upgrade_preserves_schema_acl_history_and_is_atomic(database_dsn, tmp_path, fail_at_end):
    previous = [file for file in sorted(MIGRATIONS.glob("*.sql")) if file.name[:4] <= "0013"]
    assert [file.name[:4] for file in previous] == [f"{version:04d}" for version in range(1, 14)]
    for file in previous:
        (tmp_path / file.name).write_bytes(file.read_bytes())
    assert migrate(database_dsn, tmp_path) == [f"{version:04d}" for version in range(1, 14)]
    with psycopg.connect(database_dsn) as connection:
        before = schema_snapshot(connection)
        old_functions = function_definitions(connection)
        old_operations = operation_literals(old_functions["mt.scope_operation()"])
        operations = old_operations | NEW_OPERATIONS | {"unknownOperation", "", "downloadAsset;SELECT"}
        kinds = {
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
            "model",
            "model_evaluation",
            "unknown",
            "",
        }
        old_operation_values = {name: operation_value(connection, name) for name in operations}
        assert all(old_operation_values[name] is None for name in NEW_OPERATIONS)
        old_pairs = {
            (kind, operation): allowed
            for kind, operation, allowed in connection.execute(
                "SELECT kind,operation,mt.scope_lookup_kind_allowed(kind,operation) "
                "FROM unnest(%s::text[]) AS k(kind) CROSS JOIN unnest(%s::text[]) AS o(operation)",
                (sorted(kinds), sorted(operations)),
            ).fetchall()
        }
        assert all(old_pairs[pair] is False for pair in NEW_KIND_PAIRS)
        owner_row = connection.execute("SELECT oid FROM pg_roles WHERE rolname=current_user").fetchone()
        assert owner_row is not None
        migration_owner = owner_row[0]
    upgrades = list(MIGRATIONS.glob("0014_*.sql"))
    assert len(upgrades) == 1, "exactly one reviewed 0014 upgrade is required"
    upgrade = upgrades[0]
    (tmp_path / upgrade.name).write_bytes(
        upgrade.read_bytes() + (b"\nSELECT missing_resource_registry_upgrade_function();\n" if fail_at_end else b"")
    )
    if fail_at_end:
        with pytest.raises(psycopg.errors.UndefinedFunction, match="missing_resource_registry_upgrade_function"):
            migrate(database_dsn, tmp_path)
    else:
        assert migrate(database_dsn, tmp_path) == ["0014"]
        assert migrate(database_dsn, tmp_path) == []
    with psycopg.connect(database_dsn) as connection:
        after = schema_snapshot(connection)
        new_functions = function_definitions(connection)
        assert connection.execute(
            "SELECT version,sha256 FROM mt_meta.schema_migrations WHERE version<='0013' ORDER BY version"
        ).fetchall() == [(file.name[:4], hashlib.sha256(file.read_bytes()).hexdigest()) for file in previous]
        assert connection.execute("SELECT count(*) FROM mt_meta.schema_migrations WHERE version='0014'").fetchone() == (
            (0,) if fail_at_end else (1,)
        )
        # Existing table/column definitions, constraints, RLS flags and table ACLs stay exact.
        for name in ("columns", "tables", "constraints"):
            assert after[name] == before[name]
        old_acl = {row[0]: row[1:] for row in before["function_acl"]}
        new_acl = {row[0]: row[1:] for row in after["function_acl"]}
        assert {name: new_acl[name] for name in old_acl} == old_acl
        assert set(new_acl) - set(old_acl) == (set() if fail_at_end else {ARTIFACT_FUNCTION})
        assert set(new_functions) - set(old_functions) == (set() if fail_at_end else {ARTIFACT_FUNCTION})
        for signature, definition in old_functions.items():
            if fail_at_end or signature not in CHANGED_FUNCTIONS:
                assert new_functions[signature] == definition
        if fail_at_end:
            assert after["policies"] == before["policies"]
        else:
            before_policies = {(row[0], row[1]): row for row in before["policies"]}
            after_policies = {(row[0], row[1]): row for row in after["policies"]}
            assert {key: after_policies[key] for key in before_policies} == before_policies
            added = set(after_policies) - set(before_policies)
            assert len(added) == 3
            assert {key[0] for key in added} == {"model_registry", "model_evaluation", "object_version"}
            for table, name in added:
                policy = connection.execute(
                    "SELECT p.polroles,p.polcmd,p.polpermissive,pg_get_expr(p.polqual,p.polrelid),"
                    "pg_get_expr(p.polwithcheck,p.polrelid) FROM pg_policy p JOIN pg_class c ON c.oid=p.polrelid "
                    "WHERE c.relnamespace='mt'::regnamespace AND c.relname=%s AND p.polname=%s",
                    (table, name),
                ).fetchone()
                assert policy == ([migration_owner], "r", True, "true", None)
            # The new data-bearing function keeps a fixed owner/search path and no PUBLIC execution.
            artifact = connection.execute(
                "SELECT proowner,prosecdef,provolatile,proconfig FROM pg_proc WHERE oid=%s::regprocedure",
                (ARTIFACT_FUNCTION,),
            ).fetchone()
            assert artifact is not None
            assert artifact[0:3] == (migration_owner, True, "v")
            assert artifact[3] == ["search_path=pg_catalog, mt"]
            assert connection.execute(
                "SELECT has_function_privilege('mt_runtime',%s,'EXECUTE')", (ARTIFACT_FUNCTION,)
            ).fetchone() == (True,)
            assert connection.execute(
                "SELECT count(*) FROM pg_proc p CROSS JOIN LATERAL "
                "aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) a "
                "WHERE p.oid=%s::regprocedure AND a.grantee=0 AND a.privilege_type='EXECUTE'",
                (ARTIFACT_FUNCTION,),
            ).fetchone() == (0,)
            assert connection.execute(
                "SELECT count(*) FROM pg_proc p CROSS JOIN LATERAL "
                "aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) a "
                "WHERE p.oid=%s::regprocedure AND a.grantee<>p.proowner "
                "AND a.grantee<>(SELECT oid FROM pg_roles WHERE rolname='mt_runtime')",
                (ARTIFACT_FUNCTION,),
            ).fetchone() == (0,)
        # Exercise the registry matrix, including any unexpected literals added by the migration.
        observed = operation_literals(new_functions["mt.scope_operation()"])
        for name in operations | observed:
            previous_value = old_operation_values.get(name)
            expected = name if not fail_at_end and name in NEW_OPERATIONS else previous_value
            assert operation_value(connection, name) == expected
        for pair, allowed in old_pairs.items():
            expected = True if not fail_at_end and pair in NEW_KIND_PAIRS else allowed
            assert connection.execute("SELECT mt.scope_lookup_kind_allowed(%s,%s)", pair).fetchone() == (expected,)
        assert connection.execute("SELECT mt.scope_lookup_kind_allowed(NULL,NULL)").fetchone() == (False,)
