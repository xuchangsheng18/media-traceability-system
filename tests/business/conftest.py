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
