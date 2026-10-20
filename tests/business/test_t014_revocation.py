"""Ordered real PostgreSQL revocation and explicit, independent recovery generations."""

import threading
import time
from dataclasses import replace
from types import SimpleNamespace
from uuid import uuid4

import psycopg
import pytest
from business_app.errors import BusinessError
from sqlalchemy import text

from tests.business.test_t014_object_rules import configure
from tests.business.test_t014_permissions import permission_context as permission_context
from tests.business.test_t014_permissions import permission_module


def environment(ctx):
    types, roles, rules, objects, authority = configure(ctx, "data_admin")
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        assert admin.execute("SELECT to_regclass('mt.authorization_epoch') IS NOT NULL").fetchone() == (True,), (
            "transaction authorization epoch is not implemented"
        )
        database_row = admin.execute(
            "SELECT current_database(),oid FROM pg_database WHERE datname=current_database()"
        ).fetchone()
        assert database_row is not None
        database_name, database_oid = database_row
        epoch_row = admin.execute("SELECT epoch FROM mt.authorization_epoch").fetchone()
        assert epoch_row is not None
        activated = admin.execute(
            "SELECT mt.activate_authorization_generation(%s,%s,%s,%s)",
            (rules.snapshot.version, rules.snapshot.sha256, rules.snapshot.recovery_generation, epoch_row[0]),
        ).fetchone()
        assert activated is not None
        epoch = activated[0]
    module = permission_module("fence")
    clock = [time.time()]

    class Generations:
        proof = module.GenerationProof(
            rules.snapshot.recovery_generation,
            rules.snapshot.version,
            rules.snapshot.sha256,
            database_name,
            database_oid,
            epoch,
            clock[0] - 1,
            clock[0] + 1800,
        )

        def read(self):
            return self.proof

    generations = Generations()
    target = types.RuleTarget(ctx["actor"].org_id, "policy_collection", None, None, None, None, "retention")
    evidence = authority.authorize(ctx["principal"], "createPolicy", target)
    return SimpleNamespace(
        types=types,
        roles=roles,
        rules=rules,
        objects=objects,
        authority=authority,
        clock=clock,
        generations=generations,
        evidence=evidence,
        fence=module.AuthorizationFence(authority, generations, clock=lambda: clock[0]),
    )


def insert_policy(connection, ctx):
    identifier = uuid4()
    connection.execute(
        text(
            "INSERT INTO mt.policy_registry(policy_id,org_id,kind,version,definition_ref,status,created_by) "
            "VALUES(:id,:org,'retention',:version,'urn:synthetic-only','DRAFT',:actor)"
        ),
        dict(id=identifier, org=ctx["actor"].org_id, version=uuid4().hex, actor=ctx["actor"].user_id),
    )
    connection.execute(
        text(
            "INSERT INTO mt.audit_event(event_id,org_id,actor_id,action,object_type,object_id,object_version,outcome,request_id,occurred_at,details,created_by) "
            "VALUES(:event,:org,:actor,'policy.create','policy',:id,1,'allowed',:request,now(),'{}'::jsonb,:actor)"
        ),
        dict(event=uuid4(), org=ctx["actor"].org_id, actor=ctx["actor"].user_id, id=identifier, request=uuid4()),
    )
    return identifier


def counts(ctx):
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        row = admin.execute(
            "SELECT (SELECT count(*) FROM mt.policy_registry),(SELECT count(*) FROM mt.audit_event)"
        ).fetchone()
        assert row is not None
        return tuple(row)


def test_revoke_committed_before_fence_blocks_business_commit(permission_context):
    ctx = permission_context
    e = environment(ctx)
    with psycopg.connect(ctx["admin_dsn"]) as revoker:
        revoker.execute(
            "UPDATE mt.user_roles SET revoked_at=statement_timestamp() WHERE user_id=%s AND revoked_at IS NULL",
            (ctx["actor"].user_id,),
        )
    with pytest.raises(BusinessError) as caught:
        with ctx["database"].identity_transaction(ctx["actor"]) as connection:
            e.fence.hold(connection, e.evidence)
            insert_policy(connection, ctx)
    assert caught.value.http_status == 403
    assert counts(ctx) == (0, 0)


