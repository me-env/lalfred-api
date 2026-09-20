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

    otel_service_name: str = "lalfred-api-dev"

    app_deeplink_scheme: str = "lalfred://auth/callback"

    release_bucket_url: str = "https://lalfred-prod-public.s3.fr-par.scw.cloud"


settings = Settings()  # type: ignore[call-arg]  # pyright: ignore[reportCallIssue]
