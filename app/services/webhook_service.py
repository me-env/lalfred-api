import logging

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import TransactionType
from app.providers import lemonsqueezy_provider
from app.repositories import credit_repository, user_repository

logger = logging.getLogger(__name__)

CREDITS_PER_PRODUCT: dict[str, int] = {
    "starter": 100,
    "pro": 500,
    "unlimited": 2000,
}


async def handle_lemonsqueezy(
    db: AsyncSession, payload: bytes, signature: str, data: dict
) -> dict:
    if not lemonsqueezy_provider.verify_signature(payload, signature):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid signature")

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

    user = await user_repository.find_by_email(db, user_email)
    if user is None:
        logger.warning("Webhook for unknown user email: %s", user_email)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    existing = await credit_repository.find_by_order_id(db, order_id)
    if existing is not None:
        return {"status": "already_processed"}

    user.credits += credit_amount
    await credit_repository.create(
        db,
        user_id=user.id,
        amount=credit_amount,
        type=TransactionType.PURCHASE,
        description=f"Purchased {variant_name or product_name} ({credit_amount} credits)",
        lemon_order_id=order_id,
    )
    logger.info("Added %d credits to user %s (order %s)", credit_amount, user.email, order_id)
    return {"status": "ok", "credits_added": credit_amount}
