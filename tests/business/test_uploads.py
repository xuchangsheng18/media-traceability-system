import hashlib
from dataclasses import replace
from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient

AUTH = {"Authorization": "Bearer test-only-valid-token"}


@pytest.fixture
def upload_client(business_context):
    from business_app.main import create_app

    with TestClient(
        create_app(replace(business_context["settings"], part_size_bytes=3), business_context["authority"])
    ) as http:
        yield http


def create(http, context, data=b"ABCDEF", key="create-one"):
    response = http.post(
        "/api/v1/uploads",
        headers={**AUTH, "Idempotency-Key": key},
        json={
            "case_id": str(context["case_id"]),
            "source_id": str(context["source_id"]),
            "filename": "synthetic.bin",
            "size_bytes": len(data),
            "mime": "image/png",
            "sha256": hashlib.sha256(data).hexdigest(),
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["upload_id"]


def part(http, upload_id, number, data, key=None):
    return http.put(
        f"/api/v1/uploads/{upload_id}/parts/{number}",
        content=data,
        headers={
            **AUTH,
            "Idempotency-Key": key or f"part-{number}",
            "X-Part-Sha256": hashlib.sha256(data).hexdigest(),
            "Content-Length": str(len(data)),
            "Content-Type": "application/octet-stream",
        },
    )


def test_resume_after_client_disconnect(upload_client, business_context):
    upload = create(upload_client, business_context)
    assert part(upload_client, upload, 1, b"ABC").status_code == 200
    progress = upload_client.get(f"/api/v1/uploads/{upload}", headers=AUTH)
    assert progress.status_code == 200
    assert progress.json()["received_parts_count"] == 1
    assert progress.json()["received_bytes"] == 3
    assert progress.json()["result"] is None
    assert part(upload_client, upload, 2, b"DEF").status_code == 200
    page = upload_client.get(f"/api/v1/uploads/{upload}/parts", headers=AUTH).json()
    assert [item["part_no"] for item in page["items"]] == [1, 2]


def test_same_part_hash_is_idempotent(upload_client, business_context):
    upload = create(upload_client, business_context)
    first = part(upload_client, upload, 1, b"ABC")
    second = part(upload_client, upload, 1, b"ABC")
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    progress = upload_client.get(f"/api/v1/uploads/{upload}", headers=AUTH).json()
    assert progress["received_parts_count"] == 1
    assert progress["received_bytes"] == 3
    assert len(list(business_context["settings"].object_root.rglob("*.bin"))) == 1


def test_conflicting_part_is_409(upload_client, business_context):
    upload = create(upload_client, business_context)
    assert part(upload_client, upload, 1, b"ABC").status_code == 200
    assert part(upload_client, upload, 1, b"XYZ", "different-key").status_code == 409
    items = upload_client.get(f"/api/v1/uploads/{upload}/parts", headers=AUTH).json()["items"]
    assert items[0]["sha256"] == hashlib.sha256(b"ABC").hexdigest()


def test_expired_session_is_rejected(upload_client, business_context):
    upload = create(upload_client, business_context)
    with psycopg.connect(business_context["admin_dsn"]) as connection:
        connection.execute(
            "UPDATE mt.upload_session SET expires_at=now()-interval '1 second' WHERE upload_id=%s", (upload,)
        )
    assert part(upload_client, upload, 1, b"ABC").status_code == 410
    assert not list(business_context["settings"].object_root.rglob("*.bin"))


def test_DB_failure_does_not_report_received(upload_client, business_context):
    upload = create(upload_client, business_context)
    with psycopg.connect(business_context["admin_dsn"]) as connection:
        connection.execute("REVOKE INSERT ON mt.upload_part FROM mt_runtime")
    try:
        response = part(upload_client, upload, 1, b"ABC")
        assert response.status_code == 503
    finally:
        with psycopg.connect(business_context["admin_dsn"]) as connection:
            connection.execute("GRANT INSERT ON mt.upload_part TO mt_runtime")
    progress = upload_client.get(f"/api/v1/uploads/{upload}", headers=AUTH).json()
    assert progress["received_parts_count"] == progress["received_bytes"] == 0
    assert len(list(business_context["settings"].object_root.rglob("*.orphan.json"))) == 1


def test_cursor_bound_to_session_version(upload_client, business_context):
    upload = create(upload_client, business_context, b"ABCDEFGHI")
    assert part(upload_client, upload, 1, b"ABC").status_code == 200
    assert part(upload_client, upload, 2, b"DEF").status_code == 200
    page = upload_client.get(f"/api/v1/uploads/{upload}/parts?limit=1", headers=AUTH).json()
    assert page["next_cursor"]
    assert part(upload_client, upload, 3, b"GHI").status_code == 200
    response = upload_client.get(
        f"/api/v1/uploads/{upload}/parts", params={"cursor": page["next_cursor"]}, headers=AUTH
    )
    assert response.status_code == 409


def test_cross_case_read_denied(upload_client, business_context):
    upload = create(upload_client, business_context)
    with psycopg.connect(business_context["admin_dsn"]) as connection:
        connection.execute(
            "UPDATE mt.case_membership SET revoked_at=now() WHERE case_id=%s", (business_context["case_id"],)
        )
    assert upload_client.get(f"/api/v1/uploads/{upload}", headers=AUTH).status_code == 404
    assert upload_client.get(f"/api/v1/uploads/{uuid4()}", headers=AUTH).status_code == 404
