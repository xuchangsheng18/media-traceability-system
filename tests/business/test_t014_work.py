"""Real queued-work ownership, fresh directory facts and no user-token impersonation."""

import time
from dataclasses import replace
from uuid import UUID, uuid4

import psycopg
import pytest
from business_app.errors import BusinessError
from business_app.types import Scope
from business_app.uploads.worker import UploadValidationWorker

from tests.business.http_fixtures import FixtureMetadataWorkTrust
from tests.business.test_adapters_and_execution import prepare_node
from tests.business.test_controls import control_context as control_context
from tests.business.test_controls import export_fixture
from tests.business.test_t014_permissions import permission_context as permission_context
from tests.business.test_t014_permissions import permission_module
from tests.business.test_t014_revocation import environment
from tests.business.test_upload_validation import complete, event, prepared_upload


def work_types():
    types = permission_module("rule_types")
    assert hasattr(types, "ExecutionSubject"), "Background work needs a real subject, not a fabricated JWT Principal"
    return types


def test_existing_upload_worker_requires_separate_work_authority(business_context):
    ctx = business_context
    app, http, upload, descriptor = prepared_upload(ctx)
    try:
        assert complete(http, upload, descriptor).status_code == 202
        with pytest.raises(BusinessError) as missing:
            UploadValidationWorker(app.state.upload_service, ctx["authority"]).consume_validation(event(ctx, upload))
        assert (missing.value.code, missing.value.http_status) == ("CONDITIONAL_POLICY_UNCONFIGURED", 503)
        with psycopg.connect(ctx["admin_dsn"]) as admin:
            assert admin.execute(
                "SELECT state,asset_id FROM mt.upload_session WHERE upload_id=%s", (upload,)
            ).fetchone() == ("VALIDATING", None)
            assert admin.execute("SELECT count(*) FROM mt.media_asset").fetchone() == (0,)
    finally:
        http.__exit__(None, None, None)


@pytest.mark.parametrize("kind", ["node", "export"])
def test_existing_background_entry_cannot_bypass_missing_work_authority(control_context, kind):
    ctx = control_context
    app = ctx["control_app"]
    scope = Scope(ctx["actor"], ctx["case_id"])
    if kind == "node":
        identifier = prepare_node(ctx)
        service = app.state.execution
        if hasattr(service, "work_authorization"):
            service.work_authorization = None
        action = lambda: service.claim(scope, identifier, task_id=ctx["task_id"])
    else:
        identifier, _ = export_fixture(ctx)
        service = app.state.exports
        if hasattr(service, "work_authorization"):
            service.work_authorization = None
        action = lambda: service.process(scope, UUID(identifier))
    with pytest.raises(BusinessError) as missing:
        action()
    assert (missing.value.code, missing.value.http_status) == ("CONDITIONAL_POLICY_UNCONFIGURED", 503)
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        if kind == "node":
            assert admin.execute(
                "SELECT state,fencing_epoch FROM mt.task_node_run WHERE run_id=%s", (identifier,)
            ).fetchone() == ("READY", 1)
        else:
            assert admin.execute(
                "SELECT state,artifact_ref FROM mt.audit_export WHERE export_id=%s", (identifier,)
            ).fetchone() == ("REQUESTED", {})


