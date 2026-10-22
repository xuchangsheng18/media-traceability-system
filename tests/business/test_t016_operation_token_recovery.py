"""Upgrade preserves legacy evidence and never fabricates a current token binding."""

import hashlib
from contextlib import contextmanager
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from business_migrations.runner import apply_migrations
from psycopg import sql

from tests.business.test_t015_scope_recovery import copied_migrations
from tests.business.test_t015_scope_recovery import fresh_scope_database as fresh_scope_database

ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS = ROOT / "backend/business_migrations"


@pytest.fixture
def token_database(fresh_scope_database):
    """Disposable real SQL fixture; it grants no HTTP or formal business authority."""
    dsn = fresh_scope_database
    apply_migrations(dsn, MIGRATIONS)
    org, actor = uuid4(), uuid4()
    cases = []
    with psycopg.connect(dsn) as admin:
        admin.execute("INSERT INTO mt.organizations(org_id,name) VALUES(%s,'self-owned token SQL')", (org,))
        admin.execute(
            "INSERT INTO mt.users(user_id,org_id,subject,enabled) VALUES(%s,%s,%s,true)",
            (actor, org, str(actor)),
        )
        for _ in range(2):
            case, approval, task = uuid4(), uuid4(), uuid4()
            admin.execute(
                "INSERT INTO mt.cases(case_id,org_id,display_code,status) VALUES(%s,%s,%s,'ACTIVE')",
                (case, org, str(case)),
            )
            admin.execute(
                "INSERT INTO mt.case_membership(membership_id,case_id,org_id,user_id) VALUES(%s,%s,%s,%s)",
                (uuid4(), case, org, actor),
            )
            admin.execute(
                "INSERT INTO mt.approval_request(approval_id,org_id,case_id,object_type,object_id,object_version,purpose,policy_version,requested_by,state,reason,run_version,result_version,expires_at) VALUES(%s,%s,%s,'task',%s,1,'seal','self-owned-1',%s,'APPROVED','synthetic SQL binding only',1,1,clock_timestamp()+interval '10 minutes')",
                (approval, org, case, task, actor),
            )
            cases.append(dict(case_id=case, approval_id=approval, object_id=task))
    return dict(dsn=dsn, org_id=org, actor_id=actor, cases=cases)


def set_token_scope(connection, context, record, operation="issueOperationToken"):
    for name, value in {
        "app.actor_id": context["actor_id"],
        "app.org_id": context["org_id"],
        "app.case_id": record["case_id"],
        "app.scope_mode": "CASE",
        "app.operation_id": operation,
    }.items():
        connection.execute("SELECT set_config(%s,%s,true)", (name, str(value)))


@contextmanager
def token_runtime(context, record, operation="issueOperationToken"):
    with psycopg.connect(context["dsn"]) as connection:
        connection.execute("SET LOCAL ROLE mt_runtime")
        set_token_scope(connection, context, record, operation)
        assert connection.execute(
            "SELECT mt.actor_in_org(),mt.can_access_case(%s)", (record["case_id"],)
        ).fetchone() == (
            True,
            True,
        )
        yield connection


def token_values(connection, context, record):
    current = connection.execute("SELECT clock_timestamp()").fetchone()[0]
    return dict(
        token_id=uuid4(),
        org_id=context["org_id"],
        case_id=record["case_id"],
        approval_id=record["approval_id"],
        actor_id=context["actor_id"],
        purpose="seal",
        object_id=record["object_id"],
        object_version=1,
        token_sha256=hashlib.sha256(uuid4().bytes).hexdigest(),
        expires_at=current + timedelta(seconds=60),
        consumed_at=None,
        created_at=current - timedelta(seconds=1),
        updated_at=current,
        row_version=1,
        created_by=context["actor_id"],
        storage_version=1,
        action="sealEvidence",
        object_type="task",
        approval_version=1,
        approval_policy_version="self-owned-1",
        permission_policy_version="synthetic-permission-1",
        rule_version="synthetic-seal-60s",
        recovery_generation="synthetic-generation-1",
        key_id="synthetic-key-1",
        principal_sha256="b" * 64,
        request_sha256="c" * 64,
        idempotency_key=str(uuid4()),
    )


def insert_token(connection, values):
    connection.execute(
        sql.SQL("INSERT INTO mt.operation_token({}) VALUES({})").format(
            sql.SQL(",").join(map(sql.Identifier, values)),
            sql.SQL(",").join(sql.Placeholder() for _ in values),
        ),
        tuple(values.values()),
    )


def test_v1_nullable_bindings_cannot_bypass_sql_check(token_database):
    context = token_database
    first = context["cases"][0]
    accepted = []
    with token_runtime(context, first) as connection:
        for field in (
            "action",
            "object_type",
            "approval_version",
            "approval_policy_version",
            "permission_policy_version",
            "rule_version",
            "recovery_generation",
            "key_id",
            "principal_sha256",
            "request_sha256",
            "idempotency_key",
        ):
            values = dict(token_values(connection, context, first), **{field: None})
            try:
                with connection.transaction():
                    insert_token(connection, values)
            except psycopg.errors.CheckViolation:
                continue
            accepted.append(field)
        assert accepted == [], f"NULL_VERSIONED_BINDING_ACCEPTED:{accepted}"


