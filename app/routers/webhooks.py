from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import webhook_service

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/lemonsqueezy", status_code=status.HTTP_200_OK)
async def lemonsqueezy_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    signature = request.headers.get("x-signature", "")
    data = await request.json()
    result = await webhook_service.handle_lemonsqueezy(db, payload, signature, data)
    await db.commit()
    return result