@pytest.mark.parametrize("defect", ["identity", "mapping", "work_id", "actor", "expiry", "revoked_role"])
def test_queued_job_revalidates_actor_identity_and_scope(permission_context, defect):
    ctx = permission_context
    types = work_types()
    app, http, upload, descriptor = prepared_upload(ctx)
    try:
        assert complete(http, upload, descriptor).status_code == 202
        subject = types.ExecutionSubject(
            ctx["actor"], ctx["identity"], "fixture-map-v1", "upload_validation", UUID(upload)
        )
        reader = permission_module("role_facts").RoleDirectory(
            ctx["lookup"], clock=time.time, work_database=ctx["database"], work_trust=FixtureMetadataWorkTrust()
        )
        fact = reader.read_for_work(subject, "identity.read")
        assert fact.subject == subject and fact.eligible is True
        assert time.time() < fact.valid_until <= time.time() + 5
        assert not hasattr(fact, "principal"), "No token expiry or fabricated user token may be invented for a job"
        if defect in {"identity", "work_id", "actor"}:
            subject = replace(
                subject,
                **{
                    "identity": {"identity_id": uuid4()},
                    "work_id": {"work_id": uuid4()},
                    "actor": {"actor": ctx["other_actor"]},
                }[defect],
            )
        else:
            statement = {
                "mapping": "UPDATE mt.user_identities SET mapping_version='changed',row_version=row_version+1 WHERE identity_id=%s",
                "expiry": "UPDATE mt.user_identities SET expires_at=now()-interval '1 second',row_version=row_version+1 WHERE identity_id=%s",
                "revoked_role": "UPDATE mt.user_roles SET revoked_at=now() WHERE user_role_id=%s",
            }[defect]
            with psycopg.connect(ctx["admin_dsn"]) as admin:
                admin.execute(statement, (ctx["binding"] if defect == "revoked_role" else ctx["identity"],))
        if defect == "revoked_role":
            assert reader.read_for_work(subject, "identity.read").eligible is False
        else:
            with pytest.raises(BusinessError) as denied:
                reader.read_for_work(subject, "identity.read")
            expected = (
                (404, "RESOURCE_NOT_FOUND") if defect in {"work_id", "actor"} else (401, "AUTHENTICATION_REQUIRED")
            )
            assert (denied.value.http_status, denied.value.code) == expected
    finally:
        http.__exit__(None, None, None)


def candidate_work(ctx, kind, identifier, *, role="data_admin"):
    conditional = permission_module("conditional")
    assert hasattr(conditional.ConditionalPermissionAuthority, "authorize_work"), (
        "Work facts must be authorized without fabricating a user JWT"
    )
    module, types = permission_module("work"), work_types()
    e = environment(ctx)
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        found_role = admin.execute("SELECT role_id FROM mt.roles WHERE code=%s", (role,)).fetchone()
        role_id = found_role[0] if found_role else uuid4()
        if not found_role:
            admin.execute(
                "INSERT INTO mt.roles(role_id,code,description,enabled) VALUES(%s,%s,'synthetic work only',true)",
                (role_id, role),
            )
        if role != "data_admin":
            admin.execute(
                "UPDATE mt.user_roles SET revoked_at=now() WHERE user_id=%s AND revoked_at IS NULL",
                (ctx["actor"].user_id,),
            )
            admin.execute(
                "INSERT INTO mt.user_roles(user_role_id,user_id,role_id) VALUES(%s,%s,%s)",
                (uuid4(), ctx["actor"].user_id, role_id),
            )
        for code in ["asset.upload", "task.create", "task.cancel", "audit.export", "audit.read"]:
            found = admin.execute("SELECT permission_id FROM mt.permissions WHERE code=%s", (code,)).fetchone()
            permission = found[0] if found else uuid4()
            if not found:
                admin.execute(
                    "INSERT INTO mt.permissions(permission_id,code,description,enabled) VALUES(%s,%s,'synthetic work only',true)",
                    (permission, code),
                )
            if not admin.execute(
                "SELECT 1 FROM mt.role_permissions WHERE role_id=%s AND permission_id=%s", (role_id, permission)
            ).fetchone():
                admin.execute(
                    "INSERT INTO mt.role_permissions(role_permission_id,role_id,permission_id) VALUES(%s,%s,%s)",
                    (uuid4(), role_id, permission),
                )
    subject = types.ExecutionSubject(ctx["actor"], ctx["identity"], "fixture-map-v1", kind, UUID(str(identifier)))

    class Delegations:
        value = module.WorkDelegation(subject, "d" * 64, time.time() + 600)

        def read(self, actor, work_kind, work_id):
            if (actor, work_kind, work_id) != (subject.actor, subject.work_kind, subject.work_id):
                raise RuntimeError("Unknown synthetic delegation")
            return self.value

    class Services:
        available = True

        def read(self, service_id, work_kind, work_id):
            if not self.available:
                raise RuntimeError("Synthetic service authority unavailable")
            return module.WorkServiceProof(service_id, work_kind, work_id, "e" * 64, time.time() + 600)

    class Supplemental:
        classified = True

        def values(self, target):
            if target.kind == "upload":
                return dict(classification=self.classified, purpose_basis=True)
            if target.kind == "task":
                return dict(classification=self.classified, capability=True, model_task_version=True)
            return dict(
                audit_delegation=True, audit_window_fields_quota=True, independent_person=True, object_binding=True
            )

        def read_for_work(self, current, operation, target, *, connection):
            return types.WorkConditionFacts(current, target, self.values(target), "f" * 64, time.time() + 60)

        def read(self, principal, operation, target, *, connection):
            return types.ConditionFacts(principal, target, self.values(target), "f" * 64, time.time() + 60)

    delegations, services, supplemental = Delegations(), Services(), Supplemental()
    trust = module.WorkTrust(delegations, services, {kind: "synthetic-distinct-service"}, clock=time.time)
    e.authority.reader = permission_module("role_facts").RoleDirectory(
        ctx["lookup"], clock=time.time, work_database=ctx["database"], work_trust=trust
    )
    e.authority.objects.supplemental = supplemental
    e.authority.work_trust = trust
    e.fence.clock = time.time
    manager = module.WorkAuthorizationManager(ctx["database"], e.authority, e.fence, trust)
    return e, manager, subject, delegations, services, supplemental


