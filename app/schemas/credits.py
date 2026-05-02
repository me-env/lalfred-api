import uuid
from datetime import datetime

from pydantic import BaseModel


class CreditBalance(BaseModel):
    credits: int


class CreditTransactionRead(BaseModel):
    id: uuid.UUID
    amount: int
    type: str
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
