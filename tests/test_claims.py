import hashlib
import hmac
import json

import pytest
from sqlalchemy import select

from app.config import settings
from app.models import (CreditTransaction, PaymentClaim, PaymentClaimType,
                        SubscriptionPayment)
from app.services import payment_claim_service
from app.services.payment_claim_keys import (
    format_claim_key_for_display,
    generate_claim_key,
    normalize_claim_key
)


def sign_payload(payload: bytes) -> str:
    return hmac.new(
        settings.lemonsqueezy_webhook_secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()


# ── Webhooks now create claims and send emails (no auto-attribution) ────

@pytest.mark.asyncio
async def test_credit_webhook_creates_claim_and_emails_buyer(
    client, db_session, stub_resend_provider,
):
    payload = json.dumps({
        "meta": {"event_name": "order_created"},
        "data": {
            "id": "order-claim-001",
            "type": "orders",
            "attributes": {
                "user_email": "buyer@example.com",
                "first_order_item": {"variant_id": "1604360"},
                "subtotal_usd": 1000,
            },
        },
    }).encode()

    resp = await client.post(
        "/webhooks/lemonsqueezy/order-created",
        content=payload,
        headers={"x-signature": sign_payload(payload), "content-type": "application/json"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

    claim = (await db_session.execute(
        select(PaymentClaim).where(PaymentClaim.lemon_order_id == "order-claim-001")
    )).scalar_one()
    assert claim.type == PaymentClaimType.CREDITS
    assert claim.buyer_email == "buyer@example.com"
    assert claim.credits_amount == 50000
    assert claim.claimed_at is None
    assert claim.claimed_by_user_id is None
    assert claim.claim_key

    assert len(stub_resend_provider) == 1
    sent = stub_resend_provider[0]
    assert sent["to"] == "buyer@example.com"
    # Email body displays the dashed form; the deep link uses the canonical form.
    assert format_claim_key_for_display(claim.claim_key) in sent["html"]
    assert f"key={claim.claim_key}" in sent["html"]


@pytest.mark.asyncio
async def test_subscription_webhook_creates_claim_and_emails_buyer(
    client, db_session, stub_resend_provider,
):
    payload = json.dumps({
        "meta": {"event_name": "subscription_payment_success"},
        "data": {
            "id": "invoice-claim-001",
            "type": "subscription-invoices",
            "attributes": {
                "user_email": "newbuyer@example.com",
                "subscription_id": 9911,
                "variant_id": 1604374,
                "created_at": "2026-05-03T14:40:36.000000Z",
            },
        },
    }).encode()

    resp = await client.post(
        "/webhooks/lemonsqueezy/subscription-payment-success",
        content=payload,
        headers={"x-signature": sign_payload(payload), "content-type": "application/json"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

    claim = (await db_session.execute(
        select(PaymentClaim).where(PaymentClaim.lemon_invoice_id == "invoice-claim-001")
    )).scalar_one()
    assert claim.type == PaymentClaimType.SUBSCRIPTION
    assert claim.buyer_email == "newbuyer@example.com"
    assert claim.lemon_subscription_id == "9911"
    assert claim.starts_at is not None and claim.ends_at is not None
    assert claim.claimed_at is None

    assert len(stub_resend_provider) == 1
    assert stub_resend_provider[0]["to"] == "newbuyer@example.com"


# ── /claims/redeem ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_redeem_credit_claim_adds_credits_to_user(
    client, db_session, test_user, auth_token,
):
    claim = await payment_claim_service.create_credit_claim(
        db_session,
        buyer_email="someone@example.com",
        lemon_order_id="order-redeem-1",
        credits_amount=12345,
    )
    assert claim is not None
    await db_session.commit()

    resp = await client.post(
        "/claims/redeem",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"claim_key": claim.claim_key},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["type"] == "credits"
    assert body["credits_added"] == 12345

    await db_session.refresh(test_user)
    assert test_user.credits == 10 + 12345

    refreshed = (await db_session.execute(
        select(PaymentClaim).where(PaymentClaim.id == claim.id)
    )).scalar_one()
    assert refreshed.claimed_by_user_id == test_user.id
    assert refreshed.claimed_at is not None

    tx = (await db_session.execute(
        select(CreditTransaction).where(CreditTransaction.user_id == test_user.id)
    )).scalar_one()
    assert tx.amount == 12345
    assert tx.payment_claim_id == claim.id


@pytest.mark.asyncio
async def test_redeem_subscription_claim_creates_subscription_for_user(
    client, db_session, test_user, auth_token,
):
    from datetime import UTC, datetime, timedelta
    starts = datetime.now(UTC)
    ends = starts + timedelta(days=30)
    claim = await payment_claim_service.create_subscription_claim(
        db_session,
        buyer_email="someone@example.com",
        lemon_invoice_id="invoice-redeem-1",
        lemon_subscription_id="sub-redeem-1",
        starts_at=starts,
        ends_at=ends,
    )
    assert claim is not None
    await db_session.commit()

    resp = await client.post(
        "/claims/redeem",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"claim_key": claim.claim_key},
    )
    assert resp.status_code == 200
    assert resp.json()["type"] == "subscription"

    sub = (await db_session.execute(
        select(SubscriptionPayment).where(SubscriptionPayment.user_id == test_user.id)
    )).scalar_one()
    assert sub.payment_claim_id == claim.id


@pytest.mark.asyncio
async def test_redeem_invalid_key(client, test_user, auth_token):
    resp = await client.post(
        "/claims/redeem",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"claim_key": "BOGUS-KEY-XXXX-XXXX"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_redeem_accepts_dashed_or_undashed_key(
    client, db_session, test_user, auth_token,
):
    """Both the canonical form and the human-readable dashed form must work."""
    claim = await payment_claim_service.create_credit_claim(
        db_session,
        buyer_email="someone@example.com",
        lemon_order_id="order-redeem-formats",
        credits_amount=42,
    )
    assert claim is not None
    await db_session.commit()

    dashed = format_claim_key_for_display(claim.claim_key)
    assert "-" in dashed

    resp = await client.post(
        "/claims/redeem",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"claim_key": dashed.lower()},
    )
    assert resp.status_code == 200
    assert resp.json()["credits_added"] == 42


def test_normalize_claim_key_strips_dashes_whitespace_and_uppercases():
    assert normalize_claim_key("  abcd-efgh-jkmn-pqrs  ") == "ABCDEFGHJKMNPQRS"
    assert normalize_claim_key("ABCDEFGHJKMNPQRS") == "ABCDEFGHJKMNPQRS"
    assert normalize_claim_key("abcd efgh jkmn pqrs") == "ABCDEFGHJKMNPQRS"


def test_generate_claim_key_is_canonical():
    key = generate_claim_key()
    assert "-" not in key
    assert key.isupper()
    assert len(key) == 16


@pytest.mark.asyncio
async def test_redeem_already_claimed_key_returns_409(
    client, db_session, test_user, auth_token,
):
    claim = await payment_claim_service.create_credit_claim(
        db_session,
        buyer_email="someone@example.com",
        lemon_order_id="order-redeem-already",
        credits_amount=100,
    )
    assert claim is not None
    await db_session.commit()

    headers = {"Authorization": f"Bearer {auth_token}"}
    first = await client.post("/claims/redeem", headers=headers, json={"claim_key": claim.claim_key})
    assert first.status_code == 200

    second = await client.post("/claims/redeem", headers=headers, json={"claim_key": claim.claim_key})
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_redeem_requires_auth(client):
    resp = await client.post("/claims/redeem", json={"claim_key": "ABCD-EFGH-JKLM-NPQR"})
    assert resp.status_code in (401, 403)