@pytest.mark.parametrize("expire_delegation", [False, True])
def test_upload_longer_than_fact_refresh_rechecks_before_commit(permission_context, expire_delegation):
    ctx = permission_context
    app, http, upload, descriptor = prepared_upload(ctx)
    try:
        assert complete(http, upload, descriptor).status_code == 202
        _, manager, _, delegations, _, _ = candidate_work(ctx, "upload_validation", upload)
        original = app.state.upload_service.store.put_part
        elapsed = []

        def slower_store(*args, **kwargs):
            start = time.monotonic()
            result = original(*args, **kwargs)
            time.sleep(6)
            elapsed.append(time.monotonic() - start)
            if expire_delegation:
                delegations.value = replace(delegations.value, valid_until=time.time() - 1)
            return result

        app.state.upload_service.store.put_part = slower_store
        consumer = UploadValidationWorker(app.state.upload_service, ctx["authority"], manager)
        denied_code = None
        if expire_delegation:
            with pytest.raises(BusinessError) as caught:
                consumer.consume_validation(event(ctx, upload))
            assert caught.value.http_status == 503
            denied_code = caught.value.code
        else:
            consumer.consume_validation(event(ctx, upload))
        assert len(elapsed) == 1 and elapsed[0] >= 6, f"OBJECT_WRITE_CHECKPOINT_NOT_REACHED:{denied_code}"
        with psycopg.connect(ctx["admin_dsn"]) as admin:
            assert admin.execute("SELECT state FROM mt.upload_session WHERE upload_id=%s", (upload,)).fetchone() == (
                "VALIDATING" if expire_delegation else "COMPLETED",
            )
            assert admin.execute("SELECT count(*) FROM mt.media_asset").fetchone() == (0 if expire_delegation else 1,)
    finally:
        http.__exit__(None, None, None)


