"""Business logic for payment claims.

A claim is created when a payment webhook arrives (no auto-attribution).
The buyer receives a key by email and redeems it inside the app to
apply the benefit (credits or subscription) to whichever account is
currently signed in.
"""
import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (PaymentClaim, PaymentClaimType, TransactionType, User)
from app.repositories import (credit_repository, payment_claim_repository,
                              subscription_repository)
from app.services import email_service
from app.services.payment_claim_keys import (generate_claim_key,
                                              normalize_claim_key)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ClaimRedemptionResult:
    type: PaymentClaimType
    credits_added: int | None = None
    subscription_starts_at: datetime | None = None
    subscription_ends_at: datetime | None = None


async def create_credit_claim(
    db: AsyncSession,
    *,
    buyer_email: str,
    lemon_order_id: str,
    credits_amount: int,
) -> PaymentClaim | None:
    """Create a credit claim and email the key to the buyer.

    Returns ``None`` if a claim with this ``lemon_order_id`` already exists.
    """
    if await payment_claim_repository.find_by_order_id(db, lemon_order_id) is not None:
        logger.info("payment_claim: already exists for order_id=%s", lemon_order_id)
        return None

    claim = await payment_claim_repository.create(
        db,
        claim_key=generate_claim_key(),
        type=PaymentClaimType.CREDITS,
        buyer_email=buyer_email,
        lemon_order_id=lemon_order_id,
        credits_amount=credits_amount,
    )
    logger.info(
        "payment_claim: created credit claim id=%s order_id=%s credits=%s",
        claim.id, lemon_order_id, credits_amount,
    )
    await email_service.send_payment_claim_email(claim)
    return claim


async def create_subscription_claim(
    db: AsyncSession,
    *,
    buyer_email: str,
    lemon_invoice_id: str,
    lemon_subscription_id: str,
    starts_at: datetime,
    ends_at: datetime,
) -> PaymentClaim | None:
    """Create a subscription claim and email the key to the buyer.

    Returns ``None`` if a claim with this ``lemon_invoice_id`` already exists.
    """
    if await payment_claim_repository.find_by_invoice_id(db, lemon_invoice_id) is not None:
        logger.info("payment_claim: already exists for invoice_id=%s", lemon_invoice_id)
        return None

    claim = await payment_claim_repository.create(
        db,
        claim_key=generate_claim_key(),
        type=PaymentClaimType.SUBSCRIPTION,
        buyer_email=buyer_email,
        lemon_invoice_id=lemon_invoice_id,
        lemon_subscription_id=lemon_subscription_id,
        starts_at=starts_at,
        ends_at=ends_at,
    )
    logger.info(
        "payment_claim: created subscription claim id=%s invoice_id=%s window=%s -> %s",
        claim.id, lemon_invoice_id, starts_at.isoformat(), ends_at.isoformat(),
    )
    await email_service.send_payment_claim_email(claim)
    return claim


async def redeem(db: AsyncSession, *, user: User, claim_key: str) -> ClaimRedemptionResult:
    """Apply a claim's benefit to ``user``'s account."""
    claim = await payment_claim_repository.find_by_key(db, normalize_claim_key(claim_key))
    if claim is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid claim key")
    if claim.claimed_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="This key has already been redeemed",
        )

    now = datetime.now(UTC)
    if claim.type == PaymentClaimType.CREDITS:
        result = await _apply_credit_claim(db, user, claim)
    else:
        result = await _apply_subscription_claim(db, user, claim)

    await payment_claim_repository.mark_claimed(db, claim=claim, user_id=user.id, claimed_at=now)
    logger.info(
        "payment_claim: redeemed id=%s by user_id=%s type=%s",
        claim.id, user.id, claim.type,
    )
    return result


async def _apply_credit_claim(
    db: AsyncSession, user: User, claim: PaymentClaim,
) -> ClaimRedemptionResult:
    if claim.credits_amount is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Credit claim is missing credit amount",
        )
    user.credits += claim.credits_amount
    credit_transaction = await credit_repository.create(
        db,
        user_id=user.id,
        amount=claim.credits_amount,
        type=TransactionType.PURCHASE,
        description=f"Redeemed {claim.credits_amount} credits",
        payment_claim_id=claim.id,
    )
    logger.info(
        "credit_transaction: created id=%s user_id=%s amount=%s",
        credit_transaction.id, user.id, claim.credits_amount,
    )
    return ClaimRedemptionResult(
        type=PaymentClaimType.CREDITS, credits_added=claim.credits_amount,
    )


async def _apply_subscription_claim(
    db: AsyncSession, user: User, claim: PaymentClaim,
) -> ClaimRedemptionResult:
    if claim.starts_at is None or claim.ends_at is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Subscription claim is missing required fields",
        )
    subscription_payment = await subscription_repository.create(
        db,
        user_id=user.id,
        payment_claim_id=claim.id,
        starts_at=claim.starts_at,
        ends_at=claim.ends_at,
    )
    logger.info(
        "subscription_payment: created id=%s user_id=%s starts_at=%s ends_at=%s",
        subscription_payment.id, user.id, claim.starts_at.isoformat(), claim.ends_at.isoformat(),
    )
    return ClaimRedemptionResult(
        type=PaymentClaimType.SUBSCRIPTION,
        subscription_starts_at=claim.starts_at,
        subscription_ends_at=claim.ends_at,
    )
