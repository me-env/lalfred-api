import logging
from urllib.parse import urlencode

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import create_access_token
from app.config import settings
from app.models import TransactionType, User
from app.providers import google_provider
from app.repositories import credit_repository, user_repository

logger = logging.getLogger(__name__)

SIGNUP_BONUS_DESCRIPTION = "Sign-up bonus"


def get_login_url() -> str:
    return google_provider.get_login_url()


async def handle_callback(db: AsyncSession, code: str) -> tuple[User, str]:
    """Exchange code, upsert user, return (user, deeplink_url)."""
    tokens = await google_provider.exchange_code(code)
    userinfo = await google_provider.get_userinfo(tokens.access_token)

    google_sub = userinfo.sub
    email = userinfo.email
    name = userinfo.name
    picture = userinfo.picture

    user = await user_repository.find_by_google_sub(db, google_sub)

    if user is None:
        user = await user_repository.create(
            db,
            email=email,
            name=name,
            picture=picture,
            google_sub=google_sub,
        )
        await _grant_signup_bonus(db, user)
    else:
        user.email = email
        user.name = name
        user.picture = picture

    access_token = create_access_token(user.id)
    deeplink = f"{settings.app_deeplink_scheme}?{urlencode({'token': access_token})}"
    return user, deeplink


async def _grant_signup_bonus(db: AsyncSession, user: User) -> None:
    """Credit the sign-up bonus to a fresh user and record it in the ledger."""
    bonus = settings.initial_free_credits
    if bonus <= 0:
        return
    user.credits += bonus
    transaction = await credit_repository.create(
        db,
        user_id=user.id,
        amount=bonus,
        type=TransactionType.BONUS,
        description=SIGNUP_BONUS_DESCRIPTION,
    )
    logger.info(
        "credit_transaction: created id=%s user_id=%s amount=%s type=bonus (sign-up)",
        transaction.id, user.id, bonus,
    )
