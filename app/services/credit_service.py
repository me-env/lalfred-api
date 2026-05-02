import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CreditTransaction
from app.repositories import credit_repository


async def list_transactions(
    db: AsyncSession, user_id: uuid.UUID, *, limit: int = 50, offset: int = 0
) -> list[CreditTransaction]:
    return await credit_repository.list_by_user(db, user_id, limit=limit, offset=offset)
