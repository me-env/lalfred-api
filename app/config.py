from typing import ClassVar, Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(extra="ignore")

    env: Literal["dev", "test", "prod", "staging"]

    database_url: str

    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str

    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 10080  # 7 days

    lemonsqueezy_webhook_secret: str
    lemonsqueezy_api_key: str

    elevenlabs_api_key: str
    openai_api_key: str
    resend_api_key: str

    otel_service_name: str = "lalfred-api-dev"

    initial_free_credits: int = 500

    app_deeplink_scheme: str = "lalfred://auth/callback"

    email_from_address: str
    email_support_address: str


settings = Settings()  # type: ignore[call-arg]  # pyright: ignore[reportCallIssue]
