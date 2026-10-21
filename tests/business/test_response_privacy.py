"""Business responses must not remain in browser or intermediary caches."""

from uuid import uuid4

import pytest
from business_app.main import create_app
from business_app.permissions.guard import authorize_business_route
from business_app.settings import BusinessSettings
from fastapi.testclient import TestClient


@pytest.fixture
def private_response_client(tmp_path):
    settings = BusinessSettings(
        database_dsn="host=127.0.0.1 port=1 dbname=mt_business_test_no_connection",
        object_root=tmp_path / "objects",
        max_upload_bytes=1024,
        part_size_bytes=512,
        upload_ttl_seconds=60,
        cursor_secret=uuid4().hex,
    )
    with TestClient(create_app(settings)) as client:
        yield client


@pytest.mark.parametrize(
    "path,headers,status,code",
    [
        ("/openapi.json", {}, 200, None),
        ("/api/v1/auth/me", {}, 401, "AUTHENTICATION_REQUIRED"),
        ("/api/v1/auth/me", {"Authorization": "Bearer self-owned-no-provider"}, 503, "IDENTITY_AUTHORITY_UNAVAILABLE"),
        ("/does-not-exist", {}, 404, "RESOURCE_NOT_FOUND"),
        ("/api/v1/auth/me", {"X-Request-Id": "invalid"}, 422, "REQUEST_ID_INVALID"),
    ],
)
def test_success_and_failure_responses_are_not_cacheable(private_response_client, path, headers, status, code):
    response = private_response_client.get(path, headers=headers)
    assert response.status_code == status, response.text
    assert response.headers.get("Cache-Control") == "no-store"
    assert response.headers.get("Pragma") == "no-cache"
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Request-Id")
    if code:
        assert response.json()["code"] == code
        assert "self-owned-no-provider" not in response.text


def test_duplicate_request_identifiers_are_not_cached(private_response_client):
    response = private_response_client.get(
        "/api/v1/auth/me", headers=[("X-Request-Id", str(uuid4())), ("X-Request-Id", str(uuid4()))]
    )
    assert response.status_code == 422
    assert response.json()["code"] == "REQUEST_ID_INVALID"
    assert response.headers.get("Cache-Control") == "no-store"


def test_method_rejection_preserves_allow_header_and_no_store(private_response_client):
    response = private_response_client.post("/api/v1/auth/me")
    assert response.status_code == 405
    assert "GET" in response.headers["Allow"]
    assert response.headers.get("Cache-Control") == "no-store"


def test_caller_request_id_remains_bound_to_response(private_response_client):
    request_id = str(uuid4())
    response = private_response_client.get("/api/v1/auth/me", headers={"X-Request-Id": request_id})
    assert response.headers["X-Request-Id"] == request_id
    assert response.json()["request_id"] == request_id
    assert response.headers.get("Cache-Control") == "no-store"


def test_unexpected_exception_is_private_and_not_cacheable(private_response_client):
    def unavailable_dependency():
        raise RuntimeError("self-owned-internal-detail-must-not-be-returned")

    private_response_client.app.dependency_overrides[authorize_business_route] = unavailable_dependency
    response = private_response_client.get("/api/v1/auth/me")
    assert response.status_code == 500
    assert response.json()["code"] == "INTERNAL_ERROR"
    assert response.headers.get("Cache-Control") == "no-store"
    assert "self-owned-internal-detail" not in response.text
