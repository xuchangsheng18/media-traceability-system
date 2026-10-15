"""In-memory HTTP boundary checks; no live database or business authority is used."""

from pathlib import Path
from uuid import UUID

import pytest
from business_app.errors import BusinessError
from business_app.main import create_app
from business_app.settings import BusinessSettings
from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException


@pytest.fixture
def boundary(tmp_path: Path):
    app = create_app(
        BusinessSettings(
            database_dsn="host=127.0.0.1 port=1 dbname=mt_business_boundary user=unused",
            object_root=tmp_path / "objects",
            max_upload_bytes=1024,
            part_size_bytes=512,
            upload_ttl_seconds=60,
            cursor_secret="self-owned-unreachable-boundary-test-key",
        )
    )

    @app.get("/boundary/unknown")
    def unknown():
        raise RuntimeError("private-sentinel-not-for-response")

    @app.get("/boundary/http")
    def http_error():
        raise HTTPException(403, detail="private-sentinel-not-for-response")

    @app.get("/boundary/known")
    def known():
        raise BusinessError("DATABASE_UNAVAILABLE", 503)

    @app.get("/boundary/ok")
    def ok():
        return {"ok": True}

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


@pytest.mark.parametrize(
    "path,status,code",
    [
        ("/boundary/unknown", 500, "INTERNAL_ERROR"),
        ("/boundary/missing", 404, "RESOURCE_NOT_FOUND"),
        ("/boundary/http", 403, "HTTP_FORBIDDEN"),
        ("/boundary/known", 503, "DATABASE_UNAVAILABLE"),
    ],
)
def test_all_error_paths_have_safe_uniform_problem(boundary, path, status, code):
    response = boundary.get(path)
    assert response.status_code == status
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert {"code", "message", "request_id", "details"} <= body.keys()
    assert body["code"] == code and body["details"] == []
    assert UUID(body["request_id"])
    assert response.headers["X-Request-Id"] == body["request_id"]
    assert "private-sentinel" not in response.text


def test_method_not_allowed_is_uniform_and_preserves_allow(boundary):
    response = boundary.post("/boundary/ok")
    assert response.status_code == 405
    assert response.json()["code"] == "METHOD_NOT_ALLOWED"
    assert "GET" in response.headers["Allow"]


def test_invalid_request_id_is_safe_and_has_matching_header(boundary):
    response = boundary.get("/boundary/ok", headers={"X-Request-Id": "private-invalid-value"})
    assert response.status_code == 422
    assert response.headers["X-Request-Id"] == response.json()["request_id"]
    assert "private-invalid-value" not in response.text


@pytest.mark.parametrize("code,status", [("UNREGISTERED_ERROR", 500), ("DATABASE_UNAVAILABLE", 400)])
def test_unknown_or_inconsistent_error_registration_is_rejected(code, status):
    with pytest.raises(ValueError, match="ERROR_CODE_UNREGISTERED_OR_STATUS_MISMATCH"):
        BusinessError(code, status)


def test_duplicate_error_definitions_are_rejected():
    import business_app.errors as errors

    validator = getattr(errors, "validate_error_definitions", None)
    assert callable(validator), "unique error registry is missing"
    with pytest.raises(ValueError, match="ERROR_CODE_DEFINITION_INVALID"):
        validator([("DUPLICATE", 400), ("DUPLICATE", 400)])
