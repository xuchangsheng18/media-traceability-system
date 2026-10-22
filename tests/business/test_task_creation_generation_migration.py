"""Append-only generation JSON repair; only random isolated databases are used."""

import hashlib
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from tests.business.test_migrations import MIGRATIONS, migrate
from tests.business.test_task_creation_migration import legacy_rows

UPGRADE = "0018_task_creation_generation_json.sql"
ORIGINAL_0017_SHA256 = "b8a5401f43895a7cd9d84ffdf434356be95d4499875c6ef7cf61bafe1616dd98"
PRIVATE_ROLES = ("mt_task_plan_case_reader", "mt_task_plan_lookup")
FUNCTIONS = {
    "task_create_execution_plan": "mt.task_create_execution_plan(uuid,uuid,text,text,text[],text,uuid,text,text,text)",
    "task_create_plan_metadata": "mt.task_create_plan_metadata(uuid,uuid,text,text,text[],text)",
}
OLD_EXPRESSION = "'database_oid',v_generation.database_oid,'epoch'"
NEW_EXPRESSION = "'database_oid',v_generation.database_oid::bigint,'epoch'"


def prefix(directory: Path, through: int):
    directory.mkdir()
    files = [path for path in sorted(MIGRATIONS.glob("*.sql")) if path.name[:4] <= f"{through:04d}"]
    assert [path.name[:4] for path in files] == [f"{value:04d}" for value in range(1, through + 1)]
    for path in files:
        (directory / path.name).write_bytes(path.read_bytes())
    return files


def add_upgrade(directory):
    path = MIGRATIONS / UPGRADE
    assert path.is_file(), "The append-only generation JSON repair migration must exist"
    (directory / path.name).write_bytes(path.read_bytes())


def functions(connection):
    rows = connection.execute(
        "SELECT p.oid,p.proname,to_jsonb(p)-'prosrc',p.prosrc,obj_description(p.oid,'pg_proc') "
        "FROM pg_proc p WHERE p.pronamespace='mt'::regnamespace ORDER BY p.oid"
    ).fetchall()
    return {row[0]: (row[1], row[2], row[3], row[4]) for row in rows}


def catalogue(connection):
    return {
        "schema": connection.execute(
            "SELECT nspname,nspowner,nspacl FROM pg_namespace WHERE nspname IN ('mt','mt_meta') ORDER BY nspname"
        ).fetchall(),
        "relations": connection.execute(
            "SELECT oid,relname,relkind,relowner,relacl,relrowsecurity,relforcerowsecurity "
            "FROM pg_class WHERE relnamespace='mt'::regnamespace ORDER BY oid"
        ).fetchall(),
        "policies": connection.execute(
            "SELECT to_jsonb(p) FROM pg_policy p JOIN pg_class c ON c.oid=p.polrelid "
            "WHERE c.relnamespace='mt'::regnamespace ORDER BY p.oid"
        ).fetchall(),
        "triggers": connection.execute(
            "SELECT to_jsonb(t) FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid "
            "WHERE c.relnamespace='mt'::regnamespace ORDER BY t.oid"
        ).fetchall(),
        "roles": connection.execute(
            "SELECT to_jsonb(r) FROM pg_roles r WHERE rolname=ANY(%s) ORDER BY rolname", (list(PRIVATE_ROLES),)
        ).fetchall(),
        "memberships": connection.execute(
            "SELECT to_jsonb(m) FROM pg_auth_members m WHERE roleid IN "
            "(SELECT oid FROM pg_roles WHERE rolname=ANY(%s)) OR member IN "
            "(SELECT oid FROM pg_roles WHERE rolname=ANY(%s)) ORDER BY roleid,member,grantor",
            (list(PRIVATE_ROLES), list(PRIVATE_ROLES)),
        ).fetchall(),
    }


def ledger(connection):
    return connection.execute("SELECT * FROM mt_meta.schema_migrations ORDER BY version").fetchall()


def table_rows(connection):
    tables = connection.execute(
        "SELECT relname FROM pg_class WHERE relnamespace='mt'::regnamespace AND relkind='r' ORDER BY relname"
    ).fetchall()
    return {
        row[0]: connection.execute(
            sql.SQL("SELECT to_jsonb(t) FROM mt.{} t ORDER BY to_jsonb(t)::text").format(sql.Identifier(row[0]))
        ).fetchall()
        for row in tables
    }


def assert_only_oid_json_changed(before, after):
    assert before.keys() == after.keys()
    changed_names = []
    for oid, old in before.items():
        current = after[oid]
        assert current[0:2] == old[0:2], "All function metadata, owner, ACL and search_path must remain unchanged"
        assert current[3] == old[3], "Function comments must remain unchanged"
        if old[0] in FUNCTIONS:
            changed_names.append(old[0])
            assert old[2].count(OLD_EXPRESSION) == 1
            assert NEW_EXPRESSION not in old[2]
            assert current[2] == old[2].replace(OLD_EXPRESSION, NEW_EXPRESSION)
        else:
            assert current[2] == old[2]
    assert sorted(changed_names) == sorted(FUNCTIONS)


