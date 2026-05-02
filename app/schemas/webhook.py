from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class LemonSqueezyMeta(BaseModel):
    event_name: str
    custom_data: dict[str, object] | None = None


class LemonSqueezyFirstOrderItem(BaseModel):
    variant_id: str | int | None = None
    variant_name: str | None = None
    product_name: str | None = None


class LemonSqueezyOrderAttributes(BaseModel):
    user_email: str | None = None
    first_order_item: LemonSqueezyFirstOrderItem | None = None


class LemonSqueezyData(BaseModel):
    id: str | int
    type: str | None = None
    attributes: LemonSqueezyOrderAttributes = Field(default_factory=LemonSqueezyOrderAttributes)


class LemonSqueezyWebhook(BaseModel):
    meta: LemonSqueezyMeta
    data: LemonSqueezyData


class LemonSqueezyWebhookResponse(BaseModel):
    status: Literal["ok", "ignored", "unknown_product", "already_processed"]
    credits_added: int | None = None
    id: UUID | None = None
