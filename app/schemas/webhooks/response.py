from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class LemonSqueezyWebhookResponse(BaseModel):
    status: Literal["ok", "ignored", "unknown_product", "already_processed", "refunded"]
    credits_added: int | None = None
    credits_deducted: int | None = None
    id: UUID | None = None