def test_business_commit_before_revoke_is_ordered_and_audited(permission_context):
    ctx = permission_context
    e = environment(ctx)
    ready, finished = threading.Event(), threading.Event()
    backend_pid = []
    errors = []

    def revoke():
        try:
            with psycopg.connect(ctx["admin_dsn"]) as revoker:
                revoker.execute("SET LOCAL statement_timeout='5000ms'")
                backend_pid.append(revoker.info.backend_pid)
                ready.set()
                revoker.execute(
                    "UPDATE mt.user_roles SET revoked_at=statement_timestamp() WHERE user_id=%s AND revoked_at IS NULL",
                    (ctx["actor"].user_id,),
                )
        except Exception as exc:
            errors.append(type(exc).__name__)
        finally:
            finished.set()

    thread = threading.Thread(target=revoke, daemon=True)
    with ctx["database"].identity_transaction(ctx["actor"]) as connection:
        e.fence.hold(connection, e.evidence)
        thread.start()
        assert ready.wait(2)
        deadline = time.monotonic() + 2
        blocked = False
        with psycopg.connect(ctx["admin_dsn"], autocommit=True) as observer:
            while time.monotonic() < deadline:
                row = observer.execute(
                    "SELECT wait_event_type FROM pg_stat_activity WHERE pid=%s", (backend_pid[0],)
                ).fetchone()
                if row == ("Lock",):
                    blocked = True
                    break
                time.sleep(0.01)
        assert blocked and not finished.is_set(), "revoker must actually wait on the held authorization epoch"
        identifier = insert_policy(connection, ctx)
        e.fence.finish(connection, e.evidence)
    thread.join(5)
    assert not thread.is_alive() and finished.is_set() and errors == []
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        assert admin.execute(
            "SELECT count(*) FROM mt.audit_event WHERE object_id=%s AND outcome='allowed'", (identifier,)
        ).fetchone() == (1,)
    with pytest.raises(BusinessError):
        with ctx["database"].identity_transaction(ctx["actor"]) as connection:
            e.fence.hold(connection, e.evidence)
            insert_policy(connection, ctx)
    assert counts(ctx) == (1, 1)


def test_role_insert_conflict_cannot_bypass_fence(permission_context):
    ctx = permission_context
    e = environment(ctx)
    role = uuid4()
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            "INSERT INTO mt.roles(role_id,code,description,enabled) VALUES(%s,'auditor','synthetic conflict',true)",
            (role,),
        )
        admin.execute(
            "INSERT INTO mt.user_roles(user_role_id,user_id,role_id) VALUES(%s,%s,%s)",
            (uuid4(), ctx["actor"].user_id, role),
        )
    with pytest.raises(BusinessError) as caught:
        with ctx["database"].identity_transaction(ctx["actor"]) as connection:
            e.fence.hold(connection, e.evidence)
            insert_policy(connection, ctx)
    assert caught.value.http_status == 403
    assert counts(ctx) == (0, 0)


@pytest.mark.parametrize("defect", ["unknown", "generation", "database", "epoch_floor", "policy"])
def test_restored_or_rolled_back_policy_does_not_reactivate_revoked_grant(permission_context, defect):
    ctx = permission_context
    e = environment(ctx)
    values = {
        "generation": dict(recovery_generation="different-confirmed-recovery"),
        "database": dict(database_oid=e.generations.proof.database_oid + 1),
        "epoch_floor": dict(minimum_epoch=e.generations.proof.minimum_epoch + 100),
        "policy": dict(policy_sha256="0" * 64),
    }
    if defect == "unknown":
        e.fence.generations = None
    else:
        e.generations.proof = replace(e.generations.proof, **values[defect])
    with pytest.raises(BusinessError) as caught:
        with ctx["database"].identity_transaction(ctx["actor"]) as connection:
            e.fence.hold(connection, e.evidence)
            insert_policy(connection, ctx)
    assert caught.value.http_status == 503
    assert counts(ctx) == (0, 0)


