"""Controlled downloads against isolated SQL and self-owned image bytes only."""

import hashlib
from dataclasses import replace
from uuid import UUID, uuid4

import psycopg
import pytest

from tests.business.t014_positive_fixtures import candidate
from tests.business.test_controls import AUTH
from tests.business.test_controls import control_context as control_context
from tests.business.test_t014_permissions import permission_context as permission_context


@pytest.fixture
def download_context(request):
    ctx = request.getfixturevalue("control_context")
    permissions = request.getfixturevalue("permission_context")
    configured, objects, authority, facts = candidate(ctx, permissions, ["asset.download"])
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            "UPDATE mt.source_registry SET purpose=array_append(purpose,'download') WHERE source_id=%s",
            (ctx["source_id"],),
        )
    return dict(ctx, configured=configured, object_facts=objects, conditions=authority, facts=facts)


def content_path(ctx):
    ref = ctx["input_ref"]
    return ctx["settings"].object_root / ref["object_id"] / (ref["version_id"] + ".bin")


def download(ctx, headers=None, query=""):
    return ctx["control_http"].get(
        f"/api/v1/assets/{ctx['asset_id']}/content" + query, headers={**AUTH, **(headers or {})}
    )


def download_audits(ctx):
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        return admin.execute(
            "SELECT action,object_type,object_id,object_version,outcome,request_id FROM mt.audit_event "
            "WHERE object_id=%s AND action='asset.download' ORDER BY occurred_at",
            (ctx["asset_id"],),
        ).fetchall()


def test_full_download_verifies_exact_bytes_and_appends_request_audit(download_context):
    ctx = download_context
    request_id = str(uuid4())
    response = download(ctx, {"X-Request-Id": request_id})
    assert response.status_code == 200, response.text
    assert response.content == content_path(ctx).read_bytes()
    assert hashlib.sha256(response.content).hexdigest() == ctx["input_ref"]["sha256"]
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["Content-Type"] == "application/octet-stream"
    assert response.headers["Content-Disposition"] == f'attachment; filename="asset-{ctx["asset_id"]}.bin"'
    assert response.headers["ETag"] and response.headers["Accept-Ranges"] == "bytes"
    rows = download_audits(ctx)
    assert len(rows) == 1 and rows[0][:3] == ("asset.download", "asset", UUID(ctx["asset_id"]))
    assert rows[0][4:] == ("allowed", UUID(request_id))


@pytest.mark.parametrize("raw", ["bytes=1-4", "bytes=-4", "bytes=2-"])
def test_range_has_exact_version_bytes_and_audit(download_context, raw):
    ctx = download_context
    data = content_path(ctx).read_bytes()
    response = download(ctx, {"Range": raw})
    assert response.status_code == 206, response.text
    left, right = response.headers["Content-Range"].split()[1].split("/")[0].split("-")
    assert response.content == data[int(left) : int(right) + 1]
    assert response.headers["Content-Range"].endswith("/" + str(len(data)))
    assert len(download_audits(ctx)) == 1


def test_if_range_mismatch_returns_entire_verified_object(download_context):
    ctx = download_context
    response = download(ctx, {"Range": "bytes=0-1", "If-Range": '"old-version"'})
    assert response.status_code == 200
    assert response.content == content_path(ctx).read_bytes()
    assert "Content-Range" not in response.headers


@pytest.mark.parametrize("raw", ["bytes=0-1,3-4", "bytes=999999-", "bytes=-0", "bytes=4-1"])
def test_invalid_range_releases_no_content_or_allowed_audit(download_context, raw):
    ctx = download_context
    response = download(ctx, {"Range": raw})
    assert response.status_code == 416, response.text
    assert response.json()["code"] == "RANGE_INVALID"
    assert not download_audits(ctx)


@pytest.mark.parametrize("query", ["?case_id=forged", "?download=1", "?actor_id=forged"])
def test_download_rejects_any_client_query_scope(download_context, query):
    response = download(download_context, query=query)
    assert response.status_code == 422 and response.json()["code"] == "READ_PARAMETER_UNSUPPORTED"
    assert not download_audits(download_context)


@pytest.mark.parametrize(
    "headers", [[("Range", "bytes=0-1"), ("Range", "bytes=2-3")], [("If-Range", '"one"'), ("If-Range", '"two"')]]
)
def test_duplicate_range_headers_reject(download_context, headers):
    ctx = download_context
    response = ctx["control_http"].get(
        f"/api/v1/assets/{ctx['asset_id']}/content", headers=list(AUTH.items()) + headers
    )
    assert response.status_code == 422 and response.json()["code"] == "INPUT_INVALID"
    assert not download_audits(ctx)


def test_download_requires_authenticated_identity(download_context):
    ctx = download_context
    response = ctx["control_http"].get(f"/api/v1/assets/{ctx['asset_id']}/content")
    assert response.status_code == 401 and not download_audits(ctx)


def test_classification_denial_releases_no_bytes(download_context):
    ctx = download_context
    ctx["facts"].blocked = {UUID(ctx["asset_id"])}
    response = download(ctx)
    assert response.status_code == 403, response.text
    assert response.json()["code"] == "PERMISSION_REQUIRED" and not download_audits(ctx)


def test_source_without_download_purpose_is_denied(download_context):
    ctx = download_context
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute("UPDATE mt.source_registry SET purpose=ARRAY['analysis'] WHERE source_id=%s", (ctx["source_id"],))
    response = download(ctx)
    assert response.status_code == 403 and not download_audits(ctx)


