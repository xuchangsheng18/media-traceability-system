"""Identity mapping and tenant relationships tested against real isolated PostgreSQL."""

import importlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.exc import DBAPIError


def identity_module():
    assert (Path(__file__).resolve().parents[2] / "backend/business_app/identity/directory.py").is_file(), (
        "T012 identity directory is not implemented"
    )
    return importlib.import_module("business_app.identity.directory")


@pytest.fixture
def directory(business_context):
    ctx = business_context
    module = identity_module()
    settings = conninfo_to_dict(ctx["admin_dsn"])
    role = "mt_identity_test_" + uuid4().hex
    secret = uuid4().hex + uuid4().hex
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            sql.SQL("CREATE ROLE {} LOGIN NOSUPERUSER NOBYPASSRLS PASSWORD {}").format(
                sql.Identifier(role), sql.Literal(secret)
            )
        )
        admin.execute(sql.SQL("GRANT mt_directory_manager,mt_identity_lookup TO {}").format(sql.Identifier(role)))
    engine = create_engine(
        URL.create(
            "postgresql+psycopg",
            username=role,
            password=secret,
            host=str(settings["host"]),
            port=int(str(settings["port"])),
            database=str(settings["dbname"]),
        )
    )
    try:
        with engine.begin() as connection:
            yield module.IdentityDirectory(connection), ctx
    finally:
        engine.dispose()
        with psycopg.connect(ctx["admin_dsn"]) as admin:
            admin.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
            admin.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))


def bind(d, ctx, **changes):
    args = dict(
        user_id=ctx["actor"].user_id,
        org_id=ctx["actor"].org_id,
        issuer="https://identity.example.test/one",
        subject="synthetic-subject",
        mapping_version="test-mapping-v1",
        enabled=True,
        expires_at=None,
    )
    args.update(changes)
    return d.bind_identity(**args)


def test_same_subject_from_different_issuers_maps_to_distinct_users(directory):
    d, ctx = directory
    first = bind(d, ctx)
    second = bind(
        d,
        ctx,
        user_id=ctx["other_actor"].user_id,
        org_id=ctx["other_actor"].org_id,
        issuer="https://identity.example.test/two",
    )
    assert first != second
    assert d.resolve("https://identity.example.test/one", "synthetic-subject").user_id == ctx["actor"].user_id
    assert d.resolve("https://identity.example.test/two", "synthetic-subject").user_id == ctx["other_actor"].user_id


@pytest.mark.parametrize(
    "state", ["default_disabled", "expired", "revoked", "disabled_user", "disabled_org", "unknown"]
)
def test_inactive_or_unmapped_identity_never_resolves(directory, state):
    d, ctx = directory
    identity_id = bind(
        d,
        ctx,
        enabled=state != "default_disabled",
        expires_at=datetime.now(timezone.utc) - timedelta(seconds=1) if state == "expired" else None,
    )
    if state == "revoked":
        d.revoke_identity(identity_id, expected_version=1)
    elif state == "disabled_user":
        d.disable_user(ctx["actor"].user_id, expected_version=1)
    elif state == "disabled_org":
        d.disable_organization(ctx["actor"].org_id, expected_version=1)
    with pytest.raises(Exception) as failure:
        d.resolve("https://identity.example.test/one", "unknown" if state == "unknown" else "synthetic-subject")
    assert str(failure.value) == "AUTHENTICATION_REQUIRED"


def test_revoke_retains_external_identity_and_prevents_rebinding(directory):
    d, ctx = directory
    identity_id = bind(d, ctx)
    d.revoke_identity(identity_id, expected_version=1)
    with pytest.raises(Exception) as failure:
        bind(d, ctx, user_id=ctx["other_actor"].user_id, org_id=ctx["other_actor"].org_id)
    assert str(failure.value) == "DIRECTORY_CONFLICT"
    assert d.identity_state(identity_id) == (False, True, 2)


@pytest.mark.parametrize(
    "field,value", [("issuer", ""), ("issuer", " leading"), ("subject", " "), ("mapping_version", "")]
)
def test_invalid_external_keys_rejected_without_writing(directory, field, value):
    d, ctx = directory
    with pytest.raises(Exception) as failure:
        bind(d, ctx, **{field: value})
    assert str(failure.value) == "DIRECTORY_INPUT_INVALID"


