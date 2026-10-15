"""Profile validation uses synthetic values, never live credentials or endpoints."""

import pytest
from app.settings import validate_runtime

VALUES = {
    "DATABASE_URL": "postgresql+psycopg://unused:private-dsn-sentinel@127.0.0.1:1/unreachable",
    "BROKER_URL": "amqp://unused:private-broker-sentinel@127.0.0.1:1/test",
    "S3_ENDPOINT": "http://127.0.0.1:1",
    "INFERENCE_URL": "http://127.0.0.1:1",
    "S3_ACCESS_KEY": "self-owned-fake-key-" * 3,
    "S3_SECRET_KEY": "self-owned-fake-secret-" * 3,
    "POC_API_TOKEN": "self-owned-fake-api-" * 3,
    "INTERNAL_TOKEN": "self-owned-fake-internal-" * 3,
}


@pytest.fixture(autouse=True)
def synthetic_environment(monkeypatch):
    for key, value in VALUES.items():
        monkeypatch.setenv(key, value)
    monkeypatch.delenv("MT_RUNTIME_PROFILE", raising=False)


@pytest.mark.parametrize("profile", ["production", "unexpected"])
def test_unapproved_or_unknown_runtime_profile_is_rejected(monkeypatch, profile):
    monkeypatch.setenv("MT_RUNTIME_PROFILE", profile)
    with pytest.raises(RuntimeError, match="PRODUCTION_PROFILE_NOT_APPROVED|CONFIGURATION_INVALID"):
        validate_runtime()


@pytest.mark.parametrize("profile", ["development", "test"])
def test_valid_profile_is_explicit_and_private_urls_are_hidden(monkeypatch, profile):
    monkeypatch.setenv("MT_RUNTIME_PROFILE", profile)
    config = validate_runtime()
    assert getattr(config, "runtime_profile", None) == profile
    assert "private-dsn-sentinel" not in repr(config)
    assert "private-broker-sentinel" not in repr(config)
    assert "private-dsn-sentinel" not in config.model_dump_json()


def test_missing_required_setting_has_safe_failure(monkeypatch):
    monkeypatch.delenv("DATABASE_URL")
    with pytest.raises(RuntimeError, match="^CONFIGURATION_INVALID$") as error:
        validate_runtime()
    assert "self-owned" not in str(error.value)


def test_business_config_has_explicit_fail_closed_environment_loader():
    import business_app.settings as settings

    loader = getattr(settings, "load_business_settings", None)
    assert callable(loader), "business environment loader is missing"
    with pytest.raises(RuntimeError, match="BUSINESS_CONFIGURATION_INVALID"):
        loader({"MT_RUNTIME_PROFILE": "test"})


def test_business_environment_loader_validates_profile_and_private_fields(tmp_path):
    import business_app.settings as settings

    loader = getattr(settings, "load_business_settings", None)
    assert callable(loader), "business environment loader is missing"
    values = {
        "MT_RUNTIME_PROFILE": "test",
        "MT_BUSINESS_DATABASE_DSN": "host=127.0.0.1 port=1 dbname=mt_business_unreachable user=unused password=private-config-sentinel",
        "MT_BUSINESS_OBJECT_ROOT": str(tmp_path / "objects"),
        "MT_BUSINESS_MAX_UPLOAD_BYTES": "1024",
        "MT_BUSINESS_PART_SIZE_BYTES": "512",
        "MT_BUSINESS_UPLOAD_TTL_SECONDS": "60",
        "MT_BUSINESS_CURSOR_SECRET": "self-owned-private-cursor-secret-" * 2,
    }
    config = loader(values)
    assert config.runtime_profile == "test"
    assert "private-config-sentinel" not in repr(config)
    malformed = dict(values, MT_BUSINESS_DATABASE_DSN="invalid private-config-sentinel")
    with pytest.raises(RuntimeError, match="^BUSINESS_CONFIGURATION_INVALID$"):
        loader(malformed)
    values["MT_RUNTIME_PROFILE"] = "production"
    with pytest.raises(RuntimeError, match="PRODUCTION_PROFILE_NOT_APPROVED"):
        loader(values)
