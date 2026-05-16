import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.models import CreditTransaction, TransactionType


def _usage_tx(
    user_id: uuid.UUID,
    *,
    amount: int,
    created_at: datetime,
    duration_seconds: float | None = None,
    word_count: int | None = None,
    model: str | None = "scribe_v2",
) -> CreditTransaction:
    return CreditTransaction(
        id=uuid.uuid4(),
        user_id=user_id,
        amount=amount,
        type=TransactionType.USAGE,
        description="test",
        model=model,
        duration_seconds=duration_seconds,
        word_count=word_count,
        created_at=created_at,
    )


@pytest.mark.asyncio
async def test_stats_requires_auth(client):
    resp = await client.get("/stats/usage")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_stats_no_usage_returns_zeros(client, test_user, auth_token):
    resp = await client.get(
        "/stats/usage", headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["mean_credits_per_day"] == 0.0
    assert data["median_credits_per_day"] == 0.0
    assert data["days_remaining_estimate"] is None
    assert data["words_per_minute"] is None
    assert data["total_words"] == 0
    assert data["total_audio_seconds"] == 0.0


@pytest.mark.asyncio
async def test_stats_computes_mean_median_and_projection(
    client, db_session, test_user, auth_token
):
    test_user.credits = 1000
    now = datetime.now(UTC)
    # 4 usage txs on 3 distinct days inside the 30-day window
    db_session.add_all([
        _usage_tx(test_user.id, amount=-10, created_at=now - timedelta(days=1)),
        _usage_tx(test_user.id, amount=-30, created_at=now - timedelta(days=2)),
        _usage_tx(test_user.id, amount=-20, created_at=now - timedelta(days=2)),
        _usage_tx(test_user.id, amount=-60, created_at=now - timedelta(days=5)),
    ])
    await db_session.commit()

    resp = await client.get(
        "/stats/usage?window_days=30",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()

    # Daily totals over 30 days: [10, 50, 60] on 3 days, zeros elsewhere.
    expected_total = 10 + 50 + 60  # = 120
    expected_mean = expected_total / 30
    assert data["mean_credits_per_day"] == pytest.approx(expected_mean)
    # Median of 30 sorted values with 27 zeros is 0.
    assert data["median_credits_per_day"] == 0.0
    assert data["days_remaining_estimate"] == pytest.approx(1000 / expected_mean)


@pytest.mark.asyncio
async def test_stats_ignores_purchases_and_old_data(
    client, db_session, test_user, auth_token
):
    now = datetime.now(UTC)
    db_session.add_all([
        # Outside the window — should be excluded.
        _usage_tx(test_user.id, amount=-500, created_at=now - timedelta(days=60)),
        # A purchase inside the window — should be excluded (not USAGE).
        CreditTransaction(
            id=uuid.uuid4(),
            user_id=test_user.id,
            amount=1000,
            type=TransactionType.PURCHASE,
            description="topup",
            created_at=now - timedelta(days=3),
        ),
        # One real usage inside the window.
        _usage_tx(test_user.id, amount=-30, created_at=now - timedelta(days=1)),
    ])
    await db_session.commit()

    resp = await client.get(
        "/stats/usage", headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["mean_credits_per_day"] == pytest.approx(30 / 30)


@pytest.mark.asyncio
async def test_stats_words_per_minute(client, db_session, test_user, auth_token):
    now = datetime.now(UTC)
    # 60 words in 60 seconds → 60 WPM. Add another tx: 120 words in 60 seconds.
    # Aggregate: 180 words / 120 s = 1.5 wps = 90 WPM.
    db_session.add_all([
        _usage_tx(
            test_user.id,
            amount=-5,
            created_at=now - timedelta(days=1),
            duration_seconds=60.0,
            word_count=60,
        ),
        _usage_tx(
            test_user.id,
            amount=-5,
            created_at=now - timedelta(days=2),
            duration_seconds=60.0,
            word_count=120,
        ),
    ])
    await db_session.commit()

    resp = await client.get(
        "/stats/usage", headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_words"] == 180
    assert data["total_audio_seconds"] == pytest.approx(120.0)
    assert data["words_per_minute"] == pytest.approx(90.0)


@pytest.mark.asyncio
async def test_stats_isolated_per_user(client, db_session, test_user, auth_token):
    other = type(test_user)(
        id=uuid.uuid4(),
        email="other@example.com",
        name="Other",
        google_sub="other-sub",
        credits=100,
    )
    db_session.add(other)
    await db_session.flush()
    db_session.add(
        _usage_tx(other.id, amount=-999, created_at=datetime.now(UTC) - timedelta(days=1))
    )
    await db_session.commit()

    resp = await client.get(
        "/stats/usage", headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["mean_credits_per_day"] == 0.0
