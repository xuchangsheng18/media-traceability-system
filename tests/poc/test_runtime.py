import base64
import io
import os
from pathlib import Path

import pytest
from PIL import Image

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://unused:unused@127.0.0.1:1/unused")
from app.common import decode_image  # noqa: E402
from app.main import authorize  # noqa: E402


def test_reject_non_image_bytes():
    with pytest.raises(ValueError, match="INVALID_IMAGE"):
        decode_image(base64.b64encode(b"not an image").decode())


def test_valid_png_preserves_original_bytes():
    buffer = io.BytesIO()
    Image.new("RGB", (32, 32), "blue").save(buffer, "PNG")
    raw = buffer.getvalue()
    assert decode_image(base64.b64encode(raw).decode()) == raw


def test_missing_and_wrong_bearer_are_denied(monkeypatch):
    monkeypatch.setenv("POC_API_TOKEN", "synthetic-unit-token")
    from fastapi import HTTPException
    with pytest.raises(HTTPException):
        authorize(None)
    with pytest.raises(HTTPException):
        authorize("Bearer invalid")
    assert authorize("Bearer synthetic-unit-token") is None


def test_python_runtime_is_310():
    import sys
    assert sys.version_info[:2] == (3, 10)


def test_environment_path_is_explicit():
    assert Path("/opt/conda/glwy/envs/py310/bin/python").is_file()


def test_auth_error_has_traceable_safe_problem(monkeypatch):
    from app.main import app
    from fastapi.testclient import TestClient
    monkeypatch.setenv("POC_API_TOKEN", "synthetic-unit-token")
    response = TestClient(app).get("/api/v1/health", headers={"Authorization": "Bearer secret-value"})
    assert response.status_code == 401
    assert response.json()["code"] == "AUTH_REQUIRED"
    assert response.headers["x-request-id"] == response.json()["request_id"]
    assert "secret-value" not in response.text


def test_configuration_rejects_invalid_values_without_disclosing_secrets(monkeypatch):
    from app.settings import validate_runtime
    monkeypatch.setenv("POC_API_TOKEN", "secret-invalid-short-token")
    monkeypatch.setenv("BROKER_URL", "not-a-url")
    with pytest.raises(RuntimeError, match="^CONFIGURATION_INVALID$"):
        validate_runtime()


def test_unexpected_case_override_is_rejected_before_database_access(monkeypatch):
    import uuid
    from fastapi.testclient import TestClient
    from app.main import app
    monkeypatch.setenv("POC_API_TOKEN", "synthetic-unit-token")
    response = TestClient(app).post("/poc/jobs", headers={"Authorization": "Bearer synthetic-unit-token", "Idempotency-Key": "test"},
                                    json={"asset_id": str(uuid.uuid4()), "case_id": str(uuid.uuid4())})
    assert response.status_code == 422 and response.json()["code"] == "REQUEST_INVALID"
