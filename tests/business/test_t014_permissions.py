"""T014 facts and explicit policy on real, isolated PostgreSQL; no formal grants."""

import importlib
import time
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import psycopg
import pytest
from business_app.db import Database
from business_app.errors import BusinessError
from business_app.permissions.types import Principal
from business_app.types import Actor
from psycopg import sql
from psycopg.conninfo import make_conninfo

ROOT = Path(__file__).resolve().parents[2]


def permission_module(name):
    assert (ROOT / f"backend/business_app/permissions/{name}.py").is_file(), f"T014 {name} is missing"
    return importlib.import_module("business_app.permissions." + name)


@pytest.fixture
def permission_context(business_context):
    ctx = business_context
    role, permission, relation, binding, identity = [uuid4() for _ in range(5)]
    login, password = "mt_permission_test_" + uuid4().hex, uuid4().hex + uuid4().hex
    principal = Principal(
        ctx["actor"],
        "https://identity.example.test",
        "permission-subject",
        int(time.time()) + 600,
    )
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            sql.SQL("CREATE ROLE {} LOGIN NOSUPERUSER NOBYPASSRLS PASSWORD {}").format(
                sql.Identifier(login), sql.Literal(password)
            )
        )
        if admin.execute("SELECT 1 FROM pg_roles WHERE rolname='mt_permission_lookup'").fetchone():
            admin.execute(sql.SQL("GRANT mt_permission_lookup TO {}").format(sql.Identifier(login)))
        admin.execute(
            "INSERT INTO mt.user_identities(identity_id,user_id,org_id,issuer,subject,mapping_version,enabled) VALUES(%s,%s,%s,%s,%s,'fixture-map-v1',true)",
            (
                identity,
                principal.actor.user_id,
                principal.actor.org_id,
                principal.issuer,
                principal.subject,
            ),
        )
        admin.execute(
            "INSERT INTO mt.roles(role_id,code,description,enabled) VALUES(%s,'fixture.role','fixture',true)",
            (role,),
        )
        admin.execute(
            "INSERT INTO mt.permissions(permission_id,code,description,enabled) VALUES(%s,'identity.read','fixture',true)",
            (permission,),
        )
        admin.execute(
            "INSERT INTO mt.role_permissions(role_permission_id,role_id,permission_id) VALUES(%s,%s,%s)",
            (relation, role, permission),
        )
        admin.execute(
            "INSERT INTO mt.user_roles(user_role_id,user_id,role_id) VALUES(%s,%s,%s)",
            (binding, principal.actor.user_id, role),
        )
    lookup = Database(make_conninfo(ctx["admin_dsn"], user=login, password=password))
    try:
        yield dict(
            ctx,
            lookup=lookup,
            principal=principal,
            role=role,
            permission=permission,
            relation=relation,
            binding=binding,
            identity=identity,
            login=login,
        )
    finally:
        lookup.close()
        with psycopg.connect(ctx["admin_dsn"]) as admin:
            admin.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(login)))
            admin.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(login)))


def reader(ctx):
    return permission_module("directory").PermissionDirectory(ctx["lookup"])


def test_permission_lookup_role_cannot_read_or_write_catalog(permission_context):
    ctx = permission_context
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        row = admin.execute(
            "SELECT rolcanlogin,rolsuper,rolbypassrls,rolcreaterole,rolcreatedb,rolreplication FROM pg_roles WHERE rolname='mt_permission_lookup'"
        ).fetchone()
        assert row == (False,) * 6, "T014 least-privilege group role is missing or unsafe"
        function = admin.execute(
            "SELECT prosecdef,proconfig FROM pg_proc WHERE oid=to_regprocedure('mt.lookup_permission(text,text,uuid,uuid,text)')"
        ).fetchone()
        assert function == (True, ["search_path=pg_catalog, mt, pg_temp"])
        assert admin.execute(
            "SELECT count(*) FROM pg_proc p CROSS JOIN LATERAL aclexplode(p.proacl) a WHERE p.oid='mt.lookup_permission(text,text,uuid,uuid,text)'::regprocedure AND a.grantee=0"
        ).fetchone() == (0,)
    with ctx["lookup"].engine.begin() as connection:
        from sqlalchemy import text

        assert (
            connection.execute(
                text("SELECT mt.lookup_permission(:issuer,:subject,:user,:org,'identity.read')"),
                dict(
                    issuer=ctx["principal"].issuer,
                    subject=ctx["principal"].subject,
                    user=ctx["actor"].user_id,
                    org=ctx["actor"].org_id,
                ),
            ).fetchone()
            is not None
        )
    values = make_conninfo(ctx["admin_dsn"], options="-crole=" + ctx["login"])
    for table in (
        "user_identities",
        "users",
        "organizations",
        "roles",
        "permissions",
        "user_roles",
        "role_permissions",
    ):
        for action in ("SELECT * FROM", "DELETE FROM", "TRUNCATE"):
            with psycopg.connect(values) as connection:
                with pytest.raises(psycopg.errors.InsufficientPrivilege):
                    connection.execute(f"{action} mt.{table}")


