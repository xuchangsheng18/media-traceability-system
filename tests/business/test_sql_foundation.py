import datetime
import hashlib
import json
from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo


def test_current_canonical_sql_and_retained_ranking_constraints(database_dsn):
    root = Path(__file__).resolve().parents[2]
    name = "mt_business_sql_" + uuid4().hex
    checks: list[dict[str, str | None]] = []
    with psycopg.connect(database_dsn, autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {} TEMPLATE template0").format(sql.Identifier(name)))
        try:
            with psycopg.connect(make_conninfo(database_dsn, dbname=name), autocommit=True) as connection:
                for path in [
                    "docs/04-database/initial-schema.sql",
                    "tests/sql/integrity-tests.sql",
                    "tests/sql/ranking-fixtures.sql",
                ]:
                    raw = (root / path).read_bytes()
                    connection.execute(raw.decode("utf-8"))
                    checks.append({"name": path, "sha256": hashlib.sha256(raw).hexdigest(), "status": "PASS"})
                cases = json.loads((root / "tests/sql/first-source-cases.json").read_text())["cases"]
                for case in cases:
                    actual = None
                    try:
                        connection.execute(case["sql"])
                    except psycopg.Error as error:
                        actual = error.sqlstate
                        connection.execute("ROLLBACK")
                    assert actual == case["expected_sqlstate"], case["name"]
                    checks.append({"name": case["name"], "expected_sqlstate": actual, "status": "PASS"})
                row = connection.execute(
                    "SELECT count(*) FROM information_schema.columns WHERE table_schema='mt'"
                ).fetchone()
                assert row is not None and row[0] == 825
                version = connection.execute("SHOW server_version").fetchone()
                assert version is not None and str(version[0]).startswith("16.")
            report = {
                "status": "PASS",
                "scope": "current_canonical_SQL_and_retained_synthetic_constraints_not_production",
                "postgres_version": str(version[0]),
                "checks": checks,
                "business_fields": 825,
                "ended_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "formal_approved": False,
            }
            (root / "docs/00-project/validation/database-foundation-report.json").write_bytes(
                (json.dumps(report, indent=2) + "\n").encode()
            )
        finally:
            assert name.startswith("mt_business_sql_")
            admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name)))