@pytest.mark.parametrize(
    "defect",
    [
        "none",
        "identity",
        "mapping",
        "classification",
        "service_before",
        "service_after_store",
        "expired_delegation",
        "terminal_replay",
    ],
)
def test_upload_work_rechecks_live_facts_and_rolls_back_uncommitted_result(permission_context, defect):
    ctx = permission_context
    app, http, upload, descriptor = prepared_upload(ctx)
    try:
        assert complete(http, upload, descriptor).status_code == 202
        _, manager, _, delegations, services, supplemental = candidate_work(ctx, "upload_validation", upload)
        consumer = UploadValidationWorker(app.state.upload_service, ctx["authority"], manager)
        message = event(ctx, upload)
        if defect in {"identity", "mapping"}:
            with psycopg.connect(ctx["admin_dsn"]) as admin:
                statement = (
                    "UPDATE mt.user_identities SET enabled=false,revoked_at=now(),row_version=row_version+1 WHERE identity_id=%s"
                    if defect == "identity"
                    else "UPDATE mt.user_identities SET mapping_version='rebound',row_version=row_version+1 WHERE identity_id=%s"
                )
                admin.execute(statement, (ctx["identity"],))
        elif defect == "classification":
            supplemental.classified = False
        elif defect == "service_before":
            services.available = False
        elif defect == "expired_delegation":
            delegations.value = replace(delegations.value, valid_until=time.time() - 1)
        elif defect == "service_after_store":
            original = app.state.upload_service.store.put_part

            def store_then_service_failure(*args, **kwargs):
                result = original(*args, **kwargs)
                services.available = False
                return result

            app.state.upload_service.store.put_part = store_then_service_failure
        if defect in {"none", "terminal_replay"}:
            consumer.consume_validation(message)
            with psycopg.connect(ctx["admin_dsn"]) as admin:
                assert admin.execute(
                    "SELECT state FROM mt.upload_session WHERE upload_id=%s", (upload,)
                ).fetchone() == ("COMPLETED",)
                assert admin.execute("SELECT count(*) FROM mt.media_asset").fetchone() == (1,)
            if defect == "terminal_replay":
                with psycopg.connect(ctx["admin_dsn"]) as admin:
                    admin.execute(
                        "UPDATE mt.user_roles SET revoked_at=now() WHERE user_id=%s AND revoked_at IS NULL",
                        (ctx["actor"].user_id,),
                    )
                with pytest.raises(BusinessError) as denied:
                    consumer.consume_validation(message)
                assert denied.value.http_status == 403
        else:
            with pytest.raises(BusinessError) as denied:
                consumer.consume_validation(message)
            expected = (
                (401, "AUTHENTICATION_REQUIRED")
                if defect in {"identity", "mapping"}
                else (403, "PERMISSION_REQUIRED")
                if defect == "classification"
                else (503, "CONDITIONAL_FACTS_UNAVAILABLE")
            )
            assert (denied.value.http_status, denied.value.code) == expected
            with psycopg.connect(ctx["admin_dsn"]) as admin:
                assert admin.execute(
                    "SELECT state,asset_id FROM mt.upload_session WHERE upload_id=%s", (upload,)
                ).fetchone() == ("VALIDATING", None)
                assert admin.execute("SELECT count(*) FROM mt.media_asset").fetchone() == (0,)
            if defect == "service_after_store":
                assert list(app.state.upload_service.store.root.rglob("*.orphan.json"))
    finally:
        http.__exit__(None, None, None)


@pytest.mark.parametrize("kind", ["node", "export"])
def test_node_finish_and_export_delivery_revalidate(control_context, permission_context, kind):
    ctx = dict(control_context)
    for key in ["lookup", "principal", "identity", "binding", "role", "permission", "relation", "login"]:
        ctx[key] = permission_context[key]
    scope = Scope(ctx["actor"], ctx["case_id"])
    app = ctx["control_app"]
    if kind == "node":
        identifier = prepare_node(ctx)
        _, manager, _, _, services, _ = candidate_work(ctx, "task_execution", ctx["task_id"], role="case_investigator")
        service = app.state.execution
        service.work_authorization = manager
        lease = service.claim(scope, identifier, task_id=ctx["task_id"])
        services.available = False
        with pytest.raises(BusinessError) as denied:
            service.finish_without_result(scope, lease, "NOT_SUPPORTED", "No algorithm; explicit work-authority test")
        assert denied.value.http_status == 503
        with psycopg.connect(ctx["admin_dsn"]) as admin:
            assert admin.execute(
                "SELECT state,fencing_epoch,ended_at FROM mt.task_node_run WHERE run_id=%s", (identifier,)
            ).fetchone() == ("RUNNING", lease.epoch, None)
        services.available = True
        service.finish_without_result(scope, lease, "NOT_SUPPORTED", "No algorithm; authorized stop only")
        with psycopg.connect(ctx["admin_dsn"]) as admin:
            assert admin.execute("SELECT state FROM mt.task_node_run WHERE run_id=%s", (identifier,)).fetchone() == (
                "NOT_SUPPORTED",
            )
            assert admin.execute(
                "SELECT count(*) FROM mt.task_result WHERE task_id=%s", (ctx["task_id"],)
            ).fetchone() == (1,)
    else:
        identifier, _ = export_fixture(ctx)
        e, manager, _, _, _, _ = candidate_work(ctx, "audit_export", identifier, role="auditor")
        app.state.exports.work_authorization = manager
        app.state.exports.process(scope, UUID(identifier))
        from business_app.permissions.six_role import SixRoleEntryAuthority

        from tests.business.test_controls import AUTH

        original = ctx["control_authority"]

        class Identity:
            def authenticate_principal(self, token):
                if original.authenticate(token) != ctx["actor"]:
                    raise BusinessError("AUTHENTICATION_REQUIRED", 401)
                return ctx["principal"]

            def authenticate(self, token):
                return self.authenticate_principal(token).actor

            def authorize_case(self, actor, case, action):
                return original.authorize_case(actor, case, action)

            def authorize_source(self, scope, source, purpose):
                return original.authorize_source(scope, source, purpose)

        app.state.business_authority = Identity()
        app.state.permission_authority = SixRoleEntryAuthority(e.authority.reader, e.rules)
        app.state.conditional_permissions = e.authority
        app.state.authorization_fence = e.fence
        path = f"/api/v1/audit/exports/{identifier}/content"
        assert ctx["control_http"].get(path, headers=AUTH).status_code == 200
        with psycopg.connect(ctx["admin_dsn"]) as admin:
            before = admin.execute(
                "SELECT artifact_ref FROM mt.audit_export WHERE export_id=%s", (identifier,)
            ).fetchone()
            admin.execute(
                "UPDATE mt.user_roles SET revoked_at=now() WHERE user_id=%s AND revoked_at IS NULL",
                (ctx["actor"].user_id,),
            )
        response = ctx["control_http"].get(path, headers=AUTH)
        assert response.status_code == 403 and response.json()["code"] == "PERMISSION_REQUIRED"
        with psycopg.connect(ctx["admin_dsn"]) as admin:
            assert (
                admin.execute("SELECT artifact_ref FROM mt.audit_export WHERE export_id=%s", (identifier,)).fetchone()
                == before
            )


