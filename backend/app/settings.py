"""Validate private runtime configuration without displaying secret field values."""

from typing import Literal

from pydantic import AmqpDsn, AnyHttpUrl, Field, PostgresDsn, SecretStr, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class RuntimeSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")
    runtime_profile: Literal["development", "test", "production"] = Field(
        default="development", alias="MT_RUNTIME_PROFILE"
    )
    database_url: PostgresDsn = Field(alias="DATABASE_URL", repr=False, exclude=True)
    broker_url: AmqpDsn = Field(alias="BROKER_URL", repr=False, exclude=True)
    s3_endpoint: AnyHttpUrl = Field(alias="S3_ENDPOINT", repr=False, exclude=True)
    inference_url: AnyHttpUrl = Field(alias="INFERENCE_URL", repr=False, exclude=True)
    s3_access_key: SecretStr = Field(alias="S3_ACCESS_KEY", min_length=32)
    s3_secret_key: SecretStr = Field(alias="S3_SECRET_KEY", min_length=32)
    api_token: SecretStr = Field(alias="POC_API_TOKEN", min_length=32)
    internal_token: SecretStr = Field(alias="INTERNAL_TOKEN", min_length=32)


def validate_runtime():
    try:
        settings = RuntimeSettings()
    except ValidationError:
        raise RuntimeError("CONFIGURATION_INVALID") from None
    if settings.runtime_profile == "production":
        raise RuntimeError("PRODUCTION_PROFILE_NOT_APPROVED")
    return settings
