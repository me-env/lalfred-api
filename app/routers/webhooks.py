from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.webhook import (LemonSqueezyWebhook,
                                 LemonSqueezyWebhookResponse)
from app.services import webhook_service

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post(
    "/lemonsqueezy",
    status_code=status.HTTP_200_OK,
    response_model=LemonSqueezyWebhookResponse,
)
async def lemonsqueezy_webhook(
    request: Request,
    webhook: LemonSqueezyWebhook,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LemonSqueezyWebhookResponse:
    payload = await request.body()
    signature = request.headers.get("x-signature", "")
    result = await webhook_service.handle_lemonsqueezy(db, payload, signature, webhook)
    await db.commit()
    return result