@pytest.mark.parametrize("defect", ["clock_rollback", "fact_read_failure"])
def test_clock_rollback_or_failed_fact_read_is_denied(permission_context, defect):
    ctx = permission_context
    e = environment(ctx)
    with pytest.raises(BusinessError) as caught:
        with ctx["database"].identity_transaction(ctx["actor"]) as connection:
            e.fence.hold(connection, e.evidence)
            insert_policy(connection, ctx)
            if defect == "clock_rollback":
                e.clock[0] -= 2
            else:

                class UnavailableRoles:
                    def read_roles(self, *args, **kwargs):
                        raise RuntimeError("synthetic directory read failure")

                e.authority.reader = UnavailableRoles()
            e.fence.finish(connection, e.evidence)
    assert caught.value.http_status == 503
    assert counts(ctx) == (0, 0)


def test_epoch_lookup_is_function_only_and_lock_timeout_rolls_back(permission_context):
    ctx = permission_context
    e = environment(ctx)
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        assert admin.execute(
            "SELECT has_table_privilege('mt_runtime','mt.authorization_epoch','SELECT,INSERT,UPDATE,DELETE,TRUNCATE')"
        ).fetchone() == (False,)
        assert admin.execute(
            "SELECT count(*) FROM pg_proc p CROSS JOIN LATERAL aclexplode(p.proacl) a WHERE p.oid='mt.hold_authorization_epoch()'::regprocedure AND a.grantee=0"
        ).fetchone() == (0,)
        admin.execute("UPDATE mt.authorization_epoch SET epoch=epoch+1")
        with pytest.raises(BusinessError) as caught:
            with ctx["database"].identity_transaction(ctx["actor"]) as connection:
                connection.execute(text("SET LOCAL lock_timeout='100ms'"))
                e.fence.hold(connection, e.evidence)
                insert_policy(connection, ctx)
        assert caught.value.http_status == 503
    assert counts(ctx) == (0, 0)


def policy_application(ctx, e, fence, *, revoke_after_entry=False):
    from business_app.main import create_app
    from business_app.permissions.six_role import SixRoleEntryAuthority

    delegate = ctx["authority"]

    class Identity:
        def authenticate_principal(self, token):
            assert delegate.authenticate(token) == ctx["actor"]
            return ctx["principal"]

        authenticate = delegate.authenticate
        authorize_case = delegate.authorize_case
        authorize_source = delegate.authorize_source

    class Directory:
        def current(self, actor):
            if revoke_after_entry:
                with psycopg.connect(ctx["admin_dsn"]) as admin:
                    admin.execute(
                        "UPDATE mt.user_roles SET revoked_at=statement_timestamp() WHERE user_id=%s AND revoked_at IS NULL",
                        (actor.user_id,),
                    )
            return dict(
                user_id=str(actor.user_id),
                org_id=str(actor.org_id),
                roles=["synthetic-only"],
                permissions=["policy.manage"],
                case_ids=[],
            )

    app = create_app(
        replace(ctx["settings"], control_ttl_seconds=1800),
        Identity(),
        identity_directory=Directory(),
        permission_authority=SixRoleEntryAuthority(e.roles, e.rules),
        conditional_permissions=e.authority,
    )
    app.state.authorization_fence = fence
    return app


def create_policy_http(client):
    return client.post(
        "/api/v1/policies",
        json=dict(
            kind="retention", version=uuid4().hex, definition_ref="urn:synthetic-only", approval_id=None, status="DRAFT"
        ),
        headers={"Authorization": "Bearer test-only-valid-token", "Idempotency-Key": uuid4().hex},
    )


