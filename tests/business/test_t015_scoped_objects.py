"""Real immutable bytes and bounded metadata; synthetic authority is explicit."""

import hashlib
import importlib
import importlib.util
import io
import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import psycopg
import pytest
from business_app.data_scope import ResourceBinding, TaskBinding
from business_app.errors import BusinessError
from business_app.permissions.rule_types import RuleTarget
from business_app.scope_context import current_data_scope
from business_app.types import ObjectRef, Scope
from psycopg.types.json import Jsonb

from tests.business.t014_positive_fixtures import candidate
from tests.business.test_controls import AUTH, export_fixture
from tests.business.test_controls import control_context as control_context
from tests.business.test_t014_indirect_reads import another_history
from tests.business.test_t014_permissions import permission_context as permission_context
from tests.business.test_t015_collections import synthetic_target
from tests.business.test_t015_scope_sql import two_cases
from tests.business.test_uploads import create, part
from tests.business.test_uploads import upload_client as upload_client


def scoped_objects():
    name = "business_app.scoped_objects"
    assert importlib.util.find_spec(name) is not None, "SCOPE_BOUND_OBJECT_PORT_REQUIRED"
    return importlib.import_module(name).ScopedObjects


def ref(value):
    return ObjectRef(UUID(str(value["object_id"])), value["version_id"], value["sha256"])


class SpyStore:
    def __init__(self, wrapped, *, split=False):
        self.wrapped, self.split = wrapped, split
        self.reads, self.writes, self.blocks = 0, 0, 0

    def read(self, reference):
        self.reads += 1
        if not self.split:
            return self.wrapped.read(reference)
        raw = b"".join(self.wrapped.read(reference))

        def pieces():
            for block in (raw[:2], raw[2:]):
                self.blocks += 1
                yield block

        return pieces()

    def put_part(self, *args, **kwargs):
        self.writes += 1
        return self.wrapped.put_part(*args, **kwargs)

    def record_orphan(self, *args, **kwargs):
        return self.wrapped.record_orphan(*args, **kwargs)


def test_cross_case_object_ref_is_denied_before_store_read(control_context):
    ctx = control_context
    _, other = two_cases(ctx)
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        record = admin.execute(
            "SELECT object_id,version_id,sha256 FROM mt.object_version WHERE case_id=%s", (other["case"],)
        ).fetchone()
    assert record is not None
    reference = ObjectRef(record[0], record[1], record[2])
    spy = SpyStore(ctx["app"].state.upload_service.store)
    port = scoped_objects()(spy, ctx["authority"])
    target = RuleTarget(ctx["actor"].org_id, "task", ctx["task_id"], 1, ctx["case_id"], None, None)
    with (
        synthetic_target(ctx, "getTask", target),
        ctx["database"].transaction(Scope(ctx["actor"], ctx["case_id"])) as connection,
    ):
        with pytest.raises(BusinessError):
            b"".join(
                port.read(connection, current_data_scope(), ResourceBinding("media_input", other["asset"]), reference)
            )
    assert spy.reads == 0


@pytest.mark.parametrize("defect", ["asset", "version", "digest"])
def test_same_case_task_input_cannot_swap_asset_or_immutable_version(control_context, defect):
    ctx = control_context
    other = another_history(ctx) if defect == "asset" else ctx
    reference = ref(other["input_ref"])
    if defect == "version":
        reference = replace(reference, version_id="fs-v1-" + uuid4().hex)
    if defect == "digest":
        reference = replace(reference, sha256="f" * 64)
    spy = SpyStore(ctx["app"].state.upload_service.store)
    port = scoped_objects()(spy, ctx["authority"])
    target = RuleTarget(ctx["actor"].org_id, "task", ctx["task_id"], 1, ctx["case_id"], None, None)
    with (
        synthetic_target(ctx, "getTask", target),
        ctx["database"].transaction(Scope(ctx["actor"], ctx["case_id"])) as connection,
    ):
        binding = ResourceBinding("media_input", UUID(str(other["asset_id"])), task=TaskBinding(ctx["task_id"], 1, 1))
        with pytest.raises(BusinessError):
            b"".join(port.read(connection, current_data_scope(), binding, reference))
    assert spy.reads == 0


def test_generator_started_after_scope_exit_is_denied(control_context):
    ctx = control_context
    spy = SpyStore(ctx["app"].state.upload_service.store)
    port = scoped_objects()(spy, ctx["authority"])
    target = RuleTarget(ctx["actor"].org_id, "task", ctx["task_id"], 1, ctx["case_id"], None, None)
    with (
        synthetic_target(ctx, "getTask", target),
        ctx["database"].transaction(Scope(ctx["actor"], ctx["case_id"])) as connection,
    ):
        stream = port.read(
            connection,
            current_data_scope(),
            ResourceBinding("media_input", UUID(str(ctx["asset_id"]))),
            ref(ctx["input_ref"]),
        )
    with pytest.raises(BusinessError) as denied:
        next(stream)
    assert denied.value.http_status == 503 and spy.reads == 0


