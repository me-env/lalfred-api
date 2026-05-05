from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import User
from app.repositories import subscription_repository
from app.schemas import UserRead

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def read_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    is_subscribed = await subscription_repository.has_active_subscription(
        db, user_id=user.id, as_of=datetime.now(UTC)
    )
    return UserRead(
        id=user.id,
        email=user.email,
        name=user.name,
        picture=user.picture,
        credits=user.credits,
        is_subscribed=is_subscribed,
        created_at=user.created_at,
    )
