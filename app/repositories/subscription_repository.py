import uuid
from datetime import datetime

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SubscriptionPayment


async def create(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    payment_claim_id: uuid.UUID,
    starts_at: datetime,
    ends_at: datetime,
) -> SubscriptionPayment:
    subscription_payment = SubscriptionPayment(
        user_id=user_id,
        payment_claim_id=payment_claim_id,
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