def test_case_collection_permission_cannot_be_used_as_media_byte_permission(control_context):
    ctx = control_context
    spy = SpyStore(ctx["app"].state.upload_service.store)
    port = scoped_objects()(spy, ctx["authority"])
    target = RuleTarget(ctx["actor"].org_id, "case", ctx["case_id"], None, ctx["case_id"], None, None)
    with (
        synthetic_target(ctx, "listApprovals", target),
        ctx["database"].transaction(Scope(ctx["actor"], ctx["case_id"])) as connection,
    ):
        with pytest.raises(BusinessError) as denied:
            b"".join(
                port.read(
                    connection,
                    current_data_scope(),
                    ResourceBinding("media_input", UUID(str(ctx["asset_id"]))),
                    ref(ctx["input_ref"]),
                )
            )
        assert denied.value.http_status == 503
    assert spy.reads == 0


def test_revocation_between_blocks_stops_remaining_output(control_context):
    ctx = control_context

    class Authority:
        revoked = False

        def authorize_source(self, scope, source, purpose):
            if self.revoked:
                raise BusinessError("SOURCE_AUTHORIZATION_REQUIRED", 403)
            return ctx["authority"].authorize_source(scope, source, purpose)

    authority = Authority()
    spy = SpyStore(ctx["app"].state.upload_service.store, split=True)
    port = scoped_objects()(spy, authority)
    target = RuleTarget(ctx["actor"].org_id, "task", ctx["task_id"], 1, ctx["case_id"], None, None)
    with (
        synthetic_target(ctx, "getTask", target),
        ctx["database"].transaction(Scope(ctx["actor"], ctx["case_id"])) as connection,
    ):
        stream = port.read(
            connection,
            current_data_scope(),
            ResourceBinding("media_input", UUID(str(ctx["asset_id"]))),
            ref(ctx["input_ref"]),
        )
        sent = next(stream)
        assert len(sent) == 2 and spy.blocks == 1
        authority.revoked = True
        with pytest.raises(BusinessError) as denied:
            next(stream)
        assert denied.value.http_status == 403
        assert spy.blocks == 1, "Revoked stream must not even pull the next block"
    assert sent and len(sent) == 2  # Sent bytes cannot be recalled.


@pytest.mark.parametrize("defect", ["object", "version", "digest", "size", "expiry", "approval"])
def test_export_checks_exact_artifact_version_size_expiry_and_approval(control_context, defect):
    ctx = control_context
    identifier, approval = export_fixture(ctx)
    app = ctx["control_app"]
    scope = Scope(ctx["actor"], ctx["case_id"])
    app.state.exports.process(scope, UUID(identifier))
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        value = admin.execute(
            "SELECT artifact_ref FROM mt.audit_export WHERE export_id=%s", (UUID(identifier),)
        ).fetchone()
    assert value is not None
    artifact = dict(value[0])
    reference = ref(artifact)
    if defect == "object":
        reference = replace(reference, object_id=uuid4())
    elif defect == "version":
        reference = replace(reference, version_id="fs-v1-" + uuid4().hex)
    elif defect == "digest":
        reference = replace(reference, sha256="f" * 64)
    else:
        with psycopg.connect(ctx["admin_dsn"]) as admin:
            if defect == "approval":
                admin.execute(
                    "UPDATE mt.approval_request SET state='REVOKED',row_version=row_version+1 WHERE approval_id=%s",
                    (UUID(approval),),
                )
            else:
                if defect == "size":
                    artifact["size_bytes"] += 1
                else:
                    artifact["expires_at"] = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
                admin.execute(
                    "UPDATE mt.audit_export SET artifact_ref=%s,row_version=row_version+1 WHERE export_id=%s",
                    (Jsonb(artifact), UUID(identifier)),
                )
    spy = SpyStore(app.state.upload_service.store)
    port = scoped_objects()(spy, ctx["control_authority"], export_check=app.state.exports.check)
    target = RuleTarget(ctx["actor"].org_id, "export", UUID(identifier), None, ctx["case_id"], None, None)
    with (
        synthetic_target(ctx, "downloadAuditExport", target),
        app.state.business_database.transaction(scope) as connection,
    ):
        with pytest.raises(BusinessError):
            b"".join(
                port.read(
                    connection, current_data_scope(), ResourceBinding("export_artifact", UUID(identifier)), reference
                )
            )
    assert spy.reads == 0


def test_upload_part_binding_does_not_require_object_version_row(upload_client, business_context):
    ctx = business_context
    upload = UUID(create(upload_client, ctx))
    spy = SpyStore(upload_client.app.state.upload_service.store)
    port = scoped_objects()(spy, ctx["authority"])
    target = RuleTarget(ctx["actor"].org_id, "upload", upload, None, ctx["case_id"], "upload", None)
    with synthetic_target(ctx, "putUploadPart", target):
        stored = port.put(
            ctx["database"],
            Scope(ctx["actor"], ctx["case_id"]),
            ResourceBinding("upload_part", upload, part_no=1),
            io.BytesIO(b"ABC"),
        )
    assert stored.ref.sha256 == hashlib.sha256(b"ABC").hexdigest() and stored.size_bytes == 3
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        assert admin.execute("SELECT count(*) FROM mt.object_version").fetchone() == (0,)
        assert admin.execute("SELECT count(*) FROM mt.upload_part").fetchone() == (0,)
    assert b"".join(spy.wrapped.read(stored.ref)) == b"ABC"
    assert spy.writes == 1


