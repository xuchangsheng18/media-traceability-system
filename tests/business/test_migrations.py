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


def scalar(connection, query):
    row = connection.execute(query).fetchone()
    assert row is not None
    return row[0]


def test_empty_database_migrates_and_replay_noops(database_dsn):
    assert migrate(database_dsn) == ["0001", "0002", "0003", "0004", "0005"]
    assert migrate(database_dsn) == []
    with psycopg.connect(database_dsn) as connection:
        assert (
            scalar(
                connection,
                "SELECT count(*) FROM information_schema.tables WHERE table_schema='mt' AND table_type='BASE TABLE'",
            )
            == 63
        )
        assert scalar(connection, "SELECT count(*) FROM information_schema.columns WHERE table_schema='mt'") == 843
        assert scalar(connection, "SELECT rolbypassrls OR rolsuper FROM pg_roles WHERE rolname='mt_runtime'") is False


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
        assert scalar(connection, "SELECT to_regnamespace('mt')") is None
        assert scalar(connection, "SELECT to_regclass('mt_meta.schema_migrations')") is None


@pytest.mark.parametrize("cross_unit", [False, True])
def test_identity_upgrade_preserves_legacy_rows_or_rejects_cross_unit_members(database_dsn, tmp_path, cross_unit):
    from uuid import uuid4

    for original in sorted(MIGRATIONS.glob("*.sql"))[:3]:
        (tmp_path / original.name).write_bytes(original.read_bytes())
    assert migrate(database_dsn, tmp_path) == ["0001", "0002", "0003"]
    org, other_org, user, case, membership = [uuid4() for _ in range(5)]
    with psycopg.connect(database_dsn) as connection:
        connection.execute(
            "INSERT INTO mt.organizations(org_id,name) VALUES(%s,'legacy-unit'),(%s,'other-unit')", (org, other_org)
        )
        connection.execute(
            "INSERT INTO mt.users(user_id,org_id,subject,enabled) VALUES(%s,%s,'legacy-internal-label',true)",
            (user, org),
        )
        connection.execute(
            "INSERT INTO mt.cases(case_id,org_id,display_code,status) VALUES(%s,%s,'legacy-case','ACTIVE')",
            (case, other_org if cross_unit else org),
        )
        connection.execute(
            "INSERT INTO mt.case_membership(membership_id,case_id,org_id,user_id) VALUES(%s,%s,%s,%s)",
            (membership, case, other_org if cross_unit else org, user),
        )
    if cross_unit:
        with pytest.raises(psycopg.errors.ForeignKeyViolation):
            migrate(database_dsn)
        with psycopg.connect(database_dsn) as connection:
            assert scalar(connection, "SELECT count(*) FROM mt_meta.schema_migrations") == 3
            assert scalar(connection, "SELECT to_regclass('mt.user_identities')") is None
            assert scalar(connection, "SELECT count(*) FROM mt.case_membership") == 1
    else:
        assert migrate(database_dsn) == ["0004", "0005"]
        assert migrate(database_dsn) == []
        with psycopg.connect(database_dsn) as connection:
            assert connection.execute(
                "SELECT org_id,subject,enabled FROM mt.users WHERE user_id=%s", (user,)
            ).fetchone() == (org, "legacy-internal-label", True)
            assert scalar(connection, "SELECT count(*) FROM mt.user_identities") == 0
            assert scalar(connection, "SELECT count(*) FROM mt.case_membership") == 1


def test_identity_lookup_works_when_migration_owner_cannot_bypass_rls(database_dsn):
    from uuid import uuid4

    from psycopg import sql
    from psycopg.conninfo import conninfo_to_dict, make_conninfo

    role = "mt_schema_owner_" + uuid4().hex
    settings = conninfo_to_dict(database_dsn)
    with psycopg.connect(database_dsn) as admin:
        admin.execute(sql.SQL("CREATE ROLE {} NOLOGIN NOSUPERUSER NOBYPASSRLS CREATEROLE").format(sql.Identifier(role)))
        admin.execute(
            sql.SQL("GRANT CREATE ON DATABASE {} TO {}").format(
                sql.Identifier(str(settings["dbname"])), sql.Identifier(role)
            )
        )
    try:
        assert migrate(make_conninfo(database_dsn, options="-crole=" + role)) == [
            "0001",
            "0002",
            "0003",
            "0004",
            "0005",
        ]
        org, user = uuid4(), uuid4()
        with psycopg.connect(database_dsn) as admin:
            admin.execute("INSERT INTO mt.organizations(org_id,name) VALUES(%s,'owner-test')", (org,))
            admin.execute(
                "INSERT INTO mt.users(user_id,org_id,subject,enabled) VALUES(%s,%s,%s,true)", (user, org, str(user))
            )
            admin.execute(
                "INSERT INTO mt.user_identities(identity_id,user_id,org_id,issuer,subject,enabled,mapping_version) VALUES(%s,%s,%s,'owner-provider','owner-subject',true,'v1')",
                (uuid4(), user, org),
            )
            row = admin.execute("SELECT user_id FROM mt.resolve_identity('owner-provider','owner-subject')").fetchone()
            assert row == (user,)
    finally:
        with psycopg.connect(database_dsn) as admin:
            admin.execute(sql.SQL("REASSIGN OWNED BY {} TO CURRENT_USER").format(sql.Identifier(role)))
            admin.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
            admin.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))