@pytest.mark.parametrize("field", ["issuer", "subject", "user", "org"])
def test_permission_lookup_rejects_mismatched_identity_or_unit(permission_context, field):
    ctx = permission_context
    principal = ctx["principal"]
    if field == "issuer":
        principal = replace(principal, issuer=principal.issuer.upper())
    elif field == "subject":
        principal = replace(principal, subject=principal.subject.upper())
    elif field == "user":
        principal = replace(principal, actor=Actor(ctx["other_actor"].user_id, principal.actor.org_id))
    else:
        principal = replace(principal, actor=Actor(principal.actor.user_id, ctx["other_actor"].org_id))
    with pytest.raises(BusinessError) as caught:
        reader(ctx).read(principal, "identity.read")
    assert (caught.value.code, caught.value.http_status) == (
        "AUTHENTICATION_REQUIRED",
        401,
    )


@pytest.mark.parametrize(
    "state",
    [
        "role_disabled",
        "permission_disabled",
        "role_revoked",
        "permission_revoked",
        "role_expired",
    ],
)
def test_revoked_or_expired_binding_is_ineligible(permission_context, state):
    ctx = permission_context
    lookup = reader(ctx)
    before = lookup.read(ctx["principal"], "identity.read")
    assert before.eligible is True
    assert lookup.read(ctx["principal"], "identity.read").version_digest == before.version_digest
    queries = {
        "role_disabled": (
            "UPDATE mt.roles SET enabled=false WHERE role_id=%s",
            ctx["role"],
        ),
        "permission_disabled": (
            "UPDATE mt.permissions SET enabled=false WHERE permission_id=%s",
            ctx["permission"],
        ),
        "role_revoked": (
            "UPDATE mt.user_roles SET revoked_at=statement_timestamp() WHERE user_role_id=%s",
            ctx["binding"],
        ),
        "permission_revoked": (
            "UPDATE mt.role_permissions SET revoked_at=statement_timestamp() WHERE role_permission_id=%s",
            ctx["relation"],
        ),
        "role_expired": (
            "UPDATE mt.user_roles SET expires_at=statement_timestamp() WHERE user_role_id=%s",
            ctx["binding"],
        ),
    }
    query, identifier = queries[state]
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(query, (identifier,))
    after = lookup.read(ctx["principal"], "identity.read")
    assert after.eligible is False
    assert after.version_digest != before.version_digest


@pytest.mark.parametrize("state", ["identity_revoked", "identity_expired", "user_disabled", "org_disabled"])
def test_permission_read_rechecks_live_identity_and_organization(permission_context, state):
    ctx = permission_context
    lookup = reader(ctx)
    assert lookup.read(ctx["principal"], "identity.read").eligible is True
    query, identifier = {
        "identity_revoked": (
            "UPDATE mt.user_identities SET enabled=false,revoked_at=statement_timestamp() WHERE identity_id=%s",
            ctx["identity"],
        ),
        "identity_expired": (
            "UPDATE mt.user_identities SET expires_at=statement_timestamp() WHERE identity_id=%s",
            ctx["identity"],
        ),
        "user_disabled": (
            "UPDATE mt.users SET enabled=false WHERE user_id=%s",
            ctx["actor"].user_id,
        ),
        "org_disabled": (
            "UPDATE mt.organizations SET enabled=false WHERE org_id=%s",
            ctx["actor"].org_id,
        ),
    }[state]
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(query, (identifier,))
    with pytest.raises(BusinessError) as caught:
        lookup.read(ctx["principal"], "identity.read")
    assert caught.value.http_status == 401


