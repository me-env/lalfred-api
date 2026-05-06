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


def _order_payload(
    *,
    order_id: str,
    email: str,
    variant_id: str,
    subtotal_usd: int | None = None,
    subtotal: int | None = None,
    currency: str | None = None,
    **extra_attrs: object,
) -> bytes:
    attributes = {
        "user_email": email,
        "first_order_item": {"variant_id": variant_id},
        **extra_attrs,
    }
    if subtotal_usd is not None:
        attributes["subtotal_usd"] = subtotal_usd
    if subtotal is not None:
        attributes["subtotal"] = subtotal
    if currency is not None:
        attributes["currency"] = currency

    return json.dumps({
        "meta": {"event_name": "order_created"},
        "data": {
            "id": order_id,
            "type": "orders",
            "attributes": attributes,
        },
    }).encode()


# ── Signature ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_webhook_invalid_signature(client):
    payload = json.dumps({
        "meta": {"event_name": "order_created"},
        "data": {
            "id": "order-invalid-signature",
            "type": "orders",
            "attributes": {
                "user_email": "nobody@test.com",
                "first_order_item": {"variant_id": "1604360"},
                "subtotal_usd": 1000,
            },
        },
    }).encode()
    resp = await client.post(
        "/webhooks/lemonsqueezy/order-created",
        content=payload,
        headers={"x-signature": "invalid", "content-type": "application/json"},
    )
    assert resp.status_code == 403


