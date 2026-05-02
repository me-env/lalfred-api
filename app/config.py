from typing import ClassVar

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://lalfred:lalfred_dev@localhost:5432/lalfred"

    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/google/callback"

    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 10080  # 7 days

    lemonsqueezy_webhook_secret: str = ""
    lemonsqueezy_api_key: str = ""

    elevenlabs_api_key: str = ""

    otel_service_name: str = "lalfred-api-dev"
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_exporter_otlp_protocol: str = "grpc"
    otel_exporter_otlp_headers: str = ""

    initial_free_credits: int = 10

    app_deeplink_scheme: str = "lalfred://auth/callback"

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
