import logging

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import TransactionType
from app.pricing import resolve_product
from app.providers import lemonsqueezy_provider
from app.repositories import credit_repository, user_repository
from app.schemas.webhook import (LemonSqueezyWebhook,
                                 LemonSqueezyWebhookResponse)

logger = logging.getLogger(__name__)


async def handle_lemonsqueezy(
    db: AsyncSession, payload: bytes, signature: str, data: LemonSqueezyWebhook
) -> LemonSqueezyWebhookResponse:
    if not lemonsqueezy_provider.verify_signature(payload, signature):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid signature")

    event_name = data.meta.event_name
    if event_name != "order_created":
        return LemonSqueezyWebhookResponse(status="ignored")

    attributes = data.data.attributes
    first_item = attributes.first_order_item

    order_id = str(data.data.id)
    user_email = attributes.user_email or ""
    variant_id = str(first_item.variant_id or "") if first_item else ""
    variant_name = (first_item.variant_name or "").lower() if first_item else ""
    product_name = (first_item.product_name or "").lower() if first_item else ""

    product = resolve_product(variant_id, variant_name, product_name)
    if product is None:
        logger.warning("Unknown product/variant: %s / %s (variant_id=%s)", product_name, variant_name, variant_id)
        return LemonSqueezyWebhookResponse(status="unknown_product")

    user = await user_repository.find_by_email(db, user_email)
    if user is None:
        logger.warning("Webhook for unknown user email: %s", user_email)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    existing = await credit_repository.find_by_order_id(db, order_id)
    if existing is not None:
        return LemonSqueezyWebhookResponse(status="already_processed")

    user.credits += product.credits
    credit = await credit_repository.create(
        db,
        user_id=user.id,
        amount=product.credits,
        type=TransactionType.PURCHASE,
        description=f"Purchased {product.name} ({product.credits} credits)",
        lemon_order_id=order_id,
    )
    logger.info("Added %d credits to user %s (order %s)", product.credits, user.email, order_id)
    return LemonSqueezyWebhookResponse(status="ok", credits_added=product.credits, id=credit.id)
