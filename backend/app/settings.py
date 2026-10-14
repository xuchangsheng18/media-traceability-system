"""Validate private runtime configuration without displaying secret field values."""

from pydantic import AmqpDsn, AnyHttpUrl, Field, PostgresDsn, SecretStr, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class RuntimeSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")
    database_url: PostgresDsn = Field(alias="DATABASE_URL")
    broker_url: AmqpDsn = Field(alias="BROKER_URL")
    s3_endpoint: AnyHttpUrl = Field(alias="S3_ENDPOINT")
    inference_url: AnyHttpUrl = Field(alias="INFERENCE_URL")
    s3_access_key: SecretStr = Field(alias="S3_ACCESS_KEY", min_length=32)
    s3_secret_key: SecretStr = Field(alias="S3_SECRET_KEY", min_length=32)
    api_token: SecretStr = Field(alias="POC_API_TOKEN", min_length=32)
    internal_token: SecretStr = Field(alias="INTERNAL_TOKEN", min_length=32)


def validate_runtime():
    try:
        return RuntimeSettings()
    except ValidationError:
        raise RuntimeError("CONFIGURATION_INVALID") from None
