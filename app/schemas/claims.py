from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ClaimRedeemRequest(BaseModel):
    claim_key: str = Field(..., min_length=1, max_length=64)


class ClaimRedeemResponse(BaseModel):
    type: Literal["credits", "subscription"]
    credits_added: int | None = None
    subscription_starts_at: datetime | None = None
    subscription_ends_at: datetime | None = None
