import uuid
from datetime import datetime
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, EmailStr


class UserRead(BaseModel):
    id: uuid.UUID
    email: EmailStr
    name: str | None
    picture: str | None
    credits: int
    is_subscribed: bool
    created_at: datetime

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)
