"""A real non-superuser schema owner, distinct runtime login, and fixed function ACL."""

import time
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from business_app.data_scope import LookupKey
from business_app.db import Database
from business_app.permissions.types import Principal
from business_app.scope_lookup import SqlScopeLookup
from business_app.types import Actor, Scope
from business_migrations.runner import apply_migrations
from psycopg import sql
from psycopg.conninfo import make_conninfo


def test_non_super_owner_metadata_port_and_runtime_acl(database_dsn, tmp_path):
    owner = "mt_scope_owner_" + uuid4().hex
    login = "mt_scope_runtime_" + uuid4().hex
    name = "mt_business_scope_owner_" + uuid4().hex
    password = uuid4().hex + uuid4().hex
    admin_dsn = make_conninfo(database_dsn, dbname=name)
    runtime = None
    with psycopg.connect(database_dsn, autocommit=True) as admin:
        admin.execute(
            sql.SQL("CREATE ROLE {} NOLOGIN NOSUPERUSER NOBYPASSRLS NOCREATEROLE NOCREATEDB").format(
                sql.Identifier(owner)
            )
        )
        admin.execute(
            sql.SQL("CREATE ROLE {} LOGIN NOSUPERUSER NOBYPASSRLS PASSWORD {}").format(
                sql.Identifier(login), sql.Literal(password)
            )
        )
        admin.execute(sql.SQL("GRANT mt_runtime TO {}").format(sql.Identifier(login)))
        admin.execute(
            sql.SQL("CREATE DATABASE {} OWNER {} TEMPLATE template0").format(
                sql.Identifier(name), sql.Identifier(owner)
            )
        )
        try:
            migrations = Path(__file__).resolve().parents[2] / "backend/business_migrations"
            owner_dsn = make_conninfo(admin_dsn, options="-crole=" + owner)
            history = tmp_path / "non_super_through0016"
            history.mkdir()
            files = [path for path in sorted(migrations.glob("*.sql")) if path.name[:4] <= "0016"]
            assert [path.name[:4] for path in files] == [f"{value:04d}" for value in range(1, 17)]
            for path in files:
                (history / path.name).write_bytes(path.read_bytes())
            applied = apply_migrations(owner_dsn, history)
            assert applied == [f"{value:04d}" for value in range(1, 17)]
            # Explicit test-admin installation prerequisite. The migration itself
            # still runs as the original non-super schema owner. These SET-only
            # grants never reach the runtime login and never enable inheritance.
            admin.execute(
                sql.SQL(
                    "GRANT mt_task_plan_lookup,mt_task_plan_case_reader TO {} WITH INHERIT FALSE, SET TRUE, ADMIN FALSE"
                ).format(sql.Identifier(owner))
            )
            try:
                remaining = apply_migrations(owner_dsn, migrations)
                assert remaining == ["0017", "0018"]
                applied += remaining
            finally:
                admin.execute(
                    sql.SQL("REVOKE mt_task_plan_lookup,mt_task_plan_case_reader FROM {}").format(sql.Identifier(owner))
                )
                assert admin.execute(
                    "SELECT count(*) FROM pg_auth_members "
                    "WHERE member=%s::regrole AND roleid IN "
                    "('mt_task_plan_lookup'::regrole,'mt_task_plan_case_reader'::regrole)",
                    (owner,),
                ).fetchone() == (0,)
            assert applied == [f"{value:04d}" for value in range(1, 19)]
            assert apply_migrations(owner_dsn, migrations) == []
            org, user, case, source = [uuid4() for _ in range(4)]
            with psycopg.connect(admin_dsn) as seed:
                seed.execute("INSERT INTO mt.organizations(org_id,name) VALUES(%s,'synthetic-owner-unit')", (org,))
                seed.execute(
                    "INSERT INTO mt.users(user_id,org_id,subject,enabled) VALUES(%s,%s,%s,true)", (user, org, str(user))
                )
                seed.execute(
                    "INSERT INTO mt.cases(case_id,org_id,display_code,status) VALUES(%s,%s,'synthetic-owner-case','ACTIVE')",
                    (case, org),
                )
                seed.execute(
                    "INSERT INTO mt.case_membership(membership_id,user_id,org_id,case_id) VALUES(%s,%s,%s,%s)",
                    (uuid4(), user, org, case),
                )
                seed.execute(
                    "INSERT INTO mt.source_registry(source_id,org_id,case_id,name,source_type,authorization_ref,purpose,authorization_status,authorization_version) VALUES(%s,%s,%s,'synthetic','synthetic','urn:synthetic-only',ARRAY['upload'],'verified','v1')",
                    (source, org, case),
                )
                properties = seed.execute(
                    "SELECT p.prosecdef,r.rolname,r.rolsuper,r.rolbypassrls,p.proconfig FROM pg_proc p JOIN pg_roles r ON r.oid=p.proowner WHERE p.oid='mt.lookup_scope_metadata(text,uuid)'::regprocedure"
                ).fetchone()
                assert properties == (True, owner, False, False, ["search_path=pg_catalog, mt"])
                assert seed.execute(
                    "SELECT EXISTS(SELECT 1 FROM pg_proc p,LATERAL aclexplode(p.proacl) a WHERE p.oid='mt.lookup_scope_metadata(text,uuid)'::regprocedure AND a.grantee=0 AND a.privilege_type='EXECUTE')"
                ).fetchone() == (False,)
                assert seed.execute(
                    "SELECT has_function_privilege(%s,'mt.lookup_scope_metadata(text,uuid)','EXECUTE')", (login,)
                ).fetchone() == (True,)
            runtime = Database(make_conninfo(admin_dsn, user=login, password=password, options=""))
            subject = Principal(
                Actor(user, org), "https://identity.example.test", "synthetic-owner-user", int(time.time()) + 300
            )
            metadata = SqlScopeLookup(runtime).read(subject, "getSource", LookupKey("source", source))
            assert metadata.target.case_id == case
            assert "authorization_ref" not in metadata.projection
            privileged = Database(make_conninfo(admin_dsn, options="-crole=" + owner))
            try:
                with pytest.raises(RuntimeError, match="PRIVILEGED"):
                    with privileged.transaction(Scope(subject.actor, case)):
                        pytest.fail("SCHEMA_OWNER_IS_NOT_AN_APPLICATION_RUNTIME")
            finally:
                privileged.close()
        finally:
            if runtime is not None:
                runtime.close()
            # Also clean the explicit precondition after any earlier failure;
            # no cross-test or runtime membership may survive this fixture.
            admin.execute(
                sql.SQL("REVOKE mt_task_plan_lookup,mt_task_plan_case_reader FROM {}").format(sql.Identifier(owner))
            )
            assert admin.execute(
                "SELECT count(*) FROM pg_auth_members WHERE member=%s::regrole "
                "AND roleid IN ('mt_task_plan_lookup'::regrole,'mt_task_plan_case_reader'::regrole)",
                (owner,),
            ).fetchone() == (0,)
            assert name.startswith("mt_business_scope_owner_")
            admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name)))
            admin.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(login)))
            admin.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(owner)))
