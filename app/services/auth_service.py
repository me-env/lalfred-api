from urllib.parse import urlencode

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import create_access_token
from app.config import settings
from app.models import User
from app.providers import google_provider
from app.repositories import user_repository


def get_login_url() -> str:
    return google_provider.get_login_url()


async def handle_callback(db: AsyncSession, code: str) -> tuple[User, str]:
    """Exchange code, upsert user, return (user, deeplink_url)."""
    tokens = await google_provider.exchange_code(code)
    userinfo = await google_provider.get_userinfo(tokens["access_token"])

    google_sub = userinfo["sub"]
    email = userinfo["email"]
    name = userinfo.get("name")
    picture = userinfo.get("picture")

    user = await user_repository.find_by_google_sub(db, google_sub)

    if user is None:
        user = await user_repository.create(
            db,
            email=email,
            name=name,
            picture=picture,
            google_sub=google_sub,
            credits=settings.initial_free_credits,
        )
    else:
        user.email = email
        user.name = name
        user.picture = picture

    access_token = create_access_token(user.id)
    deeplink = f"{settings.app_deeplink_scheme}?{urlencode({'token': access_token})}"
    return user, deeplink