@pytest.fixture
def through_0017(database_dsn, tmp_path):
    directory = tmp_path / "through_0017"
    originals = prefix(directory, 17)
    assert hashlib.sha256(originals[-1].read_bytes()).hexdigest() == ORIGINAL_0017_SHA256
    assert migrate(database_dsn, directory) == [f"{value:04d}" for value in range(1, 18)]
    return database_dsn, directory, originals


def test_0018_upgrade_changes_only_two_json_arguments_and_replay_noops(through_0017):
    dsn, directory, originals = through_0017
    with psycopg.connect(dsn) as connection:
        legacy_rows(connection)
        before_functions = functions(connection)
        before_catalogue = catalogue(connection)
        before_rows = table_rows(connection)
        before_ledger = ledger(connection)
    assert [(row[0], row[1]) for row in before_ledger] == [
        (path.name[:4], hashlib.sha256(path.read_bytes()).hexdigest()) for path in originals
    ]
    add_upgrade(directory)
    assert migrate(dsn, directory) == ["0018"]
    with psycopg.connect(dsn) as connection:
        assert_only_oid_json_changed(before_functions, functions(connection))
        assert catalogue(connection) == before_catalogue
        assert table_rows(connection) == before_rows
        after_ledger = ledger(connection)
        assert after_ledger[:-1] == before_ledger
        assert after_ledger[-1][0:2] == ("0018", hashlib.sha256((MIGRATIONS / UPGRADE).read_bytes()).hexdigest())
    assert migrate(dsn, directory) == []
    with psycopg.connect(dsn) as connection:
        assert ledger(connection) == after_ledger
        assert_only_oid_json_changed(before_functions, functions(connection))
        assert catalogue(connection) == before_catalogue
        assert table_rows(connection) == before_rows


def test_0018_preserves_legally_absent_comments_on_both_functions(through_0017):
    dsn, directory, _ = through_0017
    with psycopg.connect(dsn) as connection:
        for signature in FUNCTIONS.values():
            connection.execute(sql.SQL("COMMENT ON FUNCTION {} IS NULL").format(sql.SQL(signature)))
        before_functions = functions(connection)
        assert all(value[3] is None for value in before_functions.values() if value[0] in FUNCTIONS)
        before_catalogue = catalogue(connection)
        before_ledger = ledger(connection)
    add_upgrade(directory)
    assert migrate(dsn, directory) == ["0018"]
    assert migrate(dsn, directory) == []
    with psycopg.connect(dsn) as connection:
        assert_only_oid_json_changed(before_functions, functions(connection))
        assert catalogue(connection) == before_catalogue
        assert ledger(connection)[:-1] == before_ledger


def installation_memberships(admin, installer, *, grant):
    if grant:
        admin.execute(
            sql.SQL(
                "GRANT mt_task_plan_lookup,mt_task_plan_case_reader TO {} WITH INHERIT FALSE, SET TRUE, ADMIN FALSE"
            ).format(sql.Identifier(installer))
        )
        assert admin.execute(
            "SELECT r.rolname,m.inherit_option,m.set_option,m.admin_option "
            "FROM pg_auth_members m JOIN pg_roles r ON r.oid=m.roleid "
            "WHERE m.member=%s::regrole AND r.rolname=ANY(%s) ORDER BY r.rolname",
            (installer, list(PRIVATE_ROLES)),
        ).fetchall() == [(role, False, True, False) for role in PRIVATE_ROLES]
    else:
        admin.execute(
            sql.SQL("REVOKE mt_task_plan_lookup,mt_task_plan_case_reader FROM {}").format(sql.Identifier(installer))
        )
        assert admin.execute(
            "SELECT count(*) FROM pg_auth_members WHERE member=%s::regrole AND roleid IN "
            "(SELECT oid FROM pg_roles WHERE rolname=ANY(%s))",
            (installer, list(PRIVATE_ROLES)),
        ).fetchone() == (0,)


