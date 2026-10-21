"""Expired metadata remains inspectable; active source uses still fail closed.

Expected RED before the fix: ObjectFactsReader reduces every source fact's
valid_until to its past expires_at; ConditionalPermissionAuthority._facts raises
CONDITIONAL_FACTS_UNAVAILABLE before getSource/listSources can project expired.
Only SOURCE metadata reads should change. SOURCE_WRITE and media-use deadlines
must retain their existing refusal behavior.
"""

import hashlib
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import psycopg
import pytest
from business_app.contracts import validate_response
from business_app.data_scope import ResourceBinding
from business_app.errors import BusinessError
from business_app.permissions.context import request_authorization
from business_app.permissions.object_facts import digest
from business_app.permissions.rule_types import ConditionFacts
from business_app.scope_context import current_data_scope
from business_app.scoped_objects import ScopedObjects
from business_app.types import ObjectRef, Scope

from tests.business.t014_positive_fixtures import candidate
from tests.business.test_controls import AUTH
from tests.business.test_controls import control_context as control_context
from tests.business.test_t014_permissions import permission_context as permission_context


@pytest.fixture
def source_metadata_context(request):
    ctx = request.getfixturevalue("control_context")
    permissions = request.getfixturevalue("permission_context")
    configured, objects, conditions, facts = candidate(
        ctx, permissions, ["source.read", "asset.upload", "asset.download", "task.read"]
    )
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            "UPDATE mt.source_registry SET authorization_status='verified',"
            "purpose=ARRAY['upload','download','analysis'],expires_at=%s,row_version=row_version+1 WHERE source_id=%s",
            (datetime.now(timezone.utc) + timedelta(hours=1), ctx["source_id"]),
        )
    return dict(ctx, configured=configured, object_facts=objects, conditions=conditions, facts=facts)


def expire_source(ctx):
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            "UPDATE mt.source_registry SET expires_at=now()-interval '1 second',"
            "row_version=row_version+1 WHERE source_id=%s",
            (ctx["source_id"],),
        )
        assert admin.execute(
            "SELECT authorization_status,expires_at<now() FROM mt.source_registry WHERE source_id=%s",
            (ctx["source_id"],),
        ).fetchone() == ("verified", True)


def metadata(ctx, kind, *, source=None, case=None):
    if kind == "detail":
        return ctx["control_http"].get(f"/api/v1/sources/{source or ctx['source_id']}", headers=AUTH)
    return ctx["control_http"].get("/api/v1/sources", params={"case_id": str(case or ctx["case_id"])}, headers=AUTH)


@pytest.mark.parametrize("kind", ["detail", "list"])
def test_naturally_expired_verified_source_metadata_remains_readable(source_metadata_context, kind):
    ctx = source_metadata_context
    before = metadata(ctx, kind)
    assert before.status_code == 200, before.json()
    expire_source(ctx)
    response = metadata(ctx, kind)
    assert response.status_code == 200, response.json()
    value = response.json()
    validate_response("Source" if kind == "detail" else "SourcePage", value)
    item = (
        value if kind == "detail" else next(row for row in value["items"] if row["source_id"] == str(ctx["source_id"]))
    )
    assert item["authorization_status"] == "expired"
    assert datetime.fromisoformat(item["expires_at"]) < datetime.now(timezone.utc)
    assert item["case_id"] == str(ctx["case_id"])
    assert response.headers["Cache-Control"] == "no-store" and response.headers["ETag"]


@pytest.mark.parametrize("kind", ["detail", "list"])
def test_revoked_source_metadata_remains_readable(source_metadata_context, kind):
    ctx = source_metadata_context
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            "UPDATE mt.source_registry SET authorization_status='revoked',expires_at=NULL,"
            "row_version=row_version+1 WHERE source_id=%s",
            (ctx["source_id"],),
        )
    response = metadata(ctx, kind)
    assert response.status_code == 200, response.json()
    value = response.json()
    validate_response("Source" if kind == "detail" else "SourcePage", value)
    item = (
        value if kind == "detail" else next(row for row in value["items"] if row["source_id"] == str(ctx["source_id"]))
    )
    assert item["authorization_status"] == "revoked"


@pytest.mark.parametrize("foreign_org", [False, True])
@pytest.mark.parametrize("kind", ["detail", "list"])
def test_source_metadata_expiry_fix_does_not_widen_case_or_organization_scope(
    source_metadata_context, foreign_org, kind
):
    ctx = source_metadata_context
    source = uuid4()
    if foreign_org:
        org, case, creator = ctx["other_actor"].org_id, ctx["other_case_id"], ctx["other_actor"].user_id
    else:
        org, case, creator = ctx["actor"].org_id, uuid4(), ctx["reviewers"][0].user_id
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        if not foreign_org:
            admin.execute(
                "INSERT INTO mt.cases(case_id,org_id,display_code,status) VALUES(%s,%s,%s,'ACTIVE')",
                (case, org, "unassigned-source-case-" + uuid4().hex),
            )
        admin.execute(
            "INSERT INTO mt.source_registry(source_id,org_id,case_id,name,source_type,authorization_ref,purpose,"
            "authorization_status,authorization_version,expires_at,created_by) "
            "VALUES(%s,%s,%s,'synthetic foreign source','synthetic','self-owned-fixture',ARRAY['analysis'],"
            "'verified','synthetic/1',now()-interval '1 second',%s)",
            (source, org, case, creator),
        )
    response = metadata(ctx, kind, source=source, case=case)
    assert response.status_code == 404, response.json()
    assert not {"source_id", "items", "next_cursor"} & response.json().keys()


