import uuid
from datetime import datetime

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SubscriptionPayment


async def find_by_invoice_id(db: AsyncSession, invoice_id: str) -> SubscriptionPayment | None:
    result = await db.execute(
        select(SubscriptionPayment).where(SubscriptionPayment.lemon_invoice_id == invoice_id)
    )
    return result.scalar_one_or_none()


async def create(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    lemon_subscription_id: str,
    lemon_invoice_id: str,
    starts_at: datetime,
    ends_at: datetime,
) -> SubscriptionPayment:
    subscription_payment = SubscriptionPayment(
        user_id=user_id,
        lemon_subscription_id=lemon_subscription_id,
        lemon_invoice_id=lemon_invoice_id,
        starts_at=starts_at,
        ends_at=ends_at,
    )
    db.add(subscription_payment)
    await db.flush()
    return subscription_payment


async def has_active_subscription(
    db: AsyncSession, *, user_id: uuid.UUID, as_of: datetime,
) -> bool:
    result = await db.execute(
        select(
            exists().where(
                SubscriptionPayment.user_id == user_id,
                SubscriptionPayment.starts_at <= as_of,
                SubscriptionPayment.ends_at > as_of,
            )
        )
    )
    return bool(result.scalar())
