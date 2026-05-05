from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas.webhooks.common import LemonSqueezyRelationshipLinks


class LemonSqueezySubscriptionPaymentSuccessMeta(BaseModel):
    event_name: Literal["subscription_payment_success"]
    test_mode: bool | None = None
    webhook_id: str | None = None


class LemonSqueezySubscriptionPaymentSuccessUrls(BaseModel):
    invoice_url: str | None = None


class LemonSqueezySubscriptionPaymentSuccessAttributes(BaseModel):
    tax: int | None = None
    urls: LemonSqueezySubscriptionPaymentSuccessUrls | None = None
    total: int | None = None
    status: str | None = None
    tax_usd: int | None = None
    currency: str | None = None
    refunded: bool = False
    store_id: int | None = None
    subtotal: int | None = None
    test_mode: bool | None = None
    total_usd: int | None = None
    user_name: str | None = None
    card_brand: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    user_email: str
    customer_id: int | None = None
    refunded_at: datetime | None = None
    subtotal_usd: int | None = None
    currency_rate: str | None = None
    tax_formatted: str | None = None
    tax_inclusive: bool | None = None
    billing_reason: str | None = None
    card_last_four: str | None = None
    discount_total: int | None = None
    refunded_amount: int | None = None
    subscription_id: int
    total_formatted: str | None = None
    status_formatted: str | None = None
    discount_total_usd: int | None = None
    subtotal_formatted: str | None = None
    refunded_amount_usd: int | None = None
    discount_total_formatted: str | None = None
    refunded_amount_formatted: str | None = None
    ends_at: datetime | None = None
    variant_id: int | None = None


class LemonSqueezySubscriptionPaymentSuccessRelationships(BaseModel):
    store: LemonSqueezyRelationshipLinks | None = None
    customer: LemonSqueezyRelationshipLinks | None = None
    subscription: LemonSqueezyRelationshipLinks | None = None


class LemonSqueezySubscriptionPaymentSuccessData(BaseModel):
    id: str
    type: Literal["subscription-invoices"]
    links: dict[str, str] | None = None
    attributes: LemonSqueezySubscriptionPaymentSuccessAttributes
    relationships: LemonSqueezySubscriptionPaymentSuccessRelationships | None = None


class LemonSqueezySubscriptionPaymentSuccessWebhook(BaseModel):
    meta: LemonSqueezySubscriptionPaymentSuccessMeta
    data: LemonSqueezySubscriptionPaymentSuccessData
