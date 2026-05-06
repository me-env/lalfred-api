from datetime import UTC, datetime, timedelta

import pytest

from app.models import PaymentClaim, PaymentClaimType, SubscriptionPayment


@pytest.mark.asyncio
async def test_get_me(client, test_user, auth_token):
    resp = await client.get("/users/me", headers={"Authorization": f"Bearer {auth_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "test@example.com"
    assert data["credits"] == 10
    assert data["is_subscribed"] is False


@pytest.mark.asyncio
async def test_get_me_no_auth(client):
    resp = await client.get("/users/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_invalid_token(client):
    resp = await client.get("/users/me", headers={"Authorization": "Bearer invalid-token"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_returns_active_subscription_status(client, db_session, test_user, auth_token):
    now = datetime.now(UTC)
    claim = PaymentClaim(
        claim_key="TEST-USER-SUB-KEY1",
        type=PaymentClaimType.SUBSCRIPTION,
        buyer_email=test_user.email,
        lemon_invoice_id="invoice-6958066",
        lemon_subscription_id="2119572",
        starts_at=now - timedelta(days=1),
        ends_at=now + timedelta(days=29),
    )
    db_session.add(claim)
    await db_session.flush()
    db_session.add(
        SubscriptionPayment(
            user_id=test_user.id,
            payment_claim_id=claim.id,
            starts_at=now - timedelta(days=1),
            ends_at=now + timedelta(days=29),
        )
    )
    await db_session.commit()

    resp = await client.get("/users/me", headers={"Authorization": f"Bearer {auth_token}"})
    assert resp.status_code == 200
    assert resp.json()["is_subscribed"] is True
