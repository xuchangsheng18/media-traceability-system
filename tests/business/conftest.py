"""Only explicitly configured isolated PostgreSQL targets are permitted."""

import json
import os
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo


class PrivateTestDSN(str):
    def __repr__(self):
        return "'<isolated-test-database-credentials-redacted>'"


@pytest.fixture
def database_dsn():
    configured = os.environ.get("MT_BUSINESS_TEST_ADMIN_DSN")
    private = (
        Path(os.environ.get("MT_RUNTIME_DIR", "/workspace/glwy/runtime/media-traceability-system"))
        / "business-test-postgres-private.json"
    )
    if not configured and private.is_file():
        configured = json.loads(private.read_text())["admin_dsn"]
    if not configured:
        pytest.fail("Explicit isolated business test database is required; never use the PoC fallback")
    settings = conninfo_to_dict(configured)
    if settings.get("dbname") == "media_trace_poc":
        pytest.fail("PoC database is forbidden as the business test administration target")
    name = "mt_business_test_" + uuid4().hex
    with psycopg.connect(configured, autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {} TEMPLATE template0").format(sql.Identifier(name)))
        try:
            yield PrivateTestDSN(make_conninfo(configured, dbname=name))
        finally:
            assert name.startswith("mt_business_test_") and len(name) == 49
            admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name)))


@pytest.fixture
def business_context(database_dsn, tmp_path):
    root = Path(__file__).resolve().parents[2]
    if not (root / "backend/business_app/main.py").is_file():
        yield None
        return
    from business_app.db import Database
    from business_app.errors import BusinessError
    from business_app.settings import BusinessSettings
    from business_app.types import Actor, Scope
    from business_migrations.runner import apply_migrations

    apply_migrations(database_dsn, root / "backend/business_migrations")
    org, other_org, case, other_case, user, other_user = [uuid4() for _ in range(6)]
    role = "mt_business_runtime_" + uuid4().hex
    password = uuid4().hex + uuid4().hex
    with psycopg.connect(database_dsn) as connection:
        connection.execute(
            sql.SQL("CREATE ROLE {} LOGIN NOSUPERUSER NOBYPASSRLS PASSWORD {}").format(
                sql.Identifier(role), sql.Literal(password)
            )
        )
        connection.execute(sql.SQL("GRANT mt_runtime TO {}").format(sql.Identifier(role)))
        for current_org, current_user, current_case in [(org, user, case), (other_org, other_user, other_case)]:
            connection.execute(
                "INSERT INTO mt.organizations(org_id,name) VALUES(%s,'synthetic-test-organization')", (current_org,)
            )
            connection.execute(
                "INSERT INTO mt.users(user_id,org_id,subject,enabled) VALUES(%s,%s,%s,true)",
                (current_user, current_org, str(current_user)),
            )
            connection.execute(
                "INSERT INTO mt.cases(case_id,org_id,display_code,status) VALUES(%s,%s,%s,'ACTIVE')",
                (current_case, current_org, str(current_case)),
            )
            connection.execute(
                "INSERT INTO mt.case_membership(membership_id,case_id,org_id,user_id) VALUES(%s,%s,%s,%s)",
                (uuid4(), current_case, current_org, current_user),
            )
    runtime_dsn = PrivateTestDSN(make_conninfo(database_dsn, user=role, password=password))
    settings = BusinessSettings(
        database_dsn=runtime_dsn,
        object_root=tmp_path / "objects",
        max_upload_bytes=1_048_576,
        part_size_bytes=256_000,
        upload_ttl_seconds=3600,
        cursor_secret=uuid4().hex,
    )
    actor = Actor(user_id=user, org_id=org)
    other_actor = Actor(user_id=other_user, org_id=other_org)

    class TestAuthority:
        def authenticate(self, bearer):
            if bearer != "test-only-valid-token":
                raise BusinessError("AUTHENTICATION_REQUIRED", 401)
            return actor

        def authorize_case(self, current_actor, case_id, action):
            if current_actor != actor or case_id != case:
                raise BusinessError("CASE_NOT_FOUND", 404)
            return Scope(actor=current_actor, case_id=case_id)

        def authorize_source(self, scope, source_id, purpose):
            with psycopg.connect(database_dsn) as connection:
                row = connection.execute(
                    "SELECT authorization_status,purpose,expires_at FROM mt.source_registry WHERE case_id=%s AND source_id=%s",
                    (scope.case_id, source_id),
                ).fetchone()
            if not row or row[0] != "verified" or purpose not in row[1]:
                raise BusinessError("SOURCE_AUTHORIZATION_REQUIRED", 403)
            from datetime import datetime, timezone

            if row[2] is not None and row[2] <= datetime.now(timezone.utc):
                raise BusinessError("SOURCE_AUTHORIZATION_REQUIRED", 403)

    source = uuid4()
    with psycopg.connect(database_dsn) as connection:
        connection.execute(
            "INSERT INTO mt.source_registry(source_id,org_id,case_id,name,source_type,authorization_ref,purpose,authorization_status,authorization_version) VALUES(%s,%s,%s,'synthetic','test-only','fixture-not-formal-authority',ARRAY['upload'],'verified','test-version-1')",
            (source, org, case),
        )
    database = Database(runtime_dsn)
    try:
        yield dict(
            settings=settings,
            authority=TestAuthority(),
            database=database,
            actor=actor,
            other_actor=other_actor,
            case_id=case,
            source_id=source,
            other_case_id=other_case,
            admin_dsn=database_dsn,
        )
    finally:
        database.close()
        with psycopg.connect(database_dsn) as connection:
            connection.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
            connection.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))
