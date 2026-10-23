"""Complete role facts on real isolated PostgreSQL, without role or account seeds."""

import time
from dataclasses import replace
from uuid import uuid4

import psycopg
import pytest
from business_app.db import Database
from business_app.errors import BusinessError
from psycopg import sql
from psycopg.conninfo import make_conninfo
from sqlalchemy import text

from tests.business.test_t014_permissions import permission_context as permission_context
from tests.business.test_t014_permissions import permission_module


def role_reader(ctx):
    return permission_module("role_facts").RoleDirectory(ctx["lookup"], clock=time.time)


def test_all_active_roles_include_nonmatching_permission_role(permission_context):
    ctx = permission_context
    role, binding = uuid4(), uuid4()
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            "INSERT INTO mt.roles(role_id,code,description,enabled) VALUES(%s,'auditor','synthetic',true)", (role,)
        )
        admin.execute(
            "INSERT INTO mt.user_roles(user_role_id,user_id,role_id) VALUES(%s,%s,%s)",
            (binding, ctx["actor"].user_id, role),
        )
    reader = role_reader(ctx)
    value = reader.read_roles(ctx["principal"], "identity.read")
    assert value.principal == ctx["principal"]
    assert value.eligible is True
    assert {item.code for item in value.active_roles} == {"fixture.role", "auditor"}
    assert set(value.permission_role_ids) == {ctx["role"]}
    assert value.version_digest == reader.read_roles(ctx["principal"], "identity.read").version_digest
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute("UPDATE mt.user_roles SET revoked_at=statement_timestamp() WHERE user_role_id=%s", (binding,))
    changed = reader.read_roles(ctx["principal"], "identity.read")
    assert {item.code for item in changed.active_roles} == {"fixture.role"}
    assert changed.version_digest != value.version_digest


@pytest.mark.parametrize("field", ["issuer", "subject", "user", "org", "expired"])
def test_role_facts_exact_principal_and_expiry(permission_context, field):
    ctx = permission_context
    principal = ctx["principal"]
    if field in {"issuer", "subject"}:
        principal = replace(principal, **{field: getattr(principal, field).upper()})
    elif field in {"user", "org"}:
        actor = replace(principal.actor, **{field + "_id": uuid4()})
        principal = replace(principal, actor=actor)
    else:
        principal = replace(principal, expires_at=int(time.time()) - 1)
    with pytest.raises(BusinessError) as caught:
        role_reader(ctx).read_roles(principal, "identity.read")
    assert caught.value.http_status == 401


def test_role_lookup_is_function_only(permission_context):
    ctx = permission_context
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        assert admin.execute(
            "SELECT to_regprocedure('mt.lookup_role_facts(text,text,uuid,uuid,text)') IS NOT NULL"
        ).fetchone() == (True,), "complete role-fact function is missing"
        assert admin.execute(
            "SELECT has_function_privilege('mt_runtime','mt.lookup_role_facts(text,text,uuid,uuid,text)','EXECUTE')"
        ).fetchone() == (False,)
        for table in ("roles", "users", "user_roles", "role_permissions", "user_identities"):
            assert admin.execute(
                "SELECT has_table_privilege('mt_permission_lookup',%s,'SELECT,INSERT,UPDATE,DELETE,TRUNCATE')",
                ("mt." + table,),
            ).fetchone() == (False,)
        assert admin.execute(
            "SELECT count(*) FROM pg_proc p CROSS JOIN LATERAL aclexplode(p.proacl) a "
            "WHERE p.oid='mt.lookup_role_facts(text,text,uuid,uuid,text)'::regprocedure AND a.grantee=0"
        ).fetchone() == (0,)
        assert admin.execute("SELECT pg_has_role('mt_runtime','mt_permission_lookup','MEMBER')").fetchone() == (False,)


def test_transaction_role_lookup_is_bound_to_session_actor(permission_context):
    from tests.business.http_fixtures import synthetic_case_evidence

    ctx = permission_context
    reader = role_reader(ctx)
    before = reader.read_roles(ctx["principal"], "identity.read")
    with (
        synthetic_case_evidence(ctx["actor"], ctx["case_id"]),
        ctx["database"].identity_transaction(ctx["actor"]) as connection,
    ):
        current = reader.read_roles(ctx["principal"], "identity.read", connection=connection)
        assert current == before
        wrong = replace(ctx["principal"], subject="not-the-current-subject")
        with pytest.raises(BusinessError) as caught:
            reader.read_roles(wrong, "identity.read", connection=connection)
        assert caught.value.http_status == 401
    with ctx["database"].engine.begin() as connection:
        with pytest.raises(BusinessError) as caught:
            reader.read_roles(ctx["principal"], "identity.read", connection=connection)
        assert caught.value.http_status == 401
    with (
        synthetic_case_evidence(ctx["other_actor"], ctx["other_case_id"]),
        ctx["database"].identity_transaction(ctx["other_actor"]) as connection,
    ):
        assert connection.execute(text("SELECT mt.actor_id()")).scalar_one() == ctx["other_actor"].user_id
        with pytest.raises(BusinessError) as caught:
            reader.read_roles(ctx["principal"], "identity.read", connection=connection)
        assert caught.value.http_status == 401


def test_complete_role_facts_survive_independent_database_restore(permission_context, tmp_path):
    from tests.business.test_recovery import pg_tool

    ctx = permission_context
    expected = role_reader(ctx).read_roles(ctx["principal"], "identity.read")
    target_name = "mt_business_role_restore_" + uuid4().hex
    restored_admin = make_conninfo(ctx["admin_dsn"], dbname=target_name)
    dump = tmp_path / "roles.dump"
    pg_tool("pg_dump", ctx["admin_dsn"], "-Fc", "--no-owner", "--file", str(dump))
    restored = None
    with psycopg.connect(ctx["admin_dsn"], autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {} TEMPLATE template0").format(sql.Identifier(target_name)))
        try:
            pg_tool("pg_restore", restored_admin, "--no-owner", "--exit-on-error", str(dump))
            url = ctx["lookup"].engine.url
            restored = Database(make_conninfo(restored_admin, user=str(url.username), password=str(url.password)))
            assert (
                permission_module("role_facts")
                .RoleDirectory(restored, clock=time.time)
                .read_roles(ctx["principal"], "identity.read")
                == expected
            )
            with psycopg.connect(restored_admin) as target, psycopg.connect(ctx["admin_dsn"]) as source:
                assert (
                    target.execute("SELECT version,sha256 FROM mt_meta.schema_migrations ORDER BY version").fetchall()
                    == source.execute(
                        "SELECT version,sha256 FROM mt_meta.schema_migrations ORDER BY version"
                    ).fetchall()
                )
        finally:
            if restored is not None:
                restored.close()
            admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(target_name)))
