import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.models import CreditTransaction, TransactionType, User

router = APIRouter(prefix="/transcribe", tags=["transcribe"])
logger = logging.getLogger(__name__)

ELEVENLABS_SCRIBE_URL = "https://api.elevenlabs.io/v1/speech-to-text"


@router.post("")
async def transcribe(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Proxy to ElevenLabs Scribe v2.

    Forwards the multipart form data as-is to ElevenLabs, acting as a transparent proxy.
    The client should send the same parameters it would send directly to ElevenLabs.
    Consumes 1 credit per request.
    """
    if user.credits <= 0:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Insufficient credits",
        )

    content_type = request.headers.get("content-type", "")
    body = await request.body()

    headers = {
        "xi-api-key": settings.elevenlabs_api_key,
        "Content-Type": content_type,
    }

    async with httpx.AsyncClient(timeout=300.0) as client:
        resp = await client.post(
            ELEVENLABS_SCRIBE_URL,
            content=body,
            headers=headers,
        )

    if resp.status_code != 200:
        logger.error("ElevenLabs API error: %d %s", resp.status_code, resp.text)
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"ElevenLabs API error: {resp.text}",
        )

    user.credits -= 1
    transaction = CreditTransaction(
        user_id=user.id,
        amount=-1,
        type=TransactionType.USAGE,
        description="Scribe v2 transcription",
    )
    db.add(transaction)
    await db.commit()

    return resp.json()
