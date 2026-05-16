import uuid
from datetime import date, datetime

from sqlalchemy import func, select
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


async def create(
    db: AsyncSession,
    user_id: uuid.UUID,
    amount: int,
    type: TransactionType,
    description: str | None = None,
    payment_claim_id: uuid.UUID | None = None,
    model: str | None = None,
    duration_seconds: float | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    character_count: int | None = None,
    word_count: int | None = None,
) -> CreditTransaction:
    transaction = CreditTransaction(
        user_id=user_id,
        amount=amount,
        type=type,
        description=description,
        payment_claim_id=payment_claim_id,
        model=model,
        duration_seconds=duration_seconds,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        character_count=character_count,
        word_count=word_count,
    )
    db.add(transaction)
    await db.flush()
    return transaction


def _to_date(value: object) -> date:
    # SQLite returns ISO strings from func.date(); Postgres returns a date object.
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


async def sum_usage_credits_per_day_since(
    db: AsyncSession, user_id: uuid.UUID, since: datetime
) -> dict[date, int]:
    """
    Aggregate credits spent per UTC day since `since`. Returns at most one row
    per day with any usage — bounded by the elapsed window, not by tx count.
    """
    day_expr = func.date(CreditTransaction.created_at)
    result = await db.execute(
        select(
            day_expr.label("day"),
            func.sum(-CreditTransaction.amount).label("credits"),
        )
        .where(
            CreditTransaction.user_id == user_id,
            CreditTransaction.type == TransactionType.USAGE,
            CreditTransaction.created_at >= since,
        )
        .group_by(day_expr)
    )
    return {_to_date(row.day): int(row.credits) for row in result.all()}


async def sum_transcription_metrics_since(
    db: AsyncSession, user_id: uuid.UUID, since: datetime
) -> tuple[int, float]:
    """
    SQL-side aggregation of word count and audio duration across USAGE rows.
    LLM rows naturally contribute zero (both columns null for them).
    """
    result = await db.execute(
        select(
            func.coalesce(func.sum(CreditTransaction.word_count), 0),
            func.coalesce(func.sum(CreditTransaction.duration_seconds), 0.0),
        ).where(
            CreditTransaction.user_id == user_id,
            CreditTransaction.type == TransactionType.USAGE,
            CreditTransaction.created_at >= since,
        )
    )
    total_words, total_duration_s = result.one()
    return int(total_words), float(total_duration_s)