def test_role_expiry_equal_statement_timestamp_is_ineligible(permission_context):
    ctx = permission_context
    reader(ctx)  # Missing implementation must fail before any SQL-only check.
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            sql.SQL("""DO $check$
          DECLARE eligible boolean;
          BEGIN
            UPDATE mt.user_roles SET expires_at=statement_timestamp() WHERE user_role_id={binding};
            SELECT p.eligible INTO eligible FROM mt.lookup_permission({issuer},{subject},{user},{org},'identity.read') p;
            IF eligible IS DISTINCT FROM false THEN RAISE EXCEPTION 'EXPIRY_EQUALITY_ACCEPTED'; END IF;
          END $check$""").format(
                binding=sql.Literal(ctx["binding"]),
                issuer=sql.Literal(ctx["principal"].issuer),
                subject=sql.Literal(ctx["principal"].subject),
                user=sql.Literal(ctx["actor"].user_id),
                org=sql.Literal(ctx["actor"].org_id),
            )
        )


def test_permission_reader_refuses_privileged_connection(permission_context):
    ctx = permission_context
    module = permission_module("directory")
    database = Database(ctx["admin_dsn"])
    try:
        with pytest.raises(BusinessError) as caught:
            module.PermissionDirectory(database).read(ctx["principal"], "identity.read")
        assert caught.value.http_status == 503
    finally:
        database.close()


@pytest.mark.parametrize(
    "changed",
    ["actor", "org", "permission", "version", "digest", "truthy", "exception"],
)
def test_old_or_misbound_policy_decision_is_unavailable(permission_context, changed):
    ctx = permission_context
    policy_module = permission_module("policy")
    types = permission_module("types")
    lookup = reader(ctx)

    class Policy:
        version = "fixture-policy-v1"

        def decide(self, fact):
            decision = types.PermissionDecision(
                fact.principal.actor,
                fact.permission,
                True,
                self.version,
                fact.version_digest,
            )
            if changed == "exception":
                raise RuntimeError("fixture unavailable")
            return {
                "actor": replace(decision, actor=ctx["other_actor"]),
                "org": replace(
                    decision,
                    actor=Actor(ctx["actor"].user_id, ctx["other_actor"].org_id),
                ),
                "permission": replace(decision, permission="export.create"),
                "version": replace(decision, policy_version="fixture-policy-v0"),
                "digest": replace(decision, fact_digest="0" * 64),
                "truthy": replace(decision, allowed="yes"),
            }[changed]

    authority = policy_module.DirectoryPermissionAuthority(lookup, Policy())
    with pytest.raises(BusinessError) as caught:
        authority.check(ctx["principal"], "identity.read")
    assert caught.value.http_status == 503


def test_directory_facts_never_allow_without_explicit_policy(permission_context):
    ctx = permission_context
    policy_module = permission_module("policy")
    lookup = reader(ctx)
    assert lookup.read(ctx["principal"], "identity.read").eligible is True
    with pytest.raises(BusinessError) as caught:
        policy_module.DirectoryPermissionAuthority(lookup, None).check(ctx["principal"], "identity.read")
    assert (caught.value.code, caught.value.http_status) == (
        "FORMAL_POLICY_UNCONFIGURED",
        503,
    )


@pytest.mark.parametrize("allowed", [True, False])
def test_explicit_policy_is_exactly_bound_and_denial_has_generic_403(permission_context, allowed):
    ctx = permission_context
    types, policies = permission_module("types"), permission_module("policy")
    policy = SimpleNamespace(version="fixture-v1")
    policy.decide = lambda fact: types.PermissionDecision(
        fact.principal.actor,
        fact.permission,
        allowed,
        policy.version,
        fact.version_digest,
    )
    authority = policies.DirectoryPermissionAuthority(reader(ctx), policy)
    if allowed:
        assert authority.check(ctx["principal"], "identity.read") is None
    else:
        with pytest.raises(BusinessError) as caught:
            authority.check(ctx["principal"], "identity.read")
        assert (caught.value.code, caught.value.http_status) == (
            "PERMISSION_REQUIRED",
            403,
        )


@pytest.mark.parametrize("stage", ["reader", "policy"])
def test_expiry_during_permission_decision_is_rejected(permission_context, stage):
    ctx = permission_context
    types, policies = permission_module("types"), permission_module("policy")
    clock = [100]
    principal = replace(ctx["principal"], expires_at=200)
    policy = SimpleNamespace(version="fixture-v1")

    def read(current, permission):
        if stage == "reader":
            clock[0] = 200
        return types.PermissionFact(current, permission, True, "1" * 64)

    def decide(fact):
        clock[0] = 200
        return types.PermissionDecision(
            fact.principal.actor,
            fact.permission,
            True,
            policy.version,
            fact.version_digest,
        )

    policy.decide = decide
    authority = policies.DirectoryPermissionAuthority(SimpleNamespace(read=read), policy, clock=lambda: clock[0])
    with pytest.raises(BusinessError) as caught:
        authority.check(principal, "identity.read")
    assert (caught.value.code, caught.value.http_status) == (
        "AUTHENTICATION_REQUIRED",
        401,
    )