@pytest.mark.parametrize("defect", ["hash", "size", "missing"])
def test_fixed_object_binding_defect_fails_before_bytes(download_context, defect):
    ctx = download_context
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        if defect == "hash":
            # A new self-owned malformed binding leaves the original asset's
            # protected provenance intact and references its registered object.
            identifier = uuid4()
            inserted = admin.execute(
                "INSERT INTO mt.media_asset(asset_id,org_id,case_id,content_id,source_id,object_id,sha256,mime,"
                "size_bytes,kind,mapping_version,state,created_by) "
                "SELECT %s,org_id,case_id,content_id,source_id,object_id,repeat('0',64),mime,size_bytes,kind,"
                "mapping_version,state,created_by FROM mt.media_asset WHERE asset_id=%s RETURNING asset_id",
                (identifier, ctx["asset_id"]),
            ).fetchone()
            assert inserted is not None
            ctx = dict(ctx, asset_id=str(inserted[0]))
        elif defect == "size":
            admin.execute("UPDATE mt.media_asset SET size_bytes=size_bytes+1 WHERE asset_id=%s", (ctx["asset_id"],))
        else:
            content_path(ctx).unlink()
    response = download(ctx)
    assert response.status_code == 503 and not download_audits(ctx)


def test_corrupt_tail_rejects_even_when_range_requests_only_valid_prefix(download_context):
    ctx = download_context
    path = content_path(ctx)
    data = path.read_bytes()
    path.write_bytes(data[:-1] + bytes([data[-1] ^ 1]))
    response = download(ctx, {"Range": "bytes=0-1"})
    assert response.status_code == 503 and not download_audits(ctx)


def test_explicit_development_resource_limit_precedes_object_read(download_context, monkeypatch):
    ctx = download_context
    service = ctx["control_app"].state.asset_download
    monkeypatch.setattr(service, "settings", replace(service.settings, max_upload_bytes=1))
    response = download(ctx)
    assert response.status_code == 503, response.text
    assert response.json()["code"] == "ASSET_DOWNLOAD_DEVELOPMENT_LIMIT_EXCEEDED"
    assert not download_audits(ctx)


def test_final_authorization_change_rolls_back_audit_before_response(download_context, monkeypatch):
    ctx = download_context
    store = ctx["control_app"].state.upload_service.store
    original = store.read

    def revoked(reference):
        yield from original(reference)
        ctx["facts"].blocked = {UUID(ctx["asset_id"])}

    monkeypatch.setattr(store, "read", revoked)
    response = download(ctx)
    assert response.status_code == 403, response.text
    assert not download_audits(ctx)


def test_storage_exception_is_redacted_and_never_audited_allowed(download_context, monkeypatch):
    ctx = download_context

    def unavailable(reference):
        raise OSError("private-storage-path-must-not-leak")
        yield b""

    monkeypatch.setattr(ctx["control_app"].state.upload_service.store, "read", unavailable)
    response = download(ctx)
    assert response.status_code == 503
    assert "private-storage" not in response.text and not download_audits(ctx)


def test_nonvalid_asset_does_not_download(download_context):
    ctx = download_context
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute("UPDATE mt.media_asset SET state='QUARANTINED' WHERE asset_id=%s", (ctx["asset_id"],))
    response = download(ctx)
    assert response.status_code == 409, response.text
    assert response.json()["code"] == "ASSET_STATE_CONFLICT" and not download_audits(ctx)


@pytest.mark.parametrize("target", ["object_version", "media_asset"])
def test_registered_objects_and_assets_reject_zero_size_and_roll_back(download_context, target):
    ctx = download_context
    identifier = uuid4()
    digest = hashlib.sha256(b"").hexdigest()
    with pytest.raises(psycopg.errors.CheckViolation):
        with psycopg.connect(ctx["admin_dsn"]) as admin:
            if target == "object_version":
                admin.execute(
                    "INSERT INTO mt.object_version(object_id,org_id,case_id,bucket_alias,object_key,version_id,"
                    "sha256,size_bytes,created_by) VALUES(%s,%s,%s,'synthetic-zero-rejected',%s,%s,%s,0,%s)",
                    (
                        identifier,
                        ctx["actor"].org_id,
                        ctx["case_id"],
                        str(identifier),
                        "fs-v1-" + uuid4().hex,
                        digest,
                        ctx["actor"].user_id,
                    ),
                )
            else:
                admin.execute(
                    "INSERT INTO mt.media_asset(asset_id,org_id,case_id,content_id,source_id,object_id,sha256,mime,"
                    "size_bytes,kind,mapping_version,state,created_by) "
                    "SELECT %s,org_id,case_id,content_id,source_id,object_id,%s,mime,0,kind,mapping_version,state,"
                    "created_by FROM mt.media_asset WHERE asset_id=%s",
                    (identifier, digest, ctx["asset_id"]),
                )
    # The current SQL registration path requires positive sizes. Pure helper
    # tests retain the empty-byte integrity and 200/416 range boundary coverage.
    key = "object_id" if target == "object_version" else "asset_id"
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        assert admin.execute(f"SELECT 1 FROM mt.{target} WHERE {key}=%s", (identifier,)).fetchone() is None
    assert not download_audits(ctx)


def test_function_permission_denial_precedes_storage(download_context):
    ctx = download_context
    with psycopg.connect(ctx["admin_dsn"]) as admin:
        admin.execute(
            "UPDATE mt.role_permissions SET revoked_at=now(),row_version=row_version+1 "
            "WHERE permission_id=(SELECT permission_id FROM mt.permissions WHERE code='asset.download') "
            "AND revoked_at IS NULL"
        )
    response = download(ctx)
    assert response.status_code == 403 and not download_audits(ctx)


def test_unknown_asset_does_not_disclose_registered_bytes(download_context):
    ctx = download_context
    response = ctx["control_http"].get(f"/api/v1/assets/{uuid4()}/content", headers=AUTH)
    assert response.status_code == 404 and not download_audits(ctx)
