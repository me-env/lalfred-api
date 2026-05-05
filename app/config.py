from typing import ClassVar, Literal

from pydantic import ValidationInfo, field_validator

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(extra="ignore")

    env: Literal["dev", "test", "prod"] = "dev"

    database_url: str = "postgresql+asyncpg://lalfred:lalfred_dev@localhost:5432/lalfred"

    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/google/callback"

    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 10080  # 7 days

    lemonsqueezy_webhook_secret: str
    lemonsqueezy_api_key: str

    elevenlabs_api_key: str
    openai_api_key: str

    otel_service_name: str = "lalfred-api-dev"
    otel_exporter_otlp_endpoint: str = ""
    otel_exporter_otlp_protocol: str = "grpc"
    otel_exporter_otlp_headers: str = ""

    initial_free_credits: int = 500

    app_deeplink_scheme: str = "lalfred://auth/callback"

    @field_validator(
        "lemonsqueezy_webhook_secret",
        "lemonsqueezy_api_key",
        "elevenlabs_api_key",
        "openai_api_key",
        mode="before",
    )
    @classmethod
    def validate_required_non_empty_secret(cls, value: object, info: ValidationInfo) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{info.field_name} must be set and non-empty")
        return value.strip()


settings = Settings()  # pyright: ignore[reportCallIssue]
