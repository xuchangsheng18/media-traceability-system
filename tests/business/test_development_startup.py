"""A real isolated DB can serve a default-deny development process."""

import json
import os
from pathlib import Path

import pytest
from business_app.development import create_development_app, load_development_settings
from fastapi.testclient import TestClient


def test_development_factory_requires_an_explicit_private_config(monkeypatch):
    monkeypatch.delenv("MT_BUSINESS_DEVELOPMENT_CONFIG", raising=False)
    with pytest.raises(RuntimeError, match="ISOLATED_DEVELOPMENT_STARTUP_FAILED"):
        create_development_app()


@pytest.mark.parametrize(
    "defect",
    ["remote", "remote_hostaddr", "service", "poc", "production", "public_file", "public_directory", "extra_key"],
)
def test_development_configuration_never_falls_back_to_a_shared_target(tmp_path, defect):
    folder = tmp_path / "private"
    folder.mkdir(mode=0o700)
    object_root = folder / "objects"
    values = {
        "MT_BUSINESS_DATABASE_DSN": "host=127.0.0.1 port=35432 dbname=mt_business_preview_test user=not_connected",
        "MT_BUSINESS_OBJECT_ROOT": str(object_root),
        "MT_BUSINESS_MAX_UPLOAD_BYTES": "1048576",
        "MT_BUSINESS_PART_SIZE_BYTES": "256000",
        "MT_BUSINESS_UPLOAD_TTL_SECONDS": "3600",
        "MT_BUSINESS_CURSOR_SECRET": "self-owned-private-config-test-0000000000000000",
    }
    if defect == "remote":
        values["MT_BUSINESS_DATABASE_DSN"] = values["MT_BUSINESS_DATABASE_DSN"].replace("127.0.0.1", "192.0.2.1")
    elif defect == "remote_hostaddr":
        values["MT_BUSINESS_DATABASE_DSN"] += " hostaddr=192.0.2.1"
    elif defect == "service":
        values["MT_BUSINESS_DATABASE_DSN"] += " service=implicit-target"
    elif defect == "poc":
        values["MT_BUSINESS_DATABASE_DSN"] = values["MT_BUSINESS_DATABASE_DSN"].replace(
            "mt_business_preview_test", "media_trace_poc"
        )
    elif defect == "production":
        values["MT_RUNTIME_PROFILE"] = "production"
    record: dict[str, object] = {"business_environment": values}
    if defect == "extra_key":
        record["implicit_authority"] = "forbidden"
    path = folder / "config.json"
    path.write_text(json.dumps(record))
    path.chmod(0o644 if defect == "public_file" else 0o600)
    if defect == "public_directory":
        folder.chmod(0o755)
    with pytest.raises(RuntimeError, match="EXPLICIT_PRIVATE_ISOLATED_DEVELOPMENT_CONFIGURATION_REQUIRED"):
        load_development_settings(path)


def test_development_configuration_pins_loopback_against_libpq_environment(tmp_path, monkeypatch):
    from psycopg.conninfo import conninfo_to_dict

    folder = tmp_path / "private"
    folder.mkdir(mode=0o700)
    values = {
        "MT_BUSINESS_DATABASE_DSN": "host=127.0.0.1 port=35432 dbname=mt_business_preview_test user=not_connected",
        "MT_BUSINESS_OBJECT_ROOT": str(folder / "objects"),
        "MT_BUSINESS_MAX_UPLOAD_BYTES": "1048576",
        "MT_BUSINESS_PART_SIZE_BYTES": "256000",
        "MT_BUSINESS_UPLOAD_TTL_SECONDS": "3600",
        "MT_BUSINESS_CURSOR_SECRET": "self-owned-private-config-test-0000000000000000",
    }
    path = folder / "config.json"
    path.write_text(json.dumps({"business_environment": values}))
    path.chmod(0o600)
    monkeypatch.setenv("PGHOSTADDR", "192.0.2.1")
    target = conninfo_to_dict(load_development_settings(path).database_dsn)
    assert target["hostaddr"] == "127.0.0.1"


@pytest.mark.parametrize("override", ["hostaddr=192.0.2.1", "service=implicit-target"])
def test_prepare_rejects_an_overridden_target_before_any_connection(tmp_path, monkeypatch, override):
    import psycopg

    from scripts.business_development import prepare

    folder = tmp_path / "private"
    folder.mkdir(mode=0o700)
    config = folder / "business-test-postgres-private.json"
    config.write_text(json.dumps({"admin_dsn": "host=127.0.0.1 port=35432 dbname=postgres " + override}))
    config.chmod(0o600)
    calls = []
    monkeypatch.setattr(psycopg, "connect", lambda *args, **kwargs: calls.append(True))
    with pytest.raises(ValueError, match="EXPLICIT_ISOLATED_LOOPBACK_TEST_INSTANCE_REQUIRED"):
        prepare(folder / "new-instance", config)
    assert calls == []
    assert not (folder / "new-instance").exists()


def test_development_factory_uses_real_least_privilege_DB_and_never_installs_mock_authority(
    business_context, tmp_path, monkeypatch
):
    # The factory is intentionally bound to a distinct preview database name;
    # the established fixture's real test database exercises the same settings
    # and role check without creating a shared or persistent preview instance.
    settings = business_context["settings"]
    monkeypatch.setenv("MT_BUSINESS_DEVELOPMENT_CONFIG", str(Path(tmp_path) / "private.json"))
    monkeypatch.setattr("business_app.development.load_development_settings", lambda _: settings)
    with TestClient(create_development_app()) as client:
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
        assert response.headers["WWW-Authenticate"] == "Bearer"
        assert client.get("/openapi.json").status_code == 200
    assert "MT_BUSINESS_DEVELOPMENT_CONFIG" in os.environ