@pytest.mark.parametrize("defect", ["missing_fence", "revoke_after_entry", "generation_changes_after_insert"])
def test_real_HTTP_write_requires_fence_and_rollback_on_final_change(permission_context, defect):
    from fastapi.testclient import TestClient
    from sqlalchemy import event

    ctx = permission_context
    e = environment(ctx)
    app = policy_application(
        ctx, e, None if defect == "missing_fence" else e.fence, revoke_after_entry=defect == "revoke_after_entry"
    )
    inserted = []

    def after_insert(connection, cursor, statement, parameters, context, executemany):
        if defect == "generation_changes_after_insert" and statement.lstrip().startswith(
            "INSERT INTO mt.policy_registry"
        ):
            inserted.append(True)
            e.generations.proof = replace(e.generations.proof, recovery_generation="externally-changed-generation")

    event.listen(app.state.business_database.engine, "after_cursor_execute", after_insert)
    with TestClient(app) as client:
        response = create_policy_http(client)
    assert response.status_code == (403 if defect == "revoke_after_entry" else 503), response.json()
    assert (
        response.json()["code"]
        == {
            "missing_fence": "CONDITIONAL_POLICY_UNCONFIGURED",
            "revoke_after_entry": "PERMISSION_REQUIRED",
            "generation_changes_after_insert": "AUTHORIZATION_CHANGED",
        }[defect]
    )
    assert inserted == ([True] if defect == "generation_changes_after_insert" else [])
    assert counts(ctx) == (0, 0)


@pytest.mark.parametrize("column", ["policy_version", "policy_sha256", "recovery_generation"])
def test_partial_generation_metadata_is_rejected_by_SQL_constraint(permission_context, column):
    ctx = permission_context
    environment(ctx)
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        with pytest.raises(psycopg.errors.CheckViolation):
            admin.execute("UPDATE mt.authorization_epoch SET " + column + "=NULL")


def test_source_change_waits_for_the_same_business_transaction(permission_context):
    ctx = permission_context
    e = environment(ctx)
    target = e.types.RuleTarget(ctx["actor"].org_id, "source", ctx["source_id"], None, ctx["case_id"], None, None)
    evidence = e.authority.authorize(ctx["principal"], "getSource", target)
    ready, finished = threading.Event(), threading.Event()
    pids = []
    failures = []

    def change_source():
        try:
            with psycopg.connect(ctx["admin_dsn"]) as admin:
                admin.execute("SET LOCAL statement_timeout='5000ms'")
                pids.append(admin.info.backend_pid)
                ready.set()
                admin.execute(
                    "UPDATE mt.source_registry SET authorization_version='synthetic-v2',row_version=row_version+1 WHERE source_id=%s",
                    (ctx["source_id"],),
                )
        except Exception as error:
            failures.append(type(error).__name__)
        finally:
            finished.set()

    thread = threading.Thread(target=change_source, daemon=True)
    try:
        with ctx["database"].identity_transaction(ctx["actor"]) as connection:
            e.fence.hold(connection, evidence)
            thread.start()
            assert ready.wait(2)
            blocked = False
            deadline = time.monotonic() + 2
            with psycopg.connect(ctx["admin_dsn"], autocommit=True) as observer:
                while time.monotonic() < deadline:
                    if observer.execute(
                        "SELECT wait_event_type FROM pg_stat_activity WHERE pid=%s", (pids[0],)
                    ).fetchone() == ("Lock",):
                        blocked = True
                        break
                    if finished.is_set():
                        break
                    time.sleep(0.01)
            assert blocked and not finished.is_set(), (
                "source authorization read must retain a row lock until business completion"
            )
            e.fence.finish(connection, evidence)
    finally:
        thread.join(5)
    assert not thread.is_alive() and failures == []