@pytest.mark.parametrize(
    "collision", ["runtime_manager", "runtime_lookup", "lookup_manager", "indirect_runtime_manager"]
)
def test_unsafe_identity_role_inheritance_aborts_migration(database_dsn, collision):
    from uuid import uuid4

    from psycopg import sql

    middle = "mt_collision_" + uuid4().hex
    grants = {
        "runtime_manager": [("mt_directory_manager", "mt_runtime")],
        "runtime_lookup": [("mt_identity_lookup", "mt_runtime")],
        "lookup_manager": [("mt_directory_manager", "mt_identity_lookup")],
        "indirect_runtime_manager": [("mt_directory_manager", middle), (middle, "mt_runtime")],
    }[collision]
    # These group roles already exist in the dedicated isolated test instance.
    with psycopg.connect(database_dsn) as admin:
        assert not scalar(
            admin,
            "SELECT pg_has_role('mt_runtime','mt_directory_manager','MEMBER') OR pg_has_role('mt_runtime','mt_identity_lookup','MEMBER') OR pg_has_role('mt_identity_lookup','mt_directory_manager','MEMBER')",
        )
        if collision.startswith("indirect"):
            admin.execute(sql.SQL("CREATE ROLE {} NOLOGIN").format(sql.Identifier(middle)))
        for granted, member in grants:
            admin.execute(sql.SQL("GRANT {} TO {}").format(sql.Identifier(granted), sql.Identifier(member)))
    try:
        with pytest.raises(psycopg.Error, match="UNSAFE_IDENTITY_ROLE_INHERITANCE"):
            migrate(database_dsn)
        with psycopg.connect(database_dsn) as admin:
            assert scalar(admin, "SELECT to_regnamespace('mt')") is None
    finally:
        with psycopg.connect(database_dsn) as admin:
            for granted, member in reversed(grants):
                admin.execute(sql.SQL("REVOKE {} FROM {}").format(sql.Identifier(granted), sql.Identifier(member)))
            if collision.startswith("indirect"):
                admin.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(middle)))


@pytest.mark.parametrize("invalid_legacy", [False, True])
def test_role_catalog_upgrade_preserves_legacy_or_rolls_back_atomically(database_dsn, tmp_path, invalid_legacy):
    from uuid import uuid4

    for original in sorted(MIGRATIONS.glob("*.sql"))[:4]:
        (tmp_path / original.name).write_bytes(original.read_bytes())
    assert migrate(database_dsn, tmp_path) == ["0001", "0002", "0003", "0004"]
    role, permission, relation = [uuid4() for _ in range(3)]
    with psycopg.connect(database_dsn) as connection:
        connection.execute(
            "INSERT INTO mt.roles(role_id,code,description) VALUES(%s,%s,'legacy')",
            (role, " bad legacy" if invalid_legacy else "legacy.role"),
        )
        connection.execute(
            "INSERT INTO mt.permissions(permission_id,code,description) VALUES(%s,'legacy.permission','legacy')",
            (permission,),
        )
        connection.execute(
            "INSERT INTO mt.role_permissions(role_permission_id,role_id,permission_id) VALUES(%s,%s,%s)",
            (relation, role, permission),
        )
    if invalid_legacy:
        with pytest.raises(psycopg.errors.CheckViolation):
            migrate(database_dsn)
        with psycopg.connect(database_dsn) as connection:
            assert scalar(connection, "SELECT count(*) FROM mt_meta.schema_migrations") == 4
            assert (
                scalar(
                    connection,
                    "SELECT count(*) FROM information_schema.columns WHERE table_schema='mt' AND table_name='roles' AND column_name='enabled'",
                )
                == 0
            )
            assert connection.execute("SELECT code FROM mt.roles WHERE role_id=%s", (role,)).fetchone() == (
                " bad legacy",
            )
    else:
        assert migrate(database_dsn) == ["0005"]
        assert migrate(database_dsn) == []
        with psycopg.connect(database_dsn) as connection:
            assert connection.execute(
                "SELECT enabled,code,row_version FROM mt.roles WHERE role_id=%s", (role,)
            ).fetchone() == (True, "legacy.role", 1)
            assert connection.execute(
                "SELECT enabled,code,row_version FROM mt.permissions WHERE permission_id=%s", (permission,)
            ).fetchone() == (True, "legacy.permission", 1)
            assert connection.execute(
                "SELECT role_id,permission_id,revoked_at,row_version FROM mt.role_permissions WHERE role_permission_id=%s",
                (relation,),
            ).fetchone() == (role, permission, None, 1)
            new_role = uuid4()
            connection.execute(
                "INSERT INTO mt.roles(role_id,code,description) VALUES(%s,'new.role','new')", (new_role,)
            )
            assert connection.execute("SELECT enabled FROM mt.roles WHERE role_id=%s", (new_role,)).fetchone() == (
                False,
            )


def test_new_catalog_migration_rechecks_unsafe_existing_role_inheritance(database_dsn, tmp_path):
    for original in sorted(MIGRATIONS.glob("*.sql"))[:4]:
        (tmp_path / original.name).write_bytes(original.read_bytes())
    assert migrate(database_dsn, tmp_path) == ["0001", "0002", "0003", "0004"]
    with psycopg.connect(database_dsn) as admin:
        admin.execute("GRANT mt_directory_manager TO mt_runtime")
    try:
        with pytest.raises(psycopg.errors.ObjectNotInPrerequisiteState, match="UNSAFE_ROLE_CATALOG_MANAGEMENT"):
            migrate(database_dsn)
        with psycopg.connect(database_dsn) as connection:
            assert scalar(connection, "SELECT count(*) FROM mt_meta.schema_migrations") == 4
            assert (
                scalar(
                    connection,
                    "SELECT count(*) FROM information_schema.columns WHERE table_schema='mt' AND table_name='permissions' AND column_name='enabled'",
                )
                == 0
            )
    finally:
        with psycopg.connect(database_dsn) as admin:
            admin.execute("REVOKE mt_directory_manager FROM mt_runtime")