def test_cross_organization_mapping_and_membership_rejected(directory):
    d, ctx = directory
    with pytest.raises(Exception) as failure:
        bind(d, ctx, org_id=ctx["other_actor"].org_id)
    assert str(failure.value) == "DIRECTORY_RELATION_INVALID"
    with pytest.raises(Exception) as failure:
        d.add_membership(ctx["actor"].user_id, ctx["other_actor"].org_id, ctx["other_case_id"])
    assert str(failure.value) == "DIRECTORY_RELATION_INVALID"


def test_optimistic_version_prevents_overwriting_revocation(directory):
    d, ctx = directory
    identity_id = bind(d, ctx)
    d.revoke_identity(identity_id, expected_version=1)
    with pytest.raises(Exception) as failure:
        d.revoke_identity(identity_id, expected_version=1)
    assert str(failure.value) == "DIRECTORY_VERSION_CONFLICT"
    assert d.identity_state(identity_id) == (False, True, 2)


def test_new_user_is_disabled_and_no_mapping_is_inferred_from_legacy_subject(directory):
    d, ctx = directory
    org_id = d.create_organization("synthetic-new-unit")
    user_id = d.create_user(org_id, "internal-label-only")
    case_id = d.create_case(org_id, "synthetic-case")
    d.add_membership(user_id, org_id, case_id)
    with pytest.raises(Exception) as failure:
        d.resolve("unconfigured-provider", "internal-label-only")
    assert str(failure.value) == "AUTHENTICATION_REQUIRED"
    assert d.user_state(user_id) == (org_id, False, 1)


def test_runtime_role_cannot_provision_identities_or_call_lookup(business_context):
    module = identity_module()
    from sqlalchemy import text

    ctx = business_context
    with ctx["database"].identity_transaction(ctx["actor"]) as connection:
        with pytest.raises(Exception) as failure:
            module.IdentityDirectory(connection).create_organization("unauthorized")
        assert str(failure.value) == "DIRECTORY_MANAGEMENT_FORBIDDEN"
    with ctx["database"].identity_transaction(ctx["actor"]) as connection:
        with pytest.raises(Exception):
            connection.execute(text("SELECT * FROM mt.resolve_identity('unknown','unknown')"))


@pytest.mark.parametrize("target", ["user_org", "case_org", "identity_subject", "identity_user"])
def test_database_rejects_identity_or_tenant_key_reassignment(directory, target):
    d, ctx = directory
    identity_id = bind(d, ctx)
    statements = {
        "user_org": (
            "UPDATE mt.users SET org_id=%s WHERE user_id=%s",
            (ctx["other_actor"].org_id, ctx["actor"].user_id),
        ),
        "case_org": ("UPDATE mt.cases SET org_id=%s WHERE case_id=%s", (ctx["other_actor"].org_id, ctx["case_id"])),
        "identity_subject": (
            "UPDATE mt.user_identities SET subject='replacement' WHERE identity_id=%s",
            (identity_id,),
        ),
        "identity_user": (
            "UPDATE mt.user_identities SET user_id=%s,org_id=%s WHERE identity_id=%s",
            (ctx["other_actor"].user_id, ctx["other_actor"].org_id, identity_id),
        ),
    }
    # Test the database guard directly; the DAO does not expose these operations.
    from sqlalchemy import text

    query, values = statements[target]
    converted = query
    arguments = {}
    for number, value in enumerate(values):
        converted = converted.replace("%s", ":v" + str(number), 1)
        arguments["v" + str(number)] = value
    with pytest.raises(DBAPIError) as failure:
        with d.connection.begin_nested():
            d.connection.execute(text(converted), arguments)
    assert getattr(failure.value.orig, "sqlstate", None) == "55000"


def test_organization_disable_blocks_existing_case_rls(business_context):
    identity_module()
    ctx = business_context
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute("UPDATE mt.organizations SET enabled=false WHERE org_id=%s", (ctx["actor"].org_id,))
    with pytest.raises(Exception) as failure:
        with ctx["database"].transaction(
            __import__("business_app.types", fromlist=["Scope"]).Scope(ctx["actor"], ctx["case_id"])
        ):
            pass
    assert str(failure.value) == "CASE_NOT_FOUND"


