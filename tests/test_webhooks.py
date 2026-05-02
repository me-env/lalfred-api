import hashlib
import hmac
import json

import pytest

from app.config import settings


def sign_payload(payload: bytes) -> str:
    return hmac.new(
        settings.lemonsqueezy_webhook_secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()


@pytest.mark.asyncio
async def test_webhook_invalid_signature(client):
    payload = json.dumps({
        "meta": {"event_name": "order_created"},
        "data": {"id": "order-invalid-signature", "attributes": {}},
    }).encode()
    resp = await client.post(
        "/webhooks/lemonsqueezy",
        content=payload,
        headers={"x-signature": "invalid", "content-type": "application/json"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_webhook_order_created(client, test_user):
    payload = json.dumps({
        "meta": {"event_name": "order_created"},
        "data": {
            "id": "order-001",
            "attributes": {
                "user_email": test_user.email,
                "first_order_item": {
                    "variant_name": "starter",
                    "product_name": "Credits Pack",
                },
            },
        },
    }).encode()
    signature = sign_payload(payload)

    resp = await client.post(
        "/webhooks/lemonsqueezy",
        content=payload,
        headers={"x-signature": signature, "content-type": "application/json"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["credits_added"] == 2500


@pytest.mark.asyncio
async def test_webhook_duplicate_order(client, test_user):
    payload = json.dumps({
        "meta": {"event_name": "order_created"},
        "data": {
            "id": "order-dup",
            "attributes": {
                "user_email": test_user.email,
                "first_order_item": {
                    "variant_name": "starter",
                    "product_name": "Credits Pack",
                },
            },
        },
    }).encode()
    signature = sign_payload(payload)
    headers = {"x-signature": signature, "content-type": "application/json"}

    await client.post("/webhooks/lemonsqueezy", content=payload, headers=headers)
    resp = await client.post("/webhooks/lemonsqueezy", content=payload, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "already_processed"


@pytest.mark.asyncio
async def test_webhook_ignores_other_events(client):
    payload = json.dumps({
        "meta": {"event_name": "subscription_updated"},
        "data": {"id": "sub-1", "attributes": {}},
    }).encode()
    signature = sign_payload(payload)

    resp = await client.post(
        "/webhooks/lemonsqueezy",
        content=payload,
        headers={"x-signature": signature, "content-type": "application/json"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ignored"
