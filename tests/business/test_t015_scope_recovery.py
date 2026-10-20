"""Incremental scope upgrade and independent restored-database enforcement."""

import asyncio
import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from business_app.db import Database
from business_app.errors import BusinessError
from business_app.permissions.context import current_authorization, request_authorization
from business_app.scope_catalog import TABLE_SCOPES
from business_app.scope_context import current_data_scope, current_scope_transaction
from business_app.types import Scope
from business_migrations.runner import apply_migrations
from psycopg import sql
from psycopg.conninfo import make_conninfo
from sqlalchemy import text

from scripts.verify_business_foundation import configured_environment, validate_target
from tests.business.conftest import PrivateTestDSN
from tests.business.test_recovery import pg_tool
from tests.business.test_t014_permissions import permission_context as permission_context
from tests.business.test_t014_revocation import environment
from tests.business.test_t015_scope_sql import case_evidence, two_cases

ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS = ROOT / "backend/business_migrations"


@contextmanager
def empty_scope_database(configured):
    name = "mt_business_test_" + uuid4().hex
    with psycopg.connect(configured, autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {} TEMPLATE template0").format(sql.Identifier(name)))
        try:
            yield PrivateTestDSN(make_conninfo(configured, dbname=name))
        finally:
            assert name.startswith("mt_business_test_") and len(name) == 49
            admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name)))


@pytest.fixture
def fresh_scope_database():
    env = configured_environment()
    validate_target(env)
    with empty_scope_database(env["MT_BUSINESS_TEST_ADMIN_DSN"]) as dsn:
        yield dsn


def copied_migrations(folder, through=10):
    folder.mkdir()
    for file in sorted(MIGRATIONS.glob("*.sql")):
        if int(file.name.split("_", 1)[0]) <= through:
            (folder / file.name).write_bytes(file.read_bytes())
    return folder


def test_upgrade_from_0009_and_partial_failure_are_atomic(fresh_scope_database, tmp_path):
    dsn = fresh_scope_database
    nine = copied_migrations(tmp_path / "nine", 9)
    assert apply_migrations(dsn, nine) == [f"{value:04d}" for value in range(1, 10)]
    failed = copied_migrations(tmp_path / "failed")
    current = failed / "0010_data_scope.sql"
    current.write_bytes(current.read_bytes() + b"\nSELECT mt.t015_deliberate_missing_function();\n")
    with pytest.raises(psycopg.Error):
        apply_migrations(dsn, failed)
    with psycopg.connect(dsn) as admin:
        assert admin.execute("SELECT count(*) FROM mt_meta.schema_migrations").fetchone() == (9,)
        assert admin.execute("SELECT to_regprocedure('mt.scope_mode()')").fetchone() == (None,)
        assert admin.execute(
            "SELECT count(*) FROM pg_policies WHERE schemaname='mt' AND policyname='request_data_scope'"
        ).fetchone() == (0,)
    assert apply_migrations(dsn, MIGRATIONS) == ["0010", "0011"]
    assert apply_migrations(dsn, MIGRATIONS) == []


