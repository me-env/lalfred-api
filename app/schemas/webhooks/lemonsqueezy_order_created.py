from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.webhooks.common import LemonSqueezyRelationshipLinks


class LemonSqueezyOrderCreatedMeta(BaseModel):
    event_name: Literal["order_created"]
    test_mode: bool | None = None
    webhook_id: str | None = None


class LemonSqueezyOrderCreatedFirstOrderItem(BaseModel):
    id: int | None = None
    price: int | None = None
    order_id: int | None = None
    price_id: int | None = None
    quantity: int | None = None
    test_mode: bool | None = None
    created_at: datetime | None = None
    product_id: int | None = None
    updated_at: datetime | None = None
    variant_id: int | str
    product_name: str | None = None
    variant_name: str | None = None


class LemonSqueezyOrderCreatedUrls(BaseModel):
    receipt: str | None = None


class LemonSqueezyOrderCreatedAttributes(BaseModel):
    tax: int | None = None
    urls: LemonSqueezyOrderCreatedUrls | None = None
    total: int | None = None
    status: str | None = None
    tax_usd: int | None = None
    currency: str | None = None
    refunded: bool = False
    store_id: int | None = None
    subtotal: int | None = None
    tax_name: str | None = None
    tax_rate: int | float | None = None
    setup_fee: int | None = None
    test_mode: bool | None = None
    total_usd: int | None = None
    user_name: str | None = None
    created_at: datetime | None = None
    identifier: str | None = None
    updated_at: datetime | None = None
    user_email: str
    customer_id: int | None = None
    refunded_at: datetime | None = None
    order_number: int | None = None
    subtotal_usd: int | None = None
    currency_rate: str | None = None
    setup_fee_usd: int | None = None
    tax_formatted: str | None = None
    tax_inclusive: bool | None = None
    discount_total: int | None = None
    refunded_amount: int | None = None
    total_formatted: str | None = None
    first_order_item: LemonSqueezyOrderCreatedFirstOrderItem
    status_formatted: str | None = None
    discount_total_usd: int | None = None
    subtotal_formatted: str | None = None
    refunded_amount_usd: int | None = None
    setup_fee_formatted: str | None = None
    discount_total_formatted: str | None = None
    refunded_amount_formatted: str | None = None


class LemonSqueezyOrderCreatedRelationships(BaseModel):
    store: LemonSqueezyRelationshipLinks | None = None
    customer: LemonSqueezyRelationshipLinks | None = None
    order_items: LemonSqueezyRelationshipLinks | None = Field(default=None, alias="order-items")
    license_keys: LemonSqueezyRelationshipLinks | None = Field(default=None, alias="license-keys")
    subscriptions: LemonSqueezyRelationshipLinks | None = None
    discount_redemptions: LemonSqueezyRelationshipLinks | None = Field(
        default=None,
        alias="discount-redemptions",
    )


class LemonSqueezyOrderCreatedData(BaseModel):
    id: str | int
    type: Literal["orders"]
    links: dict[str, str] | None = None
    attributes: LemonSqueezyOrderCreatedAttributes
    relationships: LemonSqueezyOrderCreatedRelationships | None = None


class LemonSqueezyOrderCreatedWebhook(BaseModel):
    meta: LemonSqueezyOrderCreatedMeta
    data: LemonSqueezyOrderCreatedData
