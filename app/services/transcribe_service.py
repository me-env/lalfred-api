import logging
import uuid
from dataclasses import dataclass
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import TransactionType, User
from app.pricing import (MAX_NEGATIVE_BALANCE, PREFLIGHT_DURATION_THRESHOLD_S,
                         estimate_stt_credits, stt_credits)
from app.providers import elevenlabs_provider
from app.repositories import credit_repository
from app.schemas.transcription import TranscriptionResult, WordType

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TranscriptionUsageStats:
    total_words: int
    total_audio_seconds: float
    # None when no audio has been transcribed yet (no usable denominator).
    words_per_minute: float | None


async def compute_usage_stats(
    db: AsyncSession, user_id: uuid.UUID, since: datetime
) -> TranscriptionUsageStats:
    """
    SQL-side aggregation of word count and audio duration since `since`.
    A single row comes back regardless of transcription volume.
    """
    total_words, total_duration_s = (
        await credit_repository.sum_transcription_metrics_since(db, user_id, since)
    )
    wpm: float | None = None
    if total_duration_s > 0 and total_words > 0:
        wpm = total_words / (total_duration_s / 60.0)
    return TranscriptionUsageStats(
        total_words=total_words,
        total_audio_seconds=round(total_duration_s, 2),
        words_per_minute=wpm,
    )


def _audio_duration_from_result(result: TranscriptionResult) -> float:
    if result.audio_duration_secs is not None:
        return result.audio_duration_secs
    if result.words:
        return max((w.end for w in result.words if w.end is not None), default=0.0)
    return 0.0


def _word_count_from_result(result: TranscriptionResult) -> int:
    # Prefer the structured word list (excluding spacing/audio events).
    if result.words:
        return sum(1 for w in result.words if w.type == WordType.WORD)
    # Fallback for providers that only return raw text.
    return len(result.text.split()) if result.text else 0


async def transcribe(
    db: AsyncSession,
    user: User,
    audio: bytes,
    content_type: str,
    *,
    model_id: str = "scribe_v2",
    no_verbatim: bool = True,
    tag_audio_events: bool = False,
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
        audio, content_type,
        model_id=model_id,
        no_verbatim=no_verbatim,
        tag_audio_events=tag_audio_events,
        keyterms=keyterms,
    )

    duration_s = _audio_duration_from_result(result)
    word_count = _word_count_from_result(result)
    cost = stt_credits(duration_s, keyterms=has_keyterms)
    label = f"{model_id}+keyterms" if has_keyterms else model_id

    user.credits -= cost
    _ = await credit_repository.create(
        db,
        user_id=user.id,
        amount=-cost,
        type=TransactionType.USAGE,
        description=f"{label} — {duration_s:.1f}s",
        model=model_id,
        duration_seconds=round(duration_s, 2),
        word_count=word_count,
    )
    logger.info(
        "Charged %d credits to user %s (%.1fs STT, %d words)",
        cost, user.email, duration_s, word_count,
    )
    return result
