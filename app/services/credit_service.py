import statistics
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CreditTransaction
from app.repositories import credit_repository


@dataclass(frozen=True)
class CreditUsageStats:
    mean_credits_per_day: float
    median_credits_per_day: float
    # None when there's no measurable usage in the window
    # (so no meaningful projection can be made).
    days_remaining_estimate: float | None


async def list_transactions(
    db: AsyncSession, user_id: uuid.UUID, *, limit: int = 50, offset: int = 0
) -> list[CreditTransaction]:
    return await credit_repository.list_by_user(db, user_id, limit=limit, offset=offset)


async def compute_credits_usage_stats(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    current_balance: int,
    window_start: datetime,
    window_days: int,
) -> CreditUsageStats:
    """
    Mean/median credits-per-day over a rolling window, plus a "days remaining"
    projection. Days with no usage stay zero on purpose: the projection should
    reflect real cadence — a user who dictates every other day shouldn't see
    an everyday-use estimate.

    Aggregation happens in SQL (one GROUP BY day) so we only ship at most
    `window_days` rows to Python regardless of transaction volume.
    """
    by_day = await credit_repository.sum_usage_credits_per_day_since(
        db, user_id, window_start
    )
    window_start_day = window_start.date()
    daily_totals = [
        by_day.get(window_start_day + timedelta(days=i), 0)
        for i in range(window_days)
    ]

    mean = sum(daily_totals) / window_days
    median = float(statistics.median(daily_totals))
    days_remaining = max(current_balance, 0) / mean if mean > 0 else None

    return CreditUsageStats(
        mean_credits_per_day=mean,
        median_credits_per_day=median,
        days_remaining_estimate=days_remaining,
    )