def test_actual_restored_database_needs_fresh_independent_generation(permission_context, tmp_path):
    from business_app.db import Database
    from psycopg import sql
    from psycopg.conninfo import make_conninfo

    from tests.business.test_recovery import pg_tool

    ctx = permission_context
    e = environment(ctx)
    name = "mt_business_fence_restore_" + uuid4().hex
    restored_admin = make_conninfo(ctx["admin_dsn"], dbname=name)
    dump = tmp_path / "fence.dump"
    pg_tool("pg_dump", ctx["admin_dsn"], "-Fc", "--no-owner", "--file", str(dump))
    restored = None
    lookup = None
    with psycopg.connect(ctx["admin_dsn"], autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {} TEMPLATE template0").format(sql.Identifier(name)))
        try:
            pg_tool("pg_restore", restored_admin, "--no-owner", "--exit-on-error", str(dump))
            restored = Database(make_conninfo(ctx["settings"].database_dsn, dbname=name))
            with pytest.raises(BusinessError) as stale_target:
                with restored.identity_transaction(ctx["actor"]) as connection:
                    e.fence.hold(connection, e.evidence)
            assert stale_target.value.http_status == 503
            generation = "synthetic-explicit-restored-target-confirmation"
            with psycopg.connect(restored_admin) as target:
                stamp = target.execute("SELECT epoch FROM mt.authorization_epoch").fetchone()
                assert stamp is not None
                new_epoch = target.execute(
                    "SELECT mt.activate_authorization_generation(%s,%s,%s,%s)",
                    (e.rules.snapshot.version, e.rules.snapshot.sha256, generation, stamp[0]),
                ).fetchone()
                assert new_epoch is not None
                dbrow = target.execute(
                    "SELECT current_database(),oid FROM pg_database WHERE datname=current_database()"
                ).fetchone()
                assert dbrow is not None
                old = target.execute("SELECT version,sha256 FROM mt_meta.schema_migrations ORDER BY version").fetchall()
                assert (
                    old
                    == admin.execute("SELECT version,sha256 FROM mt_meta.schema_migrations ORDER BY version").fetchall()
                )
            e.rules.snapshot = replace(e.rules.snapshot, recovery_generation=generation)
            e.generations.proof = replace(
                e.generations.proof,
                recovery_generation=generation,
                database_name=dbrow[0],
                database_oid=dbrow[1],
                minimum_epoch=new_epoch[0],
            )
            with pytest.raises(BusinessError):
                with restored.identity_transaction(ctx["actor"]) as connection:
                    e.fence.hold(connection, e.evidence)
            url = ctx["lookup"].engine.url
            lookup = Database(make_conninfo(restored_admin, user=str(url.username), password=str(url.password)))
            roles = permission_module("role_facts").RoleDirectory(lookup, clock=time.time)
            objects = permission_module("object_facts").ObjectFactsReader(restored, clock=time.time)
            authority = permission_module("conditional").ConditionalPermissionAuthority(
                roles, e.rules, objects, clock=time.time
            )
            fresh = authority.authorize(ctx["principal"], "createPolicy", e.evidence.target)
            fence = permission_module("fence").AuthorizationFence(authority, e.generations, clock=time.time)
            with restored.identity_transaction(ctx["actor"]) as connection:
                fence.hold(connection, fresh)
                insert_policy(connection, ctx)
                fence.finish(connection, fresh)
            with psycopg.connect(restored_admin) as target:
                assert target.execute("SELECT count(*) FROM mt.policy_registry").fetchone() == (1,)
            assert counts(ctx) == (0, 0)
        finally:
            if lookup is not None:
                lookup.close()
            if restored is not None:
                restored.close()
            assert name.startswith("mt_business_fence_restore_") and len(name) == 58
            admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name)))


