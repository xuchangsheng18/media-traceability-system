"""T012 catalog and binding invariants on real isolated PostgreSQL, no formal grants."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import psycopg
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from tests.business.test_identity_directory import directory as directory


def catalog(directory, *, enabled=True, expires_at=None):
    d, ctx = directory
    assert callable(getattr(d, "create_role", None)), "T012 role and permission management is missing"
    code = "fixture.permission." + uuid4().hex
    role = d.create_role("fixture.role." + uuid4().hex, "self-owned fixture", enabled=enabled)
    permission = d.create_permission(code, "self-owned fixture", enabled=enabled)
    relation = d.bind_permission(role, permission)
    binding = d.bind_role(ctx["actor"].user_id, role, expires_at=expires_at)
    return d, ctx, role, permission, relation, binding, code


def test_new_catalog_entries_default_disabled_and_preserve_rows(directory):
    d, ctx = directory
    assert callable(getattr(d, "create_role", None)), "T012 role and permission management is missing"
    role = d.create_role("fixture.role", "self-owned fixture")
    permission = d.create_permission("fixture.permission", "self-owned fixture")
    d.bind_permission(role, permission)
    d.bind_role(ctx["actor"].user_id, role)
    assert d.permission_bindings(ctx["actor"].user_id) == ()
    for table, key, identifier in [("roles", "role_id", role), ("permissions", "permission_id", permission)]:
        row = d.connection.execute(
            text(f"SELECT enabled,row_version FROM mt.{table} WHERE {key}=:id"), {"id": identifier}
        ).one()
        assert row == (False, 1)


@pytest.mark.parametrize(
    "state",
    [
        "disabled_role",
        "disabled_permission",
        "revoked_role",
        "revoked_permission",
        "expired_role",
        "disabled_user",
        "disabled_org",
    ],
)
def test_inactive_catalog_or_binding_is_excluded_without_erasing_history(directory, state):
    d, ctx, role, permission, relation, binding, code = catalog(directory)
    assert d.permission_bindings(ctx["actor"].user_id) == (code,)
    if state == "disabled_role":
        d.disable_role(role, expected_version=1)
    elif state == "disabled_permission":
        d.disable_permission(permission, expected_version=1)
    elif state == "revoked_role":
        d.revoke_role(binding, expected_version=1)
    elif state == "revoked_permission":
        d.revoke_permission(relation, expected_version=1)
    elif state == "expired_role":
        d.connection.execute(
            text("UPDATE mt.user_roles SET expires_at=statement_timestamp() WHERE user_role_id=:id"), {"id": binding}
        )
    elif state == "disabled_user":
        d.disable_user(ctx["actor"].user_id, expected_version=1)
    else:
        d.disable_organization(ctx["actor"].org_id, expected_version=1)
    assert d.permission_bindings(ctx["actor"].user_id) == ()
    assert (
        d.connection.execute(
            text("SELECT count(*) FROM mt.user_roles WHERE user_role_id=:id"), {"id": binding}
        ).scalar_one()
        == 1
    )
    assert (
        d.connection.execute(
            text("SELECT count(*) FROM mt.role_permissions WHERE role_permission_id=:id"), {"id": relation}
        ).scalar_one()
        == 1
    )


@pytest.mark.parametrize(
    "duplicate",
    ["role_code", "permission_code", "user_role", "role_permission", "revoked_user_role", "revoked_role_permission"],
)
def test_unique_codes_and_binding_history_remain_reserved(directory, duplicate):
    from business_app.errors import BusinessError

    d, ctx, role, permission, relation, binding, code = catalog(directory)
    if duplicate == "revoked_user_role":
        d.revoke_role(binding, expected_version=1)
    if duplicate == "revoked_role_permission":
        d.revoke_permission(relation, expected_version=1)
    role_code = d.connection.execute(text("SELECT code FROM mt.roles WHERE role_id=:id"), {"id": role}).scalar_one()
    actions = {
        "role_code": lambda: d.create_role(role_code, "duplicate"),
        "permission_code": lambda: d.create_permission(code, "duplicate"),
        "user_role": lambda: d.bind_role(ctx["actor"].user_id, role),
        "role_permission": lambda: d.bind_permission(role, permission),
        "revoked_user_role": lambda: d.bind_role(ctx["actor"].user_id, role),
        "revoked_role_permission": lambda: d.bind_permission(role, permission),
    }
    with pytest.raises(BusinessError, match="DIRECTORY_CONFLICT"):
        actions[duplicate]()
    assert d.connection.execute(text("SELECT count(*) FROM mt.roles WHERE role_id=:id"), {"id": role}).scalar_one() == 1


@pytest.mark.parametrize("target", ["missing_user", "missing_role", "missing_permission"])
def test_binding_foreign_keys_reject_missing_parents(directory, target):
    from business_app.errors import BusinessError

    d, ctx, role, permission, *_ = catalog(directory)
    with pytest.raises(BusinessError, match="DIRECTORY_RELATION_INVALID"):
        if target == "missing_user":
            d.bind_role(uuid4(), role)
        elif target == "missing_role":
            d.bind_permission(uuid4(), permission)
        else:
            d.bind_permission(role, uuid4())


@pytest.mark.parametrize(
    "target",
    [
        "role_key",
        "role_code",
        "permission_key",
        "permission_code",
        "relation_key",
        "relation_parent",
        "terminal_relation",
    ],
)
def test_database_rejects_stable_key_changes_and_revocation_reversal(directory, target):
    d, ctx, role, permission, relation, binding, code = catalog(directory)
    queries = {
        "role_key": ("UPDATE mt.roles SET role_id=:replacement WHERE role_id=:id", role),
        "role_code": ("UPDATE mt.roles SET code='changed-code' WHERE role_id=:id", role),
        "permission_key": ("UPDATE mt.permissions SET permission_id=:replacement WHERE permission_id=:id", permission),
        "permission_code": ("UPDATE mt.permissions SET code='changed-code' WHERE permission_id=:id", permission),
        "relation_key": (
            "UPDATE mt.role_permissions SET role_permission_id=:replacement WHERE role_permission_id=:id",
            relation,
        ),
        "relation_parent": (
            "UPDATE mt.role_permissions SET permission_id=:replacement WHERE role_permission_id=:id",
            relation,
        ),
        "terminal_relation": ("UPDATE mt.role_permissions SET revoked_at=NULL WHERE role_permission_id=:id", relation),
    }
    if target == "terminal_relation":
        d.revoke_permission(relation, expected_version=1)
    query, identifier = queries[target]
    with pytest.raises(DBAPIError) as failure:
        with d.connection.begin_nested():
            d.connection.execute(text(query), {"id": identifier, "replacement": uuid4()})
    assert getattr(failure.value.orig, "sqlstate", None) == "55000"


@pytest.mark.parametrize("table", ["roles", "permissions", "role_permissions", "user_roles"])
@pytest.mark.parametrize("operation", ["DELETE FROM", "TRUNCATE"])
def test_database_owner_cannot_ordinary_delete_or_truncate_catalog_history(directory, table, operation):
    d, ctx = directory
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        with pytest.raises(psycopg.errors.ObjectNotInPrerequisiteState):
            with admin.transaction():
                admin.execute(f"{operation} mt.{table}" + (" CASCADE" if operation == "TRUNCATE" else ""))


@pytest.mark.parametrize("role", ["mt_runtime", "mt_identity_lookup"])
def test_runtime_and_lookup_cannot_manage_catalog_or_read_manager_projection(directory, role):
    from business_app.errors import BusinessError

    d, ctx, catalog_role, *_ = catalog(directory)
    if role == "mt_runtime":
        connection_context = ctx["database"].engine.begin()
    else:
        connection_context = d.connection.begin_nested()
    with connection_context as selected:
        connection = selected if role == "mt_runtime" else d.connection
        if role == "mt_identity_lookup":
            connection.execute(text("SET LOCAL ROLE mt_identity_lookup"))
        denied = type(d)(connection)
        with pytest.raises(BusinessError, match="DIRECTORY_MANAGEMENT_FORBIDDEN"):
            denied.create_permission("forbidden", "denied")
        with pytest.raises(BusinessError, match="DIRECTORY_MANAGEMENT_FORBIDDEN"):
            denied.permission_bindings(ctx["actor"].user_id)
        with pytest.raises(DBAPIError) as failure:
            with connection.begin_nested():
                connection.execute(
                    text("INSERT INTO mt.permissions(permission_id,code,description) VALUES(:id,'forbidden','denied')"),
                    {"id": uuid4()},
                )
        assert getattr(failure.value.orig, "sqlstate", None) == "42501"


def test_role_disable_compare_and_swap_allows_exactly_one_concurrent_writer(directory):
    from business_app.errors import BusinessError

    d, ctx = directory
    assert callable(getattr(d, "disable_role", None)), "T012 role soft disable is missing"
    role = uuid4()
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            "INSERT INTO mt.roles(role_id,code,description,enabled) VALUES(%s,%s,'fixture',true)", (role, str(role))
        )

    def disable(_):
        try:
            with d.connection.engine.begin() as connection:
                type(d)(connection).disable_role(role, expected_version=1)
            return "changed"
        except BusinessError as error:
            return str(error)

    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(disable, range(2))) == ["DIRECTORY_VERSION_CONFLICT", "changed"]
    assert d.connection.execute(
        text("SELECT enabled,row_version FROM mt.roles WHERE role_id=:id"), {"id": role}
    ).one() == (False, 2)


def test_role_binding_expiry_is_rechecked_in_a_long_transaction(directory):
    d, ctx, *_, code = catalog(directory, expires_at=datetime.now(timezone.utc) + timedelta(seconds=0.4))
    assert d.permission_bindings(ctx["actor"].user_id) == (code,)
    d.connection.execute(text("SELECT pg_sleep(0.6)"))
    assert d.permission_bindings(ctx["actor"].user_id) == ()


def test_role_catalog_and_binding_backup_restore_preserves_states_and_ledger(directory, tmp_path):
    from psycopg import sql
    from psycopg.conninfo import make_conninfo
    from sqlalchemy import create_engine

    from tests.business.test_recovery import pg_tool

    d, ctx, role, permission, relation, binding, code = catalog(directory)
    d.revoke_permission(relation, expected_version=1)
    d.disable_permission(permission, expected_version=1)
    d.connection.commit()
    name = "mt_business_catalog_restore_" + uuid4().hex
    target_dsn = make_conninfo(ctx["admin_dsn"], dbname=name)
    dump = tmp_path / "catalog.dump"
    pg_tool("pg_dump", ctx["admin_dsn"], "-Fc", "--no-owner", "--file", str(dump))
    engine = None
    with psycopg.connect(ctx["admin_dsn"], autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {} TEMPLATE template0").format(sql.Identifier(name)))
        try:
            pg_tool("pg_restore", target_dsn, "--no-owner", "--exit-on-error", str(dump))
            with psycopg.connect(ctx["admin_dsn"]) as source, psycopg.connect(target_dsn) as target:
                for table, order in [
                    ("organizations", "org_id"),
                    ("users", "user_id"),
                    ("roles", "role_id"),
                    ("permissions", "permission_id"),
                    ("role_permissions", "role_permission_id"),
                    ("user_roles", "user_role_id"),
                    ("user_identities", "identity_id"),
                ]:
                    query = sql.SQL("SELECT * FROM mt.{} ORDER BY {}").format(
                        sql.Identifier(table), sql.Identifier(order)
                    )
                    assert source.execute(query).fetchall() == target.execute(query).fetchall()
                assert (
                    source.execute("SELECT version,sha256 FROM mt_meta.schema_migrations ORDER BY version").fetchall()
                    == target.execute(
                        "SELECT version,sha256 FROM mt_meta.schema_migrations ORDER BY version"
                    ).fetchall()
                )
            engine = create_engine(d.connection.engine.url.set(database=name))
            with engine.begin() as restored:
                actual = type(d)(restored)
                assert actual.permission_bindings(ctx["actor"].user_id) == ()
                with pytest.raises(Exception, match="DIRECTORY_CONFLICT"):
                    actual.bind_permission(role, permission)
        finally:
            if engine is not None:
                engine.dispose()
            assert name.startswith("mt_business_catalog_restore_")
            admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name)))