def test_expiry_rechecked_in_the_same_open_transaction(directory):
    from sqlalchemy import text

    d, ctx = directory
    bind(d, ctx, expires_at=datetime.now(timezone.utc) + timedelta(seconds=0.4))
    assert d.resolve("https://identity.example.test/one", "synthetic-subject").user_id == ctx["actor"].user_id
    d.connection.execute(text("SELECT pg_sleep(0.6)"))
    with pytest.raises(Exception) as failure:
        d.resolve("https://identity.example.test/one", "synthetic-subject")
    assert str(failure.value) == "AUTHENTICATION_REQUIRED"


def test_lookup_role_can_resolve_but_cannot_read_or_manage_directory(directory):
    from sqlalchemy import text

    d, ctx = directory
    bind(d, ctx)
    d.connection.execute(text("SET LOCAL ROLE mt_identity_lookup"))
    assert d.resolve("https://identity.example.test/one", "synthetic-subject").org_id == ctx["actor"].org_id
    with pytest.raises(DBAPIError) as failure:
        with d.connection.begin_nested():
            d.connection.execute(text("SELECT * FROM mt.user_identities"))
    assert getattr(failure.value.orig, "sqlstate", None) == "42501"
    with pytest.raises(Exception) as forbidden:
        d.disable_user(ctx["actor"].user_id, expected_version=1)
    assert str(forbidden.value) == "DIRECTORY_MANAGEMENT_FORBIDDEN"


def test_membership_and_role_revocation_are_versioned_and_terminal(directory):
    from sqlalchemy import text

    d, ctx = directory
    role_id, binding_id = uuid4(), uuid4()
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            "INSERT INTO mt.roles(role_id,code,description) VALUES(%s,%s,'synthetic')", (role_id, str(role_id))
        )
    membership_id = d.connection.execute(
        text("SELECT membership_id FROM mt.case_membership WHERE user_id=:user"), {"user": ctx["actor"].user_id}
    ).scalar_one()
    d.connection.execute(
        text("INSERT INTO mt.user_roles(user_role_id,user_id,role_id) VALUES(:id,:user,:role)"),
        {"id": binding_id, "user": ctx["actor"].user_id, "role": role_id},
    )
    d.revoke_membership(membership_id, expected_version=1)
    d.revoke_role(binding_id, expected_version=1)
    assert d.connection.execute(
        text("SELECT revoked_at IS NOT NULL,row_version FROM mt.case_membership WHERE membership_id=:id"),
        {"id": membership_id},
    ).one() == (True, 2)
    assert d.connection.execute(
        text("SELECT revoked_at IS NOT NULL,row_version FROM mt.user_roles WHERE user_role_id=:id"), {"id": binding_id}
    ).one() == (True, 2)
    for method, identifier in [(d.revoke_membership, membership_id), (d.revoke_role, binding_id)]:
        with pytest.raises(Exception) as failure:
            method(identifier, expected_version=1)
        assert str(failure.value) == "DIRECTORY_VERSION_CONFLICT"


@pytest.mark.parametrize(
    "field,value",
    [
        ("issuer", "https://identity.example.test/ONE"),
        ("issuer", "https://identity.example.test/one/"),
        ("subject", "Synthetic-subject"),
    ],
)
def test_identity_comparison_does_not_normalize_distinct_keys(directory, field, value):
    d, ctx = directory
    bind(d, ctx)
    lookup = {"issuer": "https://identity.example.test/one", "subject": "synthetic-subject", field: value}
    with pytest.raises(Exception) as failure:
        d.resolve(**lookup)
    assert str(failure.value) == "AUTHENTICATION_REQUIRED"


def test_naive_expiry_is_rejected_before_persistence(directory):
    d, ctx = directory
    with pytest.raises(Exception) as failure:
        bind(d, ctx, expires_at=datetime(2026, 10, 16))
    assert str(failure.value) == "DIRECTORY_INPUT_INVALID"
