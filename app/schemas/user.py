import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserRead(BaseModel):
    id: uuid.UUID
    email: EmailStr
    name: str | None
    picture: str | None
    credits: int
    created_at: datetime

    model_config = {"from_attributes": True}
