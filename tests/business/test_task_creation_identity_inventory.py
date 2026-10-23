"""Read actual directory rows without creating adoption or authenticating a person."""

import importlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from uuid import UUID, uuid4

import psycopg
import pytest
from business_app.db import Database
from business_app.identity.directory import IdentityDirectory
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from sqlalchemy import text


def module():
    assert importlib.util.find_spec("business_app.task_creation_identity_inventory") is not None, (
        "T034 explicit read-only identity inventory is not implemented"
    )
    return importlib.import_module("business_app.task_creation_identity_inventory")


def request(**changes):
    value = dict(
        issuer="https://identity.example.test",
        subject="self-owned-subject",
        user_id=uuid4(),
        org_id=uuid4(),
        case_id=uuid4(),
    )
    value.update(changes)
    return module().IdentityInventoryRequest(**value)


def test_read_only_inventory_component_exists_without_default_adoption():
    assert callable(module().observe_identity_inventory)
    assert request().subject == "self-owned-subject"


@pytest.mark.parametrize(
    "field,value",
    [
        ("issuer", ""),
        ("issuer", " https://identity.example.test"),
        ("subject", "bad\nsubject"),
        ("subject", None),
        ("subject", "x" * 1025),
        ("issuer", "x" * 2049),
        ("user_id", "00000000-0000-0000-0000-000000000001"),
        ("org_id", None),
        ("case_id", True),
        ("user_id", UUID(int=0)),
    ],
)
def test_inventory_requires_explicit_exact_identity_and_scope(field, value):
    with pytest.raises(ValueError, match="TASK_IDENTITY_INVENTORY_INVALID"):
        request(**{field: value})


@pytest.fixture
def inventory_environment(business_context):
    c = business_context
    role, password = "mt_inventory_test_" + uuid4().hex, uuid4().hex + uuid4().hex
    with psycopg.connect(c["admin_dsn"]) as admin:
        admin.execute(
            sql.SQL("CREATE ROLE {} LOGIN NOSUPERUSER NOBYPASSRLS PASSWORD {}").format(
                sql.Identifier(role), sql.Literal(password)
            )
        )
        admin.execute(sql.SQL("GRANT mt_directory_manager TO {}").format(sql.Identifier(role)))
    database = Database(make_conninfo(c["admin_dsn"], user=role, password=password))
    query = request(user_id=c["actor"].user_id, org_id=c["actor"].org_id, case_id=c["case_id"])
    with database.engine.begin() as connection:
        IdentityDirectory(connection).bind_identity(
            user_id=query.user_id,
            org_id=query.org_id,
            issuer=query.issuer,
            subject=query.subject,
            mapping_version="self-owned-test-v1",
            enabled=True,
        )
    try:
        yield dict(context=c, database=database, request=query, role=role, password=password)
    finally:
        database.close()
        with psycopg.connect(c["admin_dsn"]) as admin:
            admin.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
            admin.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))


def test_real_directory_inventory_is_observation_not_authentication_or_adoption(inventory_environment):
    e = inventory_environment
    observed = module().observe_identity_inventory(e["database"], e["request"])
    value = observed.as_dict()
    assert value["status"] == "IDENTITY_MEMBERSHIP_OBSERVED_NOT_ADOPTED"
    assert value["external_authentication_verified"] is False and value["adoption_authorized"] is False
    assert value["license_verified"] is False and value["classification_verified"] is False
    assert value["active_mapping_created"] is False and value["database_written"] is False
    assert value["binding"]["user_id"] == str(e["request"].user_id)
    assert value["binding"]["org_id"] == str(e["request"].org_id)
    assert value["binding"]["case_id"] == str(e["request"].case_id)
    assert value["database"]["database_name"] == conninfo_to_dict(e["context"]["admin_dsn"])["dbname"]
    assert value["database"]["database_oid"] > 0
    assert value["transaction_read_only"] is True
    value["binding"]["user_id"] = "changed"
    assert observed.as_dict()["binding"]["user_id"] == str(e["request"].user_id)
    with psycopg.connect(e["context"]["admin_dsn"]) as admin:
        count = admin.execute("SELECT count(*) FROM mt.task_plan_mapping_head").fetchone()
        assert count is not None and count[0] == 0


