import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CreditTransaction, TransactionType


async def list_by_user(
    db: AsyncSession, user_id: uuid.UUID, *, limit: int = 50, offset: int = 0
) -> list[CreditTransaction]:
    result = await db.execute(
        select(CreditTransaction)
        .where(CreditTransaction.user_id == user_id)
        .order_by(CreditTransaction.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def find_by_order_id(db: AsyncSession, order_id: str) -> CreditTransaction | None:
    result = await db.execute(
        select(CreditTransaction).where(CreditTransaction.lemon_order_id == order_id)
    )
    return result.scalar_one_or_none()


async def create(
    db: AsyncSession,
    user_id: uuid.UUID,
    amount: int,
    type: TransactionType,
    description: str | None = None,
    lemon_order_id: str | None = None,
    model: str | None = None,
    duration_seconds: float | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    character_count: int | None = None,
) -> CreditTransaction:
    transaction = CreditTransaction(
        user_id=user_id,
        amount=amount,
        type=type,
        description=description,
        lemon_order_id=lemon_order_id,
        model=model,
        duration_seconds=duration_seconds,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        character_count=character_count,
    )
    db.add(transaction)
    await db.flush()
    return transaction