@pytest.mark.parametrize("danger", ["pg_signal_backend", "pg_checkpoint"])
def test_work_directory_rejects_excessive_runtime_privilege(permission_context, danger):
    from psycopg import sql
    from psycopg.conninfo import conninfo_to_dict

    ctx = permission_context
    app, http, upload, descriptor = prepared_upload(ctx)
    login = conninfo_to_dict(ctx["settings"].database_dsn)["user"]
    assert isinstance(login, str) and login
    try:
        subject = work_types().ExecutionSubject(
            ctx["actor"], ctx["identity"], "fixture-map-v1", "upload_validation", UUID(upload)
        )
        reader = permission_module("role_facts").RoleDirectory(
            ctx["lookup"], clock=time.time, work_database=ctx["database"], work_trust=FixtureMetadataWorkTrust()
        )
        assert reader.read_for_work(subject, "identity.read").eligible is True
        with psycopg.connect(ctx["admin_dsn"]) as admin:
            admin.execute(sql.SQL("GRANT {} TO {}").format(sql.Identifier(danger), sql.Identifier(login)))
        try:
            with pytest.raises(BusinessError) as denied:
                reader.read_for_work(subject, "identity.read")
            assert denied.value.http_status == 503
        finally:
            with psycopg.connect(ctx["admin_dsn"]) as admin:
                admin.execute(sql.SQL("REVOKE {} FROM {}").format(sql.Identifier(danger), sql.Identifier(login)))
    finally:
        http.__exit__(None, None, None)


def test_missing_work_port_rejects_before_broker_or_published_receipt(business_context):
    from business_app.uploads.messaging import pump_outbox_once

    ctx = business_context
    app, http, upload, descriptor = prepared_upload(ctx)
    try:
        assert complete(http, upload, descriptor).status_code == 202
        with pytest.raises(BusinessError) as denied:
            pump_outbox_once(
                app.state.upload_service,
                ctx["authority"],
                Scope(ctx["actor"], ctx["case_id"]),
                "unsupported-test-only://never-connect",
            )
        assert (denied.value.code, denied.value.http_status) == ("CONDITIONAL_POLICY_UNCONFIGURED", 503)
        with psycopg.connect(ctx["admin_dsn"]) as admin:
            assert admin.execute(
                "SELECT published_at,attempts FROM mt.outbox_event WHERE aggregate_id=%s", (upload,)
            ).fetchone() == (None, 0)
            assert admin.execute(
                "SELECT state,asset_id FROM mt.upload_session WHERE upload_id=%s", (upload,)
            ).fetchone() == ("VALIDATING", None)
    finally:
        http.__exit__(None, None, None)