@pytest.mark.parametrize(
    "change,expected",
    [("identity", 401), ("role", 403), ("membership", 404), ("permission", 403), ("policy", 503), ("database", 503)],
)
def test_committed_revocation_rejects_new_requests_within_five_seconds(
    permission_context, record_property, change, expected
):
    from datetime import datetime, timezone

    from business_app.main import create_app
    from business_app.permissions.six_role import SixRoleEntryAuthority
    from fastapi.testclient import TestClient
    from psycopg import sql

    ctx = permission_context
    e = environment(ctx)
    e.fence.clock = time.time

    class Identity:
        def authenticate_principal(self, token):
            if token != "synthetic-same-old-token":
                raise BusinessError("AUTHENTICATION_REQUIRED", 401)
            return ctx["principal"]

        def authenticate(self, token):
            return self.authenticate_principal(token).actor

        def authorize_case(self, actor, case, action):
            return ctx["authority"].authorize_case(actor, case, action)

        def authorize_source(self, scope, source, purpose):
            return ctx["authority"].authorize_source(scope, source, purpose)

    app = create_app(
        ctx["settings"],
        Identity(),
        permission_authority=SixRoleEntryAuthority(e.roles, e.rules),
        conditional_permissions=e.authority,
        authorization_fence=e.fence,
    )
    url = f"/api/v1/sources/{ctx['source_id']}"
    headers = {"Authorization": "Bearer synthetic-same-old-token"}
    connect_revoked = False
    try:
        with TestClient(app) as client:
            assert client.get(url, headers=headers).status_code == 200
            with psycopg.connect(ctx["admin_dsn"]) as admin:
                if change == "identity":
                    admin.execute(
                        "UPDATE mt.user_identities SET enabled=false,revoked_at=now(),row_version=row_version+1 WHERE identity_id=%s",
                        (ctx["identity"],),
                    )
                elif change == "role":
                    admin.execute(
                        "UPDATE mt.user_roles SET revoked_at=now() WHERE user_id=%s AND revoked_at IS NULL",
                        (ctx["actor"].user_id,),
                    )
                elif change == "membership":
                    admin.execute(
                        "UPDATE mt.case_membership SET revoked_at=now() WHERE user_id=%s AND case_id=%s",
                        (ctx["actor"].user_id, ctx["case_id"]),
                    )
                elif change == "permission":
                    admin.execute("UPDATE mt.permissions SET enabled=false WHERE code='source.read'")
                elif change == "policy":
                    stamp = admin.execute("SELECT epoch FROM mt.authorization_epoch").fetchone()
                    assert stamp is not None
                    admin.execute(
                        "SELECT mt.activate_authorization_generation(%s,%s,%s,%s)",
                        (e.rules.snapshot.version, e.rules.snapshot.sha256, "synthetic-policy-change", stamp[0]),
                    )
                else:
                    name = admin.info.dbname
                    admin.execute(sql.SQL("REVOKE CONNECT ON DATABASE {} FROM PUBLIC").format(sql.Identifier(name)))
                    admin.execute(
                        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=current_database() AND usename=%s",
                        (ctx["login"],),
                    )
                    connect_revoked = True
            committed = time.monotonic()
            record_property("commit_observed_utc", datetime.now(timezone.utc).isoformat())
            delays = []
            for _ in range(3):
                response = client.get(url, headers=headers)
                delays.append(time.monotonic() - committed)
                assert response.status_code == expected, response.json()
                assert delays[-1] <= 5.0
            record_property("revocation_change", change)
            record_property("commit_observed_monotonic", committed)
            record_property("first_stable_denial_monotonic", committed + delays[0])
            record_property("maximum_observed_delay_seconds", max(delays))
            record_property("stable_denial_observations", 3)
    finally:
        if connect_revoked:
            with psycopg.connect(ctx["admin_dsn"]) as admin:
                admin.execute(
                    sql.SQL("GRANT CONNECT ON DATABASE {} TO PUBLIC").format(sql.Identifier(admin.info.dbname))
                )
