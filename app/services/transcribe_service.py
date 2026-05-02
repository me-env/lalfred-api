from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import TransactionType, User
from app.providers import elevenlabs_provider
from app.repositories import credit_repository


async def transcribe(db: AsyncSession, user: User, body: bytes, content_type: str) -> dict:
    if user.credits <= 0:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Insufficient credits",
        )

    result = await elevenlabs_provider.transcribe(body, content_type)

    user.credits -= 1
    await credit_repository.create(
        db,
        user_id=user.id,
        amount=-1,
        type=TransactionType.USAGE,
        description="Scribe v2 transcription",
    )
    return result
