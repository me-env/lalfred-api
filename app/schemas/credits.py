from typing import ClassVar
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CreditBalance(BaseModel):
    credits: int


class CreditTransactionRead(BaseModel):
    id: uuid.UUID
    amount: int
    type: str
    description: str | None
    created_at: datetime

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)
