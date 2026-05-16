from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.schemas.stats import UsageStats
from app.services import credit_service, transcribe_service

DEFAULT_WINDOW_DAYS = 30


async def compute_usage_stats(
    db: AsyncSession,
    user: User,
    *,
    window_days: int = DEFAULT_WINDOW_DAYS,
) -> UsageStats:
    """Coordinator: each domain service runs its own SQL aggregation."""
    window_start = datetime.now(UTC) - timedelta(days=window_days - 1)

    credit_stats = await credit_service.compute_credits_usage_stats(
        db, user.id,
        current_balance=user.credits,
        window_start=window_start,
        window_days=window_days,
    )
    transcription_stats = await transcribe_service.compute_usage_stats(
        db, user.id, window_start
    )

    return UsageStats(
        window_days=window_days,
        mean_credits_per_day=credit_stats.mean_credits_per_day,
        median_credits_per_day=credit_stats.median_credits_per_day,
        days_remaining_estimate=credit_stats.days_remaining_estimate,
        words_per_minute=transcription_stats.words_per_minute,
        total_words=transcription_stats.total_words,
        total_audio_seconds=transcription_stats.total_audio_seconds,
    )
