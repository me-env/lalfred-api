import logging

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import TransactionType, User
from app.pricing import (MAX_NEGATIVE_BALANCE, PREFLIGHT_DURATION_THRESHOLD_S,
                         estimate_stt_credits, stt_credits)
from app.providers import elevenlabs_provider
from app.repositories import credit_repository
from app.schemas.transcription import TranscriptionResult

logger = logging.getLogger(__name__)


def _audio_duration_from_result(result: TranscriptionResult) -> float:
    if result.audio_duration_secs is not None:
        return result.audio_duration_secs
    if result.words:
        return max((w.end for w in result.words if w.end is not None), default=0.0)
    return 0.0


async def transcribe(
    db: AsyncSession,
    user: User,
    audio: bytes,
    content_type: str,
    *,
    keyterms: list[str] | None = None,
    duration_hint_seconds: float | None = None,
) -> TranscriptionResult:
    has_keyterms = bool(keyterms)

    if user.credits < 0:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Insufficient credits",
        )

    if duration_hint_seconds and duration_hint_seconds > PREFLIGHT_DURATION_THRESHOLD_S:
        estimated = estimate_stt_credits(duration_hint_seconds, keyterms=has_keyterms)
        if user.credits - estimated < MAX_NEGATIVE_BALANCE:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Insufficient credits for this recording length",
            )

    result = await elevenlabs_provider.transcribe(
        audio, content_type, keyterms=keyterms,
    )

    duration_s = _audio_duration_from_result(result)
    cost = stt_credits(duration_s, keyterms=has_keyterms)
    label = "Scribe v2+keyterms" if has_keyterms else "Scribe v2"

    user.credits -= cost
    _ = await credit_repository.create(
        db,
        user_id=user.id,
        amount=-cost,
        type=TransactionType.USAGE,
        description=f"{label} — {duration_s:.1f}s",
        model="scribe_v2",
        duration_seconds=round(duration_s, 2),
    )
    logger.info("Charged %d credits to user %s (%.1fs STT)", cost, user.email, duration_s)
    return result