@pytest.mark.parametrize("field", ["issuer", "subject", "user_id", "org_id", "case_id"])
def test_mismatched_identity_or_scope_is_not_inventoried_as_current(inventory_environment, field):
    from dataclasses import replace

    e = inventory_environment
    wrong = "other" if field in {"issuer", "subject"} else uuid4()
    result = module().observe_identity_inventory(e["database"], replace(e["request"], **{field: wrong})).as_dict()
    assert result["status"] == "DIRECTORY_BINDING_NOT_CURRENT"
    assert result["binding"] is None
    assert result["adoption_authorized"] is False


@pytest.mark.parametrize(
    "state", ["identity", "expired_identity", "user", "organization", "case", "membership", "expired_membership"]
)
def test_disabled_revoked_and_expired_directory_records_remain_blocked(inventory_environment, state):
    e = inventory_environment
    q = e["request"]
    queries = {
        "identity": ("UPDATE mt.user_identities SET enabled=false,revoked_at=now() WHERE user_id=%s", q.user_id),
        "expired_identity": (
            "UPDATE mt.user_identities SET expires_at=now()-interval '1 second' WHERE user_id=%s",
            q.user_id,
        ),
        "user": ("UPDATE mt.users SET enabled=false WHERE user_id=%s", q.user_id),
        "organization": ("UPDATE mt.organizations SET enabled=false WHERE org_id=%s", q.org_id),
        "case": ("UPDATE mt.cases SET status='ARCHIVED' WHERE case_id=%s", q.case_id),
        "membership": ("UPDATE mt.case_membership SET revoked_at=now() WHERE user_id=%s", q.user_id),
        "expired_membership": (
            "UPDATE mt.case_membership SET expires_at=now()-interval '1 second' WHERE user_id=%s",
            q.user_id,
        ),
    }
    command, identifier = queries[state]
    with psycopg.connect(e["context"]["admin_dsn"]) as admin:
        admin.execute(command, (identifier,))
    value = module().observe_identity_inventory(e["database"], q).as_dict()
    assert value["status"] == "DIRECTORY_BINDING_NOT_CURRENT" and value["binding"] is None


def test_inventory_rejects_runtime_or_superuser_connections(inventory_environment):
    e = inventory_environment
    for dsn in (e["context"]["settings"].database_dsn, e["context"]["admin_dsn"]):
        database = Database(dsn)
        try:
            with pytest.raises(ValueError, match="TASK_IDENTITY_INVENTORY_UNAVAILABLE"):
                module().observe_identity_inventory(database, e["request"])
        finally:
            database.close()


@pytest.mark.parametrize("field", ["issuer", "subject"])
def test_identifier_text_is_bound_as_data_never_as_sql(inventory_environment, field):
    from dataclasses import replace

    e = inventory_environment
    query = replace(e["request"], **{field: "self-owned' OR true --"})
    value = module().observe_identity_inventory(e["database"], query).as_dict()
    assert value["status"] == "DIRECTORY_BINDING_NOT_CURRENT" and value["binding"] is None


def test_manager_with_runtime_membership_is_refused(inventory_environment):
    e = inventory_environment
    with psycopg.connect(e["context"]["admin_dsn"]) as admin:
        admin.execute(sql.SQL("GRANT mt_runtime TO {}").format(sql.Identifier(e["role"])))
    with pytest.raises(ValueError, match="TASK_IDENTITY_INVENTORY_UNAVAILABLE"):
        module().observe_identity_inventory(e["database"], e["request"])


def test_set_role_cannot_hide_operator_database_login(inventory_environment):
    from sqlalchemy import event

    e = inventory_environment
    database = Database(make_conninfo(e["context"]["admin_dsn"], user=e["role"], password=e["password"]))

    def switch_role(dbapi, record):
        old = dbapi.autocommit
        dbapi.autocommit = True
        try:
            dbapi.execute("SET ROLE mt_directory_manager")
        finally:
            dbapi.autocommit = old

    event.listen(database.engine, "connect", switch_role)
    try:
        with database.engine.begin() as connection:
            assert connection.execute(text("SELECT current_user<>session_user")).scalar_one() is True
        with pytest.raises(ValueError, match="TASK_IDENTITY_INVENTORY_UNAVAILABLE"):
            module().observe_identity_inventory(database, e["request"])
    finally:
        database.close()


@pytest.mark.parametrize("attribute", ["BYPASSRLS", "CREATEROLE", "CREATEDB", "REPLICATION"])
def test_elevated_manager_login_is_refused(inventory_environment, attribute):
    e = inventory_environment
    with psycopg.connect(e["context"]["admin_dsn"]) as admin:
        admin.execute(sql.SQL("ALTER ROLE {} {}").format(sql.Identifier(e["role"]), sql.SQL(attribute)))
    with pytest.raises(ValueError, match="TASK_IDENTITY_INVENTORY_UNAVAILABLE"):
        module().observe_identity_inventory(e["database"], e["request"])


