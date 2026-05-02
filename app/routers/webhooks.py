import hashlib
import hmac
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import CreditTransaction, TransactionType, User

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)

CREDITS_PER_PRODUCT: dict[str, int] = {
    "starter": 100,
    "pro": 500,
    "unlimited": 2000,
}


def verify_lemon_signature(payload: bytes, signature: str) -> bool:
    digest = hmac.new(
        settings.lemonsqueezy_webhook_secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(digest, signature)


@router.post("/lemonsqueezy", status_code=status.HTTP_200_OK)
async def lemonsqueezy_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle Lemon Squeezy webhook events for order completion."""
    payload = await request.body()
    signature = request.headers.get("x-signature", "")

    if not verify_lemon_signature(payload, signature):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid signature")

    data = await request.json()
    event_name = data.get("meta", {}).get("event_name")

    if event_name != "order_created":
        return {"status": "ignored"}

    attributes = data.get("data", {}).get("attributes", {})
    order_id = str(data.get("data", {}).get("id", ""))
    user_email = attributes.get("user_email", "")
    variant_name = attributes.get("first_order_item", {}).get("variant_name", "").lower()
    product_name = attributes.get("first_order_item", {}).get("product_name", "").lower()

    credit_amount = CREDITS_PER_PRODUCT.get(variant_name) or CREDITS_PER_PRODUCT.get(product_name)
    if credit_amount is None:
        logger.warning("Unknown product/variant: %s / %s", product_name, variant_name)
        return {"status": "unknown_product"}

    result = await db.execute(select(User).where(User.email == user_email))
    user = result.scalar_one_or_none()
    if user is None:
        logger.warning("Webhook for unknown user email: %s", user_email)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    existing = await db.execute(
        select(CreditTransaction).where(CreditTransaction.lemon_order_id == order_id)
    )
    if existing.scalar_one_or_none() is not None:
        return {"status": "already_processed"}

    transaction = CreditTransaction(
        user_id=user.id,
        amount=credit_amount,
        type=TransactionType.PURCHASE,
        description=f"Purchased {variant_name or product_name} ({credit_amount} credits)",
        lemon_order_id=order_id,
    )
    user.credits += credit_amount
    db.add(transaction)
    await db.commit()

    logger.info("Added %d credits to user %s (order %s)", credit_amount, user.email, order_id)
    return {"status": "ok", "credits_added": credit_amount}