def test_real_conditional_part_write_keeps_publish_and_receipt_in_one_root(control_context, permission_context):
    ctx = control_context
    candidate(ctx, permission_context, ["asset.upload"], role_code="data_admin")
    http = ctx["control_http"]
    upload = create(http, ctx, data=b"ABC")
    response = part(http, upload, 1, b"ABC")
    assert response.status_code == 200, response.json()
    assert response.json()["sha256"] == hashlib.sha256(b"ABC").hexdigest()
    again = part(http, upload, 1, b"ABC")
    assert again.status_code == 200 and again.json() == response.json()


def test_bad_http_part_digest_is_denied_before_any_object_write(upload_client, business_context):
    ctx = business_context
    upload = create(upload_client, ctx)
    response = upload_client.put(
        f"/api/v1/uploads/{upload}/parts/1",
        content=b"ABC",
        headers=dict(AUTH, **{"Idempotency-Key": uuid4().hex, "X-Part-Sha256": "f" * 64, "Content-Length": "3"}),
    )
    assert response.status_code == 422
    root = upload_client.app.state.upload_service.store.root
    records = [json.loads(path.read_text()) for path in root.rglob("*.orphan.json")]
    assert records == [] and list(root.rglob("*.bin")) == []
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        assert admin.execute("SELECT count(*) FROM mt.object_version").fetchone() == (0,)
        assert admin.execute("SELECT count(*) FROM mt.upload_part").fetchone() == (0,)


def test_internal_part_digest_failure_records_exact_unpublished_orphan(upload_client, business_context):
    ctx = business_context
    upload = UUID(create(upload_client, ctx))
    target = RuleTarget(ctx["actor"].org_id, "upload", upload, None, ctx["case_id"], "upload", None)
    service = upload_client.app.state.upload_service
    with synthetic_target(ctx, "putUploadPart", target):
        with pytest.raises(BusinessError) as denied:
            service.put_part(Scope(ctx["actor"], ctx["case_id"]), upload, 1, b"ABC", "f" * 64, uuid4().hex)
    assert denied.value.code == "UPLOAD_PART_DIGEST_INVALID"
    records = [json.loads(path.read_text()) for path in service.store.root.rglob("*.orphan.json")]
    assert len(records) == 1
    assert records[0]["sha256"] == hashlib.sha256(b"ABC").hexdigest() and records[0]["size_bytes"] == 3
    assert records[0]["upload_id"] == str(upload) and records[0]["case_id"] == str(ctx["case_id"])
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        assert admin.execute("SELECT count(*) FROM mt.object_version").fetchone() == (0,)
        assert admin.execute("SELECT count(*) FROM mt.upload_part").fetchone() == (0,)


def test_partial_object_write_is_recorded_without_registering_it(upload_client, business_context):
    ctx = business_context
    upload = UUID(create(upload_client, ctx))

    class BrokenBody:
        reads = 0

        def read(self, size):
            self.reads += 1
            if self.reads == 1:
                return b"ABC"
            raise OSError("synthetic-partial-write")

    store = upload_client.app.state.upload_service.store
    with pytest.raises(OSError, match="synthetic-partial-write"):
        store.put_part(Scope(ctx["actor"], ctx["case_id"]), upload, 1, BrokenBody())
    records = [json.loads(path.read_text()) for path in store.root.rglob("*.orphan.json")]
    assert len(records) == 1
    assert records[0]["sha256"] == hashlib.sha256(b"ABC").hexdigest() and records[0]["size_bytes"] == 3
    assert records[0]["reason"] == "OBJECT_WRITE_INCOMPLETE"


def test_unproven_model_artifact_never_falls_back_to_case_membership(control_context):
    ctx = control_context
    spy = SpyStore(ctx["app"].state.upload_service.store)
    port = scoped_objects()(spy, ctx["authority"])
    target = RuleTarget(ctx["actor"].org_id, "task", ctx["task_id"], 1, ctx["case_id"], None, None)
    with (
        synthetic_target(ctx, "getTask", target),
        ctx["database"].transaction(Scope(ctx["actor"], ctx["case_id"])) as connection,
    ):
        binding = ResourceBinding(
            "model_artifact", UUID(ctx["input_ref"]["object_id"]), task=TaskBinding(ctx["task_id"], 1, 1)
        )
        with pytest.raises(BusinessError) as denied:
            b"".join(port.read(connection, current_data_scope(), binding, ref(ctx["input_ref"])))
        assert denied.value.http_status == 503
    assert spy.reads == 0