def test_permission_facts_and_least_privilege_survive_independent_restore(permission_context, tmp_path):
    from tests.business.test_recovery import pg_tool

    ctx = permission_context
    expected = reader(ctx).read(ctx["principal"], "identity.read")
    target_name = "mt_business_permission_restore_" + uuid4().hex
    restored_admin = make_conninfo(ctx["admin_dsn"], dbname=target_name)
    dump = tmp_path / "permission.dump"
    pg_tool("pg_dump", ctx["admin_dsn"], "-Fc", "--no-owner", "--file", str(dump))
    restored = None
    with psycopg.connect(ctx["admin_dsn"], autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {} TEMPLATE template0").format(sql.Identifier(target_name)))
        try:
            pg_tool("pg_restore", restored_admin, "--no-owner", "--exit-on-error", str(dump))
            url = ctx["lookup"].engine.url
            restored = Database(make_conninfo(restored_admin, user=str(url.username), password=str(url.password)))
            assert (
                permission_module("directory").PermissionDirectory(restored).read(ctx["principal"], "identity.read")
                == expected
            )
            with (
                psycopg.connect(restored_admin) as target,
                psycopg.connect(ctx["admin_dsn"]) as source,
            ):
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


@pytest.mark.parametrize("changed", ["principal", "permission", "digest", "truthy", "exception"])
def test_misbound_or_invalid_permission_facts_fail_closed(permission_context, changed):
    ctx = permission_context
    types, policies = permission_module("types"), permission_module("policy")
    policy = SimpleNamespace(version="fixture-v1")
    policy.decide = lambda fact: types.PermissionDecision(
        fact.principal.actor, fact.permission, True, policy.version, fact.version_digest
    )

    def read(principal, permission):
        fact = types.PermissionFact(principal, permission, True, "1" * 64)
        if changed == "exception":
            raise RuntimeError("fixture unavailable")
        return {
            "principal": replace(fact, principal=replace(principal, actor=ctx["other_actor"])),
            "permission": replace(fact, permission="export.create"),
            "digest": replace(fact, version_digest="invalid"),
            "truthy": replace(fact, eligible="yes"),
        }[changed]

    authority = policies.DirectoryPermissionAuthority(SimpleNamespace(read=read), policy)
    with pytest.raises(BusinessError) as caught:
        authority.check(ctx["principal"], "identity.read")
    assert caught.value.http_status == 503


def test_ineligible_fact_cannot_be_overridden_by_policy(permission_context):
    ctx = permission_context
    types, policies = permission_module("types"), permission_module("policy")
    policy = SimpleNamespace(version="fixture-v1")
    policy.decide = lambda fact: pytest.fail("ineligible directory fact must not enter an allow policy")
    lookup = SimpleNamespace(read=lambda p, permission: types.PermissionFact(p, permission, False, "1" * 64))
    with pytest.raises(BusinessError) as caught:
        policies.DirectoryPermissionAuthority(lookup, policy).check(ctx["principal"], "identity.read")
    assert (caught.value.code, caught.value.http_status) == ("PERMISSION_REQUIRED", 403)


@pytest.mark.parametrize("state,expected", [("role", 403), ("identity", 401), ("version", 503)])
def test_policy_decision_cannot_outlive_its_exact_directory_fact(permission_context, state, expected):
    ctx = permission_context
    types, policies = permission_module("types"), permission_module("policy")

    class ChangedDuringPolicy:
        version = "fixture-v1"

        def decide(self, fact):
            query, identifier = {
                "role": ("UPDATE mt.user_roles SET revoked_at=now() WHERE user_role_id=%s", ctx["binding"]),
                "identity": (
                    "UPDATE mt.user_identities SET enabled=false,revoked_at=now() WHERE identity_id=%s",
                    ctx["identity"],
                ),
                "version": ("UPDATE mt.roles SET row_version=row_version+1 WHERE role_id=%s", ctx["role"]),
            }[state]
            with psycopg.connect(ctx["admin_dsn"]) as admin:
                admin.execute(query, (identifier,))
            return types.PermissionDecision(
                fact.principal.actor, fact.permission, True, self.version, fact.version_digest
            )

    authority = policies.DirectoryPermissionAuthority(reader(ctx), ChangedDuringPolicy())
    with pytest.raises(BusinessError) as caught:
        authority.check(ctx["principal"], "identity.read")
    assert caught.value.http_status == expected