# ── order_created ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_order_created_grants_credits(client, test_user):
    payload = _order_payload(
        order_id="order-001",
        email=test_user.email,
        variant_id="1604360",
        subtotal_usd=1760,
    )
    resp = await client.post(
        "/webhooks/lemonsqueezy/order-created",
        content=payload,
        headers={"x-signature": sign_payload(payload), "content-type": "application/json"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["credits_added"] == 88000


@pytest.mark.asyncio
async def test_order_created_grants_credits_from_eur_subtotal(client, test_user):
    payload = _order_payload(
        order_id="order-001-eur",
        email=test_user.email,
        variant_id="1604360",
        subtotal=465,
        currency="EUR",
    )
    resp = await client.post(
        "/webhooks/lemonsqueezy/order-created",
        content=payload,
        headers={"x-signature": sign_payload(payload), "content-type": "application/json"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["credits_added"] == 25100


@pytest.mark.asyncio
async def test_order_created_duplicate_is_idempotent(client, test_user):
    payload = _order_payload(
        order_id="order-dup",
        email=test_user.email,
        variant_id="1604360",
        subtotal_usd=1000,
    )
    headers = {"x-signature": sign_payload(payload), "content-type": "application/json"}

    await client.post("/webhooks/lemonsqueezy/order-created", content=payload, headers=headers)
    resp = await client.post("/webhooks/lemonsqueezy/order-created", content=payload, headers=headers)
    assert resp.json()["status"] == "already_processed"


@pytest.mark.asyncio
async def test_order_created_unknown_variant(client, test_user):
    payload = _order_payload(
        order_id="order-unknown",
        email=test_user.email,
        variant_id="9999999",
        subtotal_usd=500,
    )
    resp = await client.post(
        "/webhooks/lemonsqueezy/order-created",
        content=payload,
        headers={"x-signature": sign_payload(payload), "content-type": "application/json"},
    )
    assert resp.json()["status"] == "unknown_product"


@pytest.mark.asyncio
async def test_order_created_byok_variant_is_ignored(client, test_user):
    payload = _order_payload(
        order_id="order-byok",
        email=test_user.email,
        variant_id="1604374",
        subtotal_usd=350,
    )
    resp = await client.post(
        "/webhooks/lemonsqueezy/order-created",
        content=payload,
        headers={"x-signature": sign_payload(payload), "content-type": "application/json"},
    )
    assert resp.json()["status"] == "ignored"


@pytest.mark.asyncio
async def test_order_created_with_real_lemonsqueezy_payload_shape(client, test_user):
    payload = json.dumps({
        "data": {
            "id": "8241268",
            "type": "orders",
            "links": {
                "self": "https://api.lemonsqueezy.com/v1/orders/8241268",
            },
            "attributes": {
                "tax": 0,
                "urls": {
                    "receipt": (
                        "https://app.lemonsqueezy.com/my-orders/"
                        "e0a87257-7481-4163-984b-1e85f6851d7d"
                        "?expires=1777846860&signature="
                        "ef406bbd4a7b5b2d7e3922d249c0ddd94cff64fdc1858c6c885fd21d5186c997"
                    ),
                },
                "total": 1000,
                "status": "paid",
                "tax_usd": 0,
                "currency": "EUR",
                "refunded": False,
                "store_id": 362508,
                "subtotal": 1000,
                "tax_name": "VAT",
                "tax_rate": 0,
                "setup_fee": 0,
                "test_mode": True,
                "total_usd": 1173,
                "user_name": "Cyprien Ricque",
                "created_at": "2026-05-03T16:20:59.000000Z",
                "identifier": "e0a87257-7481-4163-984b-1e85f6851d7d",
                "updated_at": "2026-05-03T16:21:00.000000Z",
                "user_email": test_user.email,
                "customer_id": 8640795,
                "refunded_at": None,
                "order_number": 3625083,
                "subtotal_usd": 1173,
                "currency_rate": "1.17319943",
                "setup_fee_usd": 0,
                "tax_formatted": "€0.00",
                "tax_inclusive": False,
                "discount_total": 0,
                "refunded_amount": 0,
                "total_formatted": "EUR10.00",
                "first_order_item": {
                    "id": 8172186,
                    "price": 1000,
                    "order_id": 8241268,
                    "price_id": 2678979,
                    "quantity": 1,
                    "test_mode": True,
                    "created_at": "2026-05-03T16:21:00.000000Z",
                    "product_id": 1022717,
                    "updated_at": "2026-05-03T16:21:00.000000Z",
                    "variant_id": 1604360,
                    "product_name": "L'alfred Credits",
                    "variant_name": "Default",
                },
                "status_formatted": "Paid",
                "discount_total_usd": 0,
                "subtotal_formatted": "EUR10.00",
                "refunded_amount_usd": 0,
                "setup_fee_formatted": "EUR0.00",
                "discount_total_formatted": "EUR0.00",
                "refunded_amount_formatted": "EUR0.00",
            },
            "relationships": {
                "store": {
                    "links": {
                        "self": (
                            "https://api.lemonsqueezy.com/v1/orders/8241268/relationships/store"
                        ),
                        "related": "https://api.lemonsqueezy.com/v1/orders/8241268/store",
                    },
                },
                "customer": {
                    "links": {
                        "self": (
                            "https://api.lemonsqueezy.com/v1/orders/8241268/relationships/customer"
                        ),
                        "related": "https://api.lemonsqueezy.com/v1/orders/8241268/customer",
                    },
                },
                "order-items": {
                    "links": {
                        "self": (
                            "https://api.lemonsqueezy.com/v1/orders/8241268/relationships/order-items"
                        ),
                        "related": "https://api.lemonsqueezy.com/v1/orders/8241268/order-items",
                    },
                },
                "license-keys": {
                    "links": {
                        "self": (
                            "https://api.lemonsqueezy.com/v1/orders/8241268/relationships/license-keys"
                        ),
                        "related": "https://api.lemonsqueezy.com/v1/orders/8241268/license-keys",
                    },
                },
                "subscriptions": {
                    "links": {
                        "self": (
                            "https://api.lemonsqueezy.com/v1/orders/8241268/relationships/subscriptions"
                        ),
                        "related": "https://api.lemonsqueezy.com/v1/orders/8241268/subscriptions",
                    },
                },
                "discount-redemptions": {
                    "links": {
                        "self": (
                            "https://api.lemonsqueezy.com/v1/orders/8241268/relationships/"
                            "discount-redemptions"
                        ),
                        "related": (
                            "https://api.lemonsqueezy.com/v1/orders/8241268/discount-redemptions"
                        ),
                    },
                },
            },
        },
        "meta": {
            "test_mode": True,
            "event_name": "order_created",
            "webhook_id": "a1b13850-c312-484b-b4bc-5d82b09cdcde",
        },
    }).encode()
    resp = await client.post(
        "/webhooks/lemonsqueezy/order-created",
        content=payload,
        headers={"x-signature": sign_payload(payload), "content-type": "application/json"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["credits_added"] == 54000


# ── Subscription events ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_subscription_payment_success_with_real_payload(client):
    payload = json.dumps({
        "data": {
            "id": "6958066",
            "type": "subscription-invoices",
            "links": {
                "self": "https://api.lemonsqueezy.com/v1/subscription-invoices/6958066",
            },
            "attributes": {
                "tax": 0,
                "urls": {
                    "invoice_url": (
                        "https://app.lemonsqueezy.com/my-orders/"
                        "c98d8c12-fe3e-4ba4-8c60-bfd44eee071f/subscription-invoice/6958066"
                        "?expires=1777840844&signature="
                        "1312f9faa9fe0d067d53341621b02c2461f401f71197d893ac3c96c6451e7f59"
                    ),
                },
                "total": 4000,
                "status": "paid",
                "tax_usd": 0,
                "currency": "EUR",
                "refunded": False,
                "store_id": 362508,
                "subtotal": 4000,
                "test_mode": True,
                "total_usd": 4693,
                "user_name": "Cyprien Ricque",
                "card_brand": "visa",
                "created_at": "2026-05-03T14:40:36.000000Z",
                "updated_at": "2026-05-03T14:40:43.000000Z",
                "user_email": "cyprien.25@gmail.com",
                "customer_id": 8640171,
                "refunded_at": None,
                "subtotal_usd": 4693,
                "currency_rate": "1.17319943",
                "tax_formatted": "EUR0.00",
                "tax_inclusive": False,
                "billing_reason": "initial",
                "card_last_four": "4242",
                "discount_total": 0,
                "refunded_amount": 0,
                "subscription_id": 2119572,
                "total_formatted": "€40.00",
                "status_formatted": "Paid",
                "discount_total_usd": 0,
                "subtotal_formatted": "€40.00",
                "refunded_amount_usd": 0,
                "discount_total_formatted": "€0.00",
                "refunded_amount_formatted": "€0.00",
            },
            "relationships": {
                "store": {
                    "links": {
                        "self": (
                            "https://api.lemonsqueezy.com/v1/subscription-invoices/6958066/"
                            "relationships/store"
                        ),
                        "related": (
                            "https://api.lemonsqueezy.com/v1/subscription-invoices/6958066/store"
                        ),
                    },
                },
                "customer": {
                    "links": {
                        "self": (
                            "https://api.lemonsqueezy.com/v1/subscription-invoices/6958066/"
                            "relationships/customer"
                        ),
                        "related": (
                            "https://api.lemonsqueezy.com/v1/subscription-invoices/6958066/customer"
                        ),
                    },
                },
                "subscription": {
                    "links": {
                        "self": (
                            "https://api.lemonsqueezy.com/v1/subscription-invoices/6958066/"
                            "relationships/subscription"
                        ),
                        "related": (
                            "https://api.lemonsqueezy.com/v1/subscription-invoices/6958066/"
                            "subscription"
                        ),
                    },
                },
            },
        },
        "meta": {
            "test_mode": True,
            "event_name": "subscription_payment_success",
            "webhook_id": "a1b11473-a2c4-48d0-8495-08f93c44d221",
        },
    }).encode()
    resp = await client.post(
        "/webhooks/lemonsqueezy/subscription-payment-success",
        content=payload,
        headers={"x-signature": sign_payload(payload), "content-type": "application/json"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