def test_expired_source_still_blocks_upload_registration(source_metadata_context):
    ctx = source_metadata_context
    body = dict(
        case_id=str(ctx["case_id"]),
        source_id=str(ctx["source_id"]),
        filename="self-owned.png",
        size_bytes=1,
        sha256="a" * 64,
        mime="image/png",
    )
    before = ctx["control_http"].post(
        "/api/v1/uploads", json=body, headers=dict(AUTH, **{"Idempotency-Key": uuid4().hex})
    )
    assert before.status_code == 201, before.json()
    expire_source(ctx)
    response = ctx["control_http"].post(
        "/api/v1/uploads", json=body, headers=dict(AUTH, **{"Idempotency-Key": uuid4().hex})
    )
    assert response.status_code == 503 and response.json()["code"] == "CONDITIONAL_FACTS_UNAVAILABLE"
    assert "upload_id" not in response.json()


def test_expired_source_still_blocks_download(source_metadata_context):
    ctx = source_metadata_context
    path = f"/api/v1/assets/{ctx['asset_id']}/content"
    before = ctx["control_http"].get(path, headers=AUTH)
    assert before.status_code == 200, before.text
    assert hashlib.sha256(before.content).hexdigest() == ctx["input_ref"]["sha256"]
    expire_source(ctx)
    response = ctx["control_http"].get(path, headers=AUTH)
    assert response.status_code == 503 and response.json()["code"] == "CONDITIONAL_FACTS_UNAVAILABLE"
    assert response.headers["Content-Type"].startswith("application/problem+json")


def test_expired_source_still_blocks_media_read_for_analysis(source_metadata_context):
    ctx = source_metadata_context
    database = ctx["control_app"].state.business_database
    scope = Scope(ctx["actor"], ctx["case_id"])
    reference = ObjectRef(
        UUID(ctx["input_ref"]["object_id"]), ctx["input_ref"]["version_id"], ctx["input_ref"]["sha256"]
    )

    def analysis_input():
        proof = ctx["conditions"].authorize_http(
            ctx["configured"]["principal"], "getTask", {"id": str(ctx["task_id"])}, {}, {}
        )
        with request_authorization(proof, ctx["control_app"].state.authorization_fence, mutation=False):
            with database.transaction(scope) as connection:
                return b"".join(
                    ScopedObjects(
                        ctx["control_app"].state.upload_service.store, ctx["control_app"].state.business_authority
                    ).read(
                        connection,
                        current_data_scope(),
                        ResourceBinding("media_input", UUID(ctx["asset_id"])),
                        reference,
                    )
                )

    assert hashlib.sha256(analysis_input()).hexdigest() == ctx["input_ref"]["sha256"]
    expire_source(ctx)
    with pytest.raises(BusinessError) as error:
        analysis_input()
    assert (error.value.http_status, error.value.code) == (503, "CONDITIONAL_FACTS_UNAVAILABLE")


def test_expired_source_write_keeps_its_existing_deadline(request):
    ctx = request.getfixturevalue("control_context")
    permissions = request.getfixturevalue("permission_context")
    _, objects, _, facts = candidate(ctx, permissions, ["source.manage"], role_code="data_admin")

    class SyntheticSourceWriteScope:
        def read(self, principal, operation_id, target, *, connection):
            previous = facts.read(principal, operation_id, target, connection=connection)
            checks = dict(previous.checks, authoritative_source_sync=True)
            return ConditionFacts(principal, target, checks, digest([target, checks]), previous.valid_until)

    objects.supplemental = SyntheticSourceWriteScope()
    path = f"/api/v1/sources/{ctx['source_id']}/authorization/sync"
    body = {"expected_version": 1}
    headers = dict(AUTH, **{"Idempotency-Key": uuid4().hex})
    # An active source passes SOURCE_WRITE and reaches the deliberately absent adapter.
    before = ctx["control_http"].post(path, json=body, headers=headers)
    assert before.status_code == 503 and before.json()["code"] == "SOURCE_SYNCHRONIZATION_UNAVAILABLE"
    expire_source(ctx)
    response = ctx["control_http"].post(path, json=body, headers=headers)
    assert response.status_code == 503 and response.json()["code"] == "CONDITIONAL_FACTS_UNAVAILABLE"