def test_0018_non_super_schema_owner_requires_temporary_set_only_installation(database_dsn, tmp_path):
    installer = "mt_generation_installer_" + uuid4().hex
    name = conninfo_to_dict(database_dsn)["dbname"]
    assert type(name) is str
    directory = tmp_path / "non_super_prefix"
    prefix(directory, 16)
    with psycopg.connect(database_dsn, autocommit=True) as admin:
        admin.execute(
            sql.SQL(
                "CREATE ROLE {} NOLOGIN NOINHERIT NOSUPERUSER NOBYPASSRLS NOCREATEROLE NOCREATEDB NOREPLICATION"
            ).format(sql.Identifier(installer))
        )
        admin.execute(
            sql.SQL("GRANT CREATE ON DATABASE {} TO {}").format(sql.Identifier(name), sql.Identifier(installer))
        )
    owner_dsn = make_conninfo(database_dsn, options="-crole=" + installer)
    try:
        assert migrate(owner_dsn, directory) == [f"{value:04d}" for value in range(1, 17)]
        (directory / "0017_task_creation_scope_reads.sql").write_bytes(
            (MIGRATIONS / "0017_task_creation_scope_reads.sql").read_bytes()
        )
        with psycopg.connect(database_dsn, autocommit=True) as admin:
            installation_memberships(admin, installer, grant=True)
        try:
            assert migrate(owner_dsn, directory) == ["0017"]
        finally:
            with psycopg.connect(database_dsn, autocommit=True) as admin:
                installation_memberships(admin, installer, grant=False)
        with psycopg.connect(database_dsn) as admin:
            assert admin.execute(
                "SELECT rolsuper,rolbypassrls,rolcreaterole,rolcreatedb,rolinherit FROM pg_roles WHERE rolname=%s",
                (installer,),
            ).fetchone() == (False, False, False, False, False)
            before_functions = functions(admin)
            before_catalogue = catalogue(admin)
            before_ledger = ledger(admin)
        add_upgrade(directory)
        with pytest.raises(psycopg.errors.ObjectNotInPrerequisiteState):
            migrate(owner_dsn, directory)
        with psycopg.connect(database_dsn) as admin:
            assert functions(admin) == before_functions
            assert catalogue(admin) == before_catalogue
            assert ledger(admin) == before_ledger
        with psycopg.connect(database_dsn, autocommit=True) as admin:
            installation_memberships(admin, installer, grant=True)
        try:
            assert migrate(owner_dsn, directory) == ["0018"]
        finally:
            with psycopg.connect(database_dsn, autocommit=True) as admin:
                installation_memberships(admin, installer, grant=False)
        with psycopg.connect(database_dsn) as admin:
            assert_only_oid_json_changed(before_functions, functions(admin))
            assert catalogue(admin) == before_catalogue
            assert ledger(admin)[:-1] == before_ledger
        assert migrate(owner_dsn, directory) == []
    finally:
        with psycopg.connect(database_dsn, autocommit=True) as admin:
            installation_memberships(admin, installer, grant=False)
            admin.execute(sql.SQL("REASSIGN OWNED BY {} TO CURRENT_USER").format(sql.Identifier(installer)))
            admin.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(installer)))
            admin.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(installer)))
            assert admin.execute("SELECT count(*) FROM pg_roles WHERE rolname=%s", (installer,)).fetchone() == (0,)


@pytest.mark.parametrize("function", sorted(FUNCTIONS))
@pytest.mark.parametrize("tamper", ["body", "owner"])
def test_0018_refuses_unexpected_original_function_without_partial_ddl(through_0017, function, tamper):
    dsn, directory, _ = through_0017
    with psycopg.connect(dsn) as connection:
        if tamper == "body":
            definition = connection.execute(
                "SELECT pg_get_functiondef(%s::regprocedure)", (FUNCTIONS[function],)
            ).fetchone()
            assert definition is not None
            changed = definition[0].replace("\nBEGIN\n", "\nBEGIN\n -- self-owned tamper fixture\n", 1)
            assert changed != definition[0]
            connection.execute(changed)
        else:
            connection.execute(sql.SQL("ALTER FUNCTION {} OWNER TO CURRENT_USER").format(sql.SQL(FUNCTIONS[function])))
        before_functions = functions(connection)
        before_catalogue = catalogue(connection)
        before_ledger = ledger(connection)
    add_upgrade(directory)
    with pytest.raises(psycopg.errors.ObjectNotInPrerequisiteState):
        migrate(dsn, directory)
    with psycopg.connect(dsn) as connection:
        assert functions(connection) == before_functions
        assert catalogue(connection) == before_catalogue
        assert ledger(connection) == before_ledger
        assert connection.execute("SELECT count(*) FROM mt_meta.schema_migrations WHERE version='0018'").fetchone() == (
            0,
        )


@pytest.mark.parametrize("oid", [2_147_483_647, 2_147_483_648, 4_294_967_295])
def test_oid_bigint_json_conversion_keeps_high_unsigned_oid_values(database_dsn, oid):
    # This demonstrates the exact cast expression without changing a real
    # database's OID or treating a synthetic epoch as recovery authority.
    with psycopg.connect(database_dsn) as connection:
        row = connection.execute(
            "SELECT jsonb_build_object('database_oid',(%s::bigint::oid)::bigint),"
            "jsonb_typeof(jsonb_build_object('database_oid',(%s::bigint::oid)::bigint)->'database_oid')",
            (oid, oid),
        ).fetchone()
    assert row is not None
    assert type(row[0]["database_oid"]) is int
    assert row[0]["database_oid"] == oid
    assert row[1] == "number"
