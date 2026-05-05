import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.webhooks import (
    LemonSqueezyOrderCreatedWebhook,
    LemonSqueezySubscriptionPaymentSuccessWebhook, LemonSqueezyWebhookResponse)
from app.services import webhook_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post(
    "/lemonsqueezy/order-created",
    status_code=status.HTTP_200_OK,
    response_model=LemonSqueezyWebhookResponse,
)
async def lemonsqueezy_order_created_webhook(
    request: Request,
    webhook: LemonSqueezyOrderCreatedWebhook,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LemonSqueezyWebhookResponse:
    payload = await request.body()
    signature = request.headers.get("x-signature", "")
    result = await webhook_service.handle_order_created_webhook(db, payload, signature, webhook)
    await db.commit()
    logger.info(
        "POST /webhooks/lemonsqueezy/order-created committed status=%s order_id=%s",
        result.status,
        webhook.data.id,
    )
    return result


@router.post(
    "/lemonsqueezy/subscription-payment-success",
    status_code=status.HTTP_200_OK,
    response_model=LemonSqueezyWebhookResponse,
)
async def lemonsqueezy_subscription_payment_success_webhook(
    request: Request,
    webhook: LemonSqueezySubscriptionPaymentSuccessWebhook,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LemonSqueezyWebhookResponse:
    payload = await request.body()
    signature = request.headers.get("x-signature", "")
    result = await webhook_service.handle_subscription_payment_success_webhook(
        db,
        payload,
        signature,
        webhook,
    )
    await db.commit()
    logger.info(
        "POST /webhooks/lemonsqueezy/subscription-payment-success committed status=%s invoice_id=%s",
        result.status,
        webhook.data.id,
    )
    return result