def test_v1_empty_or_invalid_key_rule_and_generation_are_rejected(token_database):
    context = token_database
    first = context["cases"][0]
    accepted = []
    with token_runtime(context, first) as connection:
        for field, invalid in (
            ("permission_policy_version", ""),
            ("permission_policy_version", " "),
            ("rule_version", ""),
            ("rule_version", "bad rule"),
            ("recovery_generation", ""),
            ("recovery_generation", " "),
            ("key_id", ""),
            ("key_id", "bad key"),
        ):
            values = dict(token_values(connection, context, first), **{field: invalid})
            try:
                with connection.transaction():
                    insert_token(connection, values)
            except psycopg.errors.CheckViolation:
                continue
            accepted.append((field, invalid))
        assert accepted == [], f"INCOMPLETE_VERSIONED_BINDING_ACCEPTED:{accepted}"


def test_same_member_of_two_cases_cannot_mix_token_and_approval_scope(token_database):
    context = token_database
    first, second = context["cases"]
    with token_runtime(context, first) as connection:
        assert connection.execute("SELECT mt.can_access_case(%s)", (second["case_id"],)).fetchone() == (True,)
        for values in (
            dict(token_values(connection, context, first), approval_id=second["approval_id"]),
            token_values(connection, context, second),
        ):
            with pytest.raises(psycopg.errors.CheckViolation):
                with connection.transaction():
                    insert_token(connection, values)
        assert connection.execute("SELECT count(*) FROM mt.operation_token").fetchone() == (0,)
    with token_runtime(context, second) as connection:
        values = token_values(connection, context, second)
        insert_token(connection, values)
    with token_runtime(context, first, "sealEvidence") as connection:
        assert (
            connection.execute(
                "SELECT token_id FROM mt.operation_token WHERE token_id=%s", (values["token_id"],)
            ).fetchall()
            == []
        )
        assert (
            connection.execute(
                "UPDATE mt.operation_token SET consumed_at=clock_timestamp(),row_version=row_version+1 WHERE token_id=%s",
                (values["token_id"],),
            ).rowcount
            == 0
        )
    with token_runtime(context, second) as connection:
        assert connection.execute(
            "SELECT consumed_at,row_version FROM mt.operation_token WHERE token_id=%s", (values["token_id"],)
        ).fetchone() == (None, 1)


def test_consumption_cannot_change_credential_reconstruction_bindings(token_database):
    context = token_database
    first = context["cases"][0]
    with token_runtime(context, first) as connection:
        values = token_values(connection, context, first)
        insert_token(connection, values)
    changes = dict(
        token_id=uuid4(),
        org_id=uuid4(),
        case_id=context["cases"][1]["case_id"],
        approval_id=context["cases"][1]["approval_id"],
        actor_id=uuid4(),
        purpose="report_export",
        object_id=uuid4(),
        object_version=2,
        token_sha256="f" * 64,
        expires_at=values["expires_at"] + timedelta(seconds=1),
        created_at=values["created_at"] - timedelta(seconds=1),
        created_by=uuid4(),
        storage_version=0,
        action="exportAudit",
        object_type="report",
        approval_version=2,
        approval_policy_version="changed-approval",
        permission_policy_version="changed-permission",
        rule_version="changed-rule",
        recovery_generation="changed-generation",
        key_id="changed-key",
        principal_sha256="d" * 64,
        request_sha256="e" * 64,
        idempotency_key="changed-retry-key",
    )
    with token_runtime(context, first, "sealEvidence") as connection:
        for field, value in changes.items():
            with pytest.raises(psycopg.Error) as rejected:
                with connection.transaction():
                    connection.execute(
                        sql.SQL(
                            "UPDATE mt.operation_token SET {}=%s,consumed_at=clock_timestamp(),row_version=row_version+1 WHERE token_id=%s"
                        ).format(sql.Identifier(field)),
                        (value, values["token_id"]),
                    )
            assert rejected.value.sqlstate in {"23514", "55000"}, field
        assert connection.execute(
            "SELECT consumed_at,row_version FROM mt.operation_token WHERE token_id=%s", (values["token_id"],)
        ).fetchone() == (None, 1)
        before = connection.execute("SELECT clock_timestamp()").fetchone()[0]
        connection.execute(
            "UPDATE mt.operation_token SET consumed_at='2000-01-01Z',row_version=row_version+1 WHERE token_id=%s",
            (values["token_id"],),
        )
        consumed, after = connection.execute(
            "SELECT consumed_at,clock_timestamp() FROM mt.operation_token WHERE token_id=%s", (values["token_id"],)
        ).fetchone()
        assert before <= consumed <= after