def test_inventory_enforces_read_only_and_preserves_supplied_database_settings(inventory_environment):
    from sqlalchemy import event

    e = inventory_environment
    statements = []

    def inspect(connection, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    event.listen(e["database"].engine, "before_cursor_execute", inspect)
    module().observe_identity_inventory(e["database"], e["request"])
    assert statements[0] == "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"
    assert not any(
        command.lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE", "GRANT", "CREATE")) for command in statements
    )
    with e["database"].engine.begin() as connection:
        assert connection.execute(text("SHOW transaction_read_only")).scalar_one() == "off"


def test_private_cli_writes_only_new_private_observation_and_no_authority(inventory_environment, tmp_path, capsys):
    from scripts.task_creation_identity_inventory import main

    e = inventory_environment
    folder = tmp_path / "private"
    folder.mkdir(mode=0o700)
    configuration = folder / "inventory-input.json"
    q = e["request"]
    configuration.write_text(
        json.dumps(
            dict(
                database_dsn=make_conninfo(e["context"]["admin_dsn"], user=e["role"], password=e["password"]),
                issuer=q.issuer,
                subject=q.subject,
                user_id=str(q.user_id),
                org_id=str(q.org_id),
                case_id=str(q.case_id),
            )
        )
    )
    configuration.chmod(0o600)
    output = folder / "observation"
    assert main(["--private-configuration", str(configuration), "--output", str(output)]) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["adoption_authorized"] is False and summary["database_written"] is False
    assert e["password"] not in json.dumps(summary) and q.subject not in json.dumps(summary)
    artifact = output / "identity-directory-observation.json"
    before = artifact.read_bytes()
    assert artifact.stat().st_mode & 0o777 == 0o600 and output.stat().st_mode & 0o777 == 0o700
    assert main(["--private-configuration", str(configuration), "--output", str(output)]) == 1
    assert artifact.read_bytes() == before
    assert json.loads(capsys.readouterr().out)["status"] == "TASK_IDENTITY_INVENTORY_BLOCKED_OR_UNAVAILABLE"


@pytest.mark.parametrize(
    "kind", ["missing", "wide_permissions", "duplicate", "extra", "malformed", "repository_output"]
)
def test_cli_rejects_private_input_errors_without_leaking_values(tmp_path, capsys, monkeypatch, kind):
    from scripts.task_creation_identity_inventory import main

    folder = tmp_path / "custody"
    folder.mkdir(mode=0o700)
    configuration = folder / "private.json"
    raw = json.dumps(
        dict(
            database_dsn="host=127.0.0.1 dbname=mt_business_not_real password=not-a-real-password",
            issuer="https://identity.example.test",
            subject="private-subject",
            user_id=str(uuid4()),
            org_id=str(uuid4()),
            case_id=str(uuid4()),
        )
    )
    database_calls = []

    def forbidden_database(*args, **kwargs):
        database_calls.append(True)
        raise AssertionError("Invalid private input must be rejected before any database connection")

    monkeypatch.setattr("business_app.db.Database", forbidden_database)
    if kind == "duplicate":
        raw = '{"subject":"private-subject","subject":"another"}'
    elif kind == "extra":
        raw = '{"approved":true,"database_dsn":"not-a-real-password"}'
    elif kind == "malformed":
        raw = "private-invalid-json"
    if kind != "missing":
        configuration.write_text(raw)
        configuration.chmod(0o644 if kind == "wide_permissions" else 0o600)
    output = (
        Path(__file__).resolve().parents[2] / "must-not-be-created-in-repository"
        if kind == "repository_output"
        else folder / "output"
    )
    assert main(["--private-configuration", str(configuration), "--output", str(output)]) == 1
    text_output = capsys.readouterr().out
    assert "not-a-real-password" not in text_output and "private-subject" not in text_output
    assert json.loads(text_output)["adoption_authorized"] is False and not output.exists()
    assert database_calls == []


def test_standalone_cli_help_does_not_require_inherited_pythonpath(tmp_path):
    script = Path(__file__).resolve().parents[2] / "scripts/task_creation_identity_inventory.py"
    result = subprocess.run(
        [sys.executable, str(script), "--help"],
        cwd=tmp_path,
        env={key: value for key, value in os.environ.items() if key != "PYTHONPATH"},
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0
    assert "--private-configuration" in result.stdout and "Traceback" not in result.stderr
