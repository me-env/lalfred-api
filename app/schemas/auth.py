from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class GoogleAuthURL(BaseModel):
    url: str


class GoogleTokenResponse(BaseModel):
    access_token: str
    expires_in: int | None = None
    token_type: str | None = None
    scope: str | None = None
    refresh_token: str | None = None
    id_token: str | None = None


class GoogleUserInfo(BaseModel):
    sub: str
    email: str
    email_verified: bool | None = None
    name: str | None = None
    given_name: str | None = None
    family_name: str | None = None
    picture: str | None = None
    locale: str | None = None