def test_expiry_is_measured_at_consumption_after_transaction_start(token_database):
    context = token_database
    first = context["cases"][0]
    with token_runtime(context, first) as connection:
        values = token_values(connection, context, first)
        values["expires_at"] = connection.execute("SELECT clock_timestamp()+interval '600 milliseconds'").fetchone()[0]
        insert_token(connection, values)
    with token_runtime(context, first, "sealEvidence") as connection:
        assert connection.execute("SELECT now()<%s", (values["expires_at"],)).fetchone() == (True,)
        connection.execute("SELECT pg_sleep(0.8)")
        assert connection.execute(
            "SELECT now()<%s,clock_timestamp()>=%s", (values["expires_at"], values["expires_at"])
        ).fetchone() == (True, True)
        with pytest.raises(psycopg.errors.CheckViolation, match="expired"):
            with connection.transaction():
                connection.execute(
                    "UPDATE mt.operation_token SET consumed_at=clock_timestamp(),row_version=row_version+1 WHERE token_id=%s",
                    (values["token_id"],),
                )
        assert connection.execute(
            "SELECT consumed_at,row_version FROM mt.operation_token WHERE token_id=%s", (values["token_id"],)
        ).fetchone() == (None, 1)


def seed_legacy(connection):
    org, actor, case, approval, token = [uuid4() for _ in range(5)]
    connection.execute("INSERT INTO mt.organizations(org_id,name) VALUES(%s,'self-owned legacy')", (org,))
    connection.execute(
        "INSERT INTO mt.users(user_id,org_id,subject,enabled) VALUES(%s,%s,'self-owned legacy',true)", (actor, org)
    )
    connection.execute(
        "INSERT INTO mt.cases(case_id,org_id,display_code,status) VALUES(%s,%s,'legacy','ACTIVE')", (case, org)
    )
    connection.execute(
        "INSERT INTO mt.approval_request(approval_id,org_id,case_id,object_type,object_id,object_version,purpose,policy_version,requested_by,state,reason,run_version,result_version) VALUES(%s,%s,%s,'task',%s,1,'seal','self-owned-1',%s,'APPROVED','migration fixture only',1,1)",
        (approval, org, case, uuid4(), actor),
    )
    connection.execute(
        "INSERT INTO mt.operation_token(token_id,org_id,case_id,approval_id,actor_id,purpose,object_id,object_version,token_sha256,expires_at) SELECT %s,org_id,case_id,approval_id,requested_by,purpose,object_id,object_version,%s,now()+interval '1 hour' FROM mt.approval_request WHERE approval_id=%s",
        (token, "a" * 64, approval),
    )
    return token


def test_0011_preserves_legacy_rows_and_original_migration_checksums(fresh_scope_database, tmp_path):
    dsn = fresh_scope_database
    previous = copied_migrations(tmp_path / "through10", 10)
    assert len(apply_migrations(dsn, previous)) == 10
    with psycopg.connect(dsn) as admin:
        token = seed_legacy(admin)
    assert apply_migrations(dsn, MIGRATIONS) == ["0011", "0012", "0013", "0014", "0015", "0016", "0017"], (
        "T016_INCREMENTAL_TOKEN_MIGRATION_REQUIRED"
    )
    assert apply_migrations(dsn, MIGRATIONS) == []
    with psycopg.connect(dsn) as admin:
        assert admin.execute(
            "SELECT storage_version,consumed_at,action,key_id FROM mt.operation_token WHERE token_id=%s", (token,)
        ).fetchone() == (0, None, None, None)
        assert admin.execute(
            "SELECT count(*) FROM information_schema.columns WHERE table_schema='mt' AND table_name='operation_token'"
        ).fetchone() == (27,)
        assert admin.execute(
            "SELECT version,sha256 FROM mt_meta.schema_migrations WHERE version<='0010' ORDER BY version"
        ).fetchall() == [
            (file.name[:4], hashlib.sha256(file.read_bytes()).hexdigest()) for file in sorted(previous.glob("*.sql"))
        ]
        with pytest.raises(psycopg.errors.CheckViolation):
            admin.execute("UPDATE mt.operation_token SET consumed_at=clock_timestamp() WHERE token_id=%s", (token,))


def test_0011_partial_failure_rolls_back_new_columns_and_scope_catalog(fresh_scope_database, tmp_path):
    dsn = fresh_scope_database
    previous = copied_migrations(tmp_path / "through10", 10)
    apply_migrations(dsn, previous)
    candidate = MIGRATIONS / "0011_operation_token.sql"
    assert candidate.is_file(), "T016_INCREMENTAL_TOKEN_MIGRATION_REQUIRED"
    failed = copied_migrations(tmp_path / "failed", 11)
    (failed / candidate.name).write_bytes(candidate.read_bytes() + b"\nSELECT mt.self_owned_t016_missing();\n")
    with pytest.raises(psycopg.Error):
        apply_migrations(dsn, failed)
    with psycopg.connect(dsn) as admin:
        assert admin.execute("SELECT count(*) FROM mt_meta.schema_migrations").fetchone() == (10,)
        assert admin.execute(
            "SELECT count(*) FROM information_schema.columns WHERE table_schema='mt' AND column_name='storage_version'"
        ).fetchone() == (0,)
        assert admin.execute("SELECT mt.scope_lookup_kind_allowed('approval','issueOperationToken')").fetchone() == (
            False,
        )