@pytest.mark.parametrize("version", ["0001", "0009", "0010"])
def test_reapply_checks_exact_old_and_new_migration_digests(fresh_scope_database, tmp_path, version):
    dsn = fresh_scope_database
    assert len(apply_migrations(dsn, MIGRATIONS)) == 11
    changed = copied_migrations(tmp_path / "changed", 11)
    file = next(changed.glob(version + "_*.sql"))
    file.write_bytes(file.read_bytes() + b"\n-- intentional digest mismatch\n")
    with pytest.raises(RuntimeError, match="DIGEST"):
        apply_migrations(dsn, changed)
    expected = [
        (p.name.split("_", 1)[0], hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(MIGRATIONS.glob("*.sql"))
    ]
    with psycopg.connect(dsn) as admin:
        assert (
            admin.execute("SELECT version,sha256 FROM mt_meta.schema_migrations ORDER BY version").fetchall()
            == expected
        )


def table_scope_catalog(connection):
    actual = connection.execute(
        "SELECT c.relname,c.relrowsecurity,c.relforcerowsecurity FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='mt' AND c.relkind='r' ORDER BY c.relname"
    ).fetchall()
    assert [row[0] for row in actual] == sorted(TABLE_SCOPES) and len(actual) == 64
    for name, enabled, forced in actual:
        if TABLE_SCOPES[name].runtime_select:
            assert enabled, name
            # Directory ownership is intentionally distinct from runtime RLS.
            # Business CASE/ORG/MIXED tables force even owner filtering; the
            # pre-existing fixed directory owner is not a runtime identity.
            assert forced is (TABLE_SCOPES[name].scope_class != "DIRECTORY"), name
            assert connection.execute(
                "SELECT permissive FROM pg_policies WHERE schemaname='mt' AND tablename=%s AND policyname='request_data_scope'",
                (name,),
            ).fetchone() == ("RESTRICTIVE",)
    assert connection.execute("SELECT count(*) FROM information_schema.columns WHERE table_schema='mt'").fetchone() == (
        861,
    )
    assert connection.execute(
        "SELECT EXISTS(SELECT 1 FROM pg_proc p,LATERAL aclexplode(p.proacl) a WHERE p.oid='mt.lookup_scope_metadata(text,uuid)'::regprocedure AND a.grantee=0 AND a.privilege_type='EXECUTE')"
    ).fetchone() == (False,)
    assert connection.execute(
        "SELECT proconfig FROM pg_proc WHERE oid='mt.lookup_scope_metadata(text,uuid)'::regprocedure"
    ).fetchone() == (["search_path=pg_catalog, mt"],)


def test_restored_scope_policies_acl_and_generation_are_not_bypassed(permission_context, tmp_path):
    ctx = permission_context
    accepted = environment(ctx)
    first, second = two_cases(ctx)
    other = dict(ctx, actor=ctx["other_actor"], case_id=ctx["other_case_id"])
    third, fourth = two_cases(other)
    dump = tmp_path / "scope.dump"
    pg_tool("pg_dump", ctx["admin_dsn"], "-Fc", "--no-owner", "--file", str(dump))
    with empty_scope_database(ctx["admin_dsn"]) as restored_admin:
        pg_tool("pg_restore", restored_admin, "--no-owner", "--exit-on-error", str(dump))
        with psycopg.connect(restored_admin) as admin:
            table_scope_catalog(admin)
            assert admin.execute(
                "SELECT has_table_privilege('mt_runtime','mt.object_version','UPDATE')"
            ).fetchone() == (False,)
            assert admin.execute(
                "SELECT has_function_privilege('mt_runtime','mt.lookup_scope_metadata(text,uuid)','EXECUTE')"
            ).fetchone() == (True,)
        runtime = Database(
            make_conninfo(
                ctx["settings"].database_dsn, dbname=psycopg.conninfo.conninfo_to_dict(restored_admin)["dbname"]
            )
        )
        try:
            for current, record in [(ctx, first), (ctx, second), (other, third), (other, fourth)]:
                with case_evidence(current, record["case"]):
                    with runtime.transaction(Scope(current["actor"], record["case"])) as connection:
                        assert connection.execute(text("SELECT task_id FROM mt.analysis_task")).scalars().all() == [
                            record["task"]
                        ]
            # Missing actual authorization/recovery authority never inherits the
            # restored SQL catalog as an ALLOW. Real generation rotation and
            # accepted fresh proofs are also tested by the retained T014 suite.
            with pytest.raises(BusinessError) as missing:
                with runtime.transaction(Scope(ctx["actor"], first["case"])):
                    pytest.fail("RESTORED_CATALOG_IS_NOT_AN_AUTHORIZATION_PROOF")
            assert missing.value.http_status == 503
            with pytest.raises(BusinessError) as stale_generation:
                with request_authorization(accepted.evidence, accepted.fence, mutation=True):
                    with runtime.identity_transaction(ctx["actor"]):
                        pytest.fail("OLD_DATABASE_GENERATION_MUST_NOT_AUTHORIZE_RESTORED_TARGET")
            assert stale_generation.value.code == "AUTHORIZATION_CHANGED"
            # Actual negative control: alter only this disposable restored DB.
            # Without the new restrictive policy, the same user can see both
            # legitimate memberships. The assertion must detect that leak.
            with psycopg.connect(restored_admin) as admin:
                admin.execute("DROP POLICY request_data_scope ON mt.analysis_task")
            with pytest.raises(AssertionError, match="MUTANT_SCOPE_BYPASS"):
                with case_evidence(ctx, first["case"]):
                    with runtime.transaction(Scope(ctx["actor"], first["case"])) as connection:
                        assert connection.execute(text("SELECT task_id FROM mt.analysis_task")).scalars().all() == [
                            first["task"]
                        ], "MUTANT_SCOPE_BYPASS"
        finally:
            runtime.close()


def test_pool_and_thread_context_do_not_leak_scope_after_failure(business_context):
    ctx = business_context
    first, second = two_cases(ctx)
    barrier = threading.Barrier(2)

    def request(record):
        assert current_data_scope() is current_scope_transaction() is current_authorization() is None
        with pytest.raises(ValueError, match="synthetic-transaction-failure"):
            with case_evidence(ctx, record["case"]):
                barrier.wait(timeout=5)
                with ctx["database"].transaction(Scope(ctx["actor"], record["case"])) as connection:
                    assert connection.execute(text("SELECT task_id FROM mt.analysis_task")).scalars().all() == [
                        record["task"]
                    ]
                    raise ValueError("synthetic-transaction-failure")
        assert current_data_scope() is current_scope_transaction() is current_authorization() is None
        with case_evidence(ctx, record["case"]):
            with ctx["database"].transaction(Scope(ctx["actor"], record["case"])) as connection:
                assert connection.execute(text("SELECT task_id FROM mt.analysis_task")).scalars().all() == [
                    record["task"]
                ]
        return record["task"]

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert set(pool.map(request, [first, second])) == {first["task"], second["task"]}
    assert current_data_scope() is current_scope_transaction() is current_authorization() is None


def test_async_requests_and_sync_threads_keep_their_own_case(business_context):
    ctx = business_context
    first, second = two_cases(ctx)

    def query(record):
        with ctx["database"].transaction(Scope(ctx["actor"], record["case"])) as connection:
            return connection.execute(text("SELECT task_id FROM mt.analysis_task")).scalars().all()

    async def request(record):
        with case_evidence(ctx, record["case"]):
            before = current_authorization()
            await asyncio.sleep(0)
            values = await asyncio.to_thread(query, record)
            assert current_authorization() is before and current_data_scope() is None
            assert values == [record["task"]]
        assert current_authorization() is None

    async def run():
        await asyncio.gather(request(first), request(second))

    asyncio.run(run())
    assert current_data_scope() is current_scope_transaction() is current_authorization() is None


def test_new_schema_rejects_old_client_without_request_scope(business_context):
    ctx = business_context
    two_cases(ctx)
    with ctx["database"].engine.begin() as connection:
        for key, value in {
            "app.actor_id": str(ctx["actor"].user_id),
            "app.org_id": str(ctx["actor"].org_id),
            "app.scope_mode": "",
            "app.case_id": "",
        }.items():
            connection.execute(text("SELECT set_config(:key,:value,true)"), dict(key=key, value=value))
        assert connection.execute(text("SELECT task_id FROM mt.analysis_task")).scalars().all() == []
    with case_evidence(ctx, ctx["case_id"]):
        with ctx["database"].transaction(Scope(ctx["actor"], ctx["case_id"])) as connection:
            assert len(connection.execute(text("SELECT task_id FROM mt.analysis_task")).all()) == 1
