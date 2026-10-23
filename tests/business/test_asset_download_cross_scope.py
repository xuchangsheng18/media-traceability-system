"""Exact download scope refusals on isolated SQL with self-owned fixture records."""

import hashlib
from uuid import UUID, uuid4

import psycopg
import pytest
from business_app.data_scope import ResourceBinding
from business_app.errors import BusinessError
from business_app.scope_context import current_data_scope
from business_app.scoped_objects import ScopedObjects
from business_app.types import ObjectRef, Scope
from fastapi import Request

from tests.business.scoped_history_fixtures import history_read_evidence
from tests.business.test_asset_download import download_context as download_context
from tests.business.test_controls import AUTH
from tests.business.test_controls import control_context as control_context
from tests.business.test_t014_permissions import permission_context as permission_context
from tests.business.test_t015_scope_sql import two_cases


def assert_no_download_audit(ctx):
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        row = admin.execute("SELECT count(*) FROM mt.audit_event WHERE action='asset.download'").fetchone()
        assert row is not None and row[0] == 0


def test_existing_foreign_organization_asset_cannot_be_downloaded(download_context, monkeypatch):
    ctx = download_context
    actor, case = ctx["other_actor"], ctx["other_case_id"]
    source, content, object_id, asset = [uuid4() for _ in range(4)]
    data = b"self-owned foreign-organization download fixture"
    version = "fs-v1-" + uuid4().hex
    digest = hashlib.sha256(data).hexdigest()
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            "INSERT INTO mt.source_registry(source_id,org_id,case_id,name,source_type,authorization_ref,purpose,"
            "authorization_status,authorization_version,created_by) "
            "VALUES(%s,%s,%s,'synthetic-cross-unit','synthetic','self-owned-cross-unit',"
            "ARRAY['analysis','download'],'verified','synthetic/1',%s)",
            (source, actor.org_id, case, actor.user_id),
        )
        admin.execute(
            "INSERT INTO mt.content_item(content_id,org_id,case_id,source_id,discovered_at,status) "
            "VALUES(%s,%s,%s,%s,now(),'synthetic')",
            (content, actor.org_id, case, source),
        )
        admin.execute(
            "INSERT INTO mt.object_version(object_id,org_id,case_id,bucket_alias,object_key,version_id,sha256,"
            "size_bytes,created_by) VALUES(%s,%s,%s,'synthetic-cross-unit',%s,%s,%s,%s,%s)",
            (object_id, actor.org_id, case, str(object_id), version, digest, len(data), actor.user_id),
        )
        admin.execute(
            "INSERT INTO mt.media_asset(asset_id,org_id,case_id,content_id,source_id,object_id,sha256,mime,"
            "size_bytes,kind,mapping_version,state,created_by) "
            "VALUES(%s,%s,%s,%s,%s,%s,%s,'application/octet-stream',%s,'original','synthetic/1','VALID',%s)",
            (asset, actor.org_id, case, content, source, object_id, digest, len(data), actor.user_id),
        )
        assert admin.execute("SELECT org_id,case_id FROM mt.media_asset WHERE asset_id=%s", (asset,)).fetchone() == (
            actor.org_id,
            case,
        )
    reads = []

    def storage_read(reference):
        reads.append(reference)
        return iter((data,))

    monkeypatch.setattr(ctx["control_app"].state.asset_download.store, "read", storage_read)
    response = ctx["control_http"].get(f"/api/v1/assets/{asset}/content", headers=AUTH)
    assert response.status_code == 404, response.text
    assert response.json()["code"] == "RESOURCE_NOT_FOUND"
    assert response.headers["Content-Type"].startswith("application/problem+json")
    assert data not in response.content
    assert reads == []
    assert_no_download_audit(ctx)


@pytest.mark.parametrize("entry", ["download_service", "foreign_object_reference", "foreign_asset_binding"])
def test_download_case_root_cannot_be_reused_for_another_valid_membership(download_context, monkeypatch, entry):
    ctx = download_context
    _, other = two_cases(ctx)
    actor = ctx["actor"]
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        membership = admin.execute(
            "SELECT case_id FROM mt.case_membership WHERE org_id=%s AND user_id=%s "
            "AND case_id=ANY(%s::uuid[]) AND revoked_at IS NULL "
            "AND (expires_at IS NULL OR expires_at>now())",
            (actor.org_id, actor.user_id, [ctx["case_id"], other["case"]]),
        ).fetchall()
        assert {row[0] for row in membership} == {ctx["case_id"], other["case"]}
        admin.execute(
            "UPDATE mt.source_registry SET purpose=array_append(purpose,'download'),row_version=row_version+1 "
            "WHERE source_id=%s",
            (other["source"],),
        )
        stored = admin.execute(
            "SELECT object_id,version_id,sha256 FROM mt.object_version WHERE org_id=%s AND case_id=%s",
            (actor.org_id, other["case"]),
        ).fetchone()
        assert stored is not None
        foreign_reference = ObjectRef(stored[0], stored[1], stored[2])
    service = ctx["control_app"].state.asset_download
    reads: list[ObjectRef] = []
    released: list[bytes] = []

    def storage_read(reference):
        reads.append(reference)
        return iter((b"bytes-must-not-leave-the-wrong-case",))

    monkeypatch.setattr(service.store, "read", storage_read)
    scope = Scope(actor, ctx["case_id"])
    request = Request(
        dict(type="http", method="GET", path=f"/api/v1/assets/{other['asset']}/content", query_string=b"", headers=[])
    )
    with history_read_evidence(scope, "downloadAsset", "asset", UUID(ctx["asset_id"])):
        with service.database.transaction(scope) as connection:
            with pytest.raises(BusinessError) as denied:
                if entry == "download_service":
                    service.content(scope, other["asset"], request)
                else:
                    reference = (
                        foreign_reference
                        if entry == "foreign_object_reference"
                        else ObjectRef(
                            UUID(ctx["input_ref"]["object_id"]),
                            ctx["input_ref"]["version_id"],
                            ctx["input_ref"]["sha256"],
                        )
                    )
                    released.extend(
                        ScopedObjects(service.store, service.authority).read(
                            connection,
                            current_data_scope(),
                            ResourceBinding("asset_content", other["asset"]),
                            reference,
                        )
                    )
            assert (denied.value.code, denied.value.http_status) == ("AUTHORITY_SCOPE_INVALID", 503)
    assert released == []
    assert reads == []
    assert_no_download_audit(ctx)
