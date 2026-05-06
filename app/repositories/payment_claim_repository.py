import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import PaymentClaim, PaymentClaimType


async def find_by_key(db: AsyncSession, claim_key: str) -> PaymentClaim | None:
    result = await db.execute(select(PaymentClaim).where(PaymentClaim.claim_key == claim_key))
    return result.scalar_one_or_none()


async def find_by_order_id(db: AsyncSession, order_id: str) -> PaymentClaim | None:
    result = await db.execute(select(PaymentClaim).where(PaymentClaim.lemon_order_id == order_id))
    return result.scalar_one_or_none()


async def find_by_invoice_id(db: AsyncSession, invoice_id: str) -> PaymentClaim | None:
    result = await db.execute(
        select(PaymentClaim).where(PaymentClaim.lemon_invoice_id == invoice_id)
    )
    return result.scalar_one_or_none()


async def create(
    db: AsyncSession,
    *,
    claim_key: str,
    type: PaymentClaimType,
    buyer_email: str,
    lemon_order_id: str | None = None,
    lemon_invoice_id: str | None = None,
    lemon_subscription_id: str | None = None,
    credits_amount: int | None = None,
    starts_at: datetime | None = None,
    ends_at: datetime | None = None,
) -> PaymentClaim:
    claim = PaymentClaim(
        claim_key=claim_key,
        type=type,
        buyer_email=buyer_email,
        lemon_order_id=lemon_order_id,
        lemon_invoice_id=lemon_invoice_id,
        lemon_subscription_id=lemon_subscription_id,
        credits_amount=credits_amount,
        starts_at=starts_at,
        ends_at=ends_at,
    )
    db.add(claim)
    await db.flush()
    return claim


async def mark_claimed(
    db: AsyncSession, *, claim: PaymentClaim, user_id: uuid.UUID, claimed_at: datetime,
) -> None:
    claim.claimed_by_user_id = user_id
    claim.claimed_at = claimed_at
    await db.flush()
