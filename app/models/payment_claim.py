import uuid
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, final

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class PaymentClaimType(StrEnum):
    CREDITS = "credits"
    SUBSCRIPTION = "subscription"


@final
class PaymentClaim(Base):
    __tablename__ = "payment_claims"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    claim_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    type: Mapped[PaymentClaimType] = mapped_column(String(20), nullable=False)

    buyer_email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)

    lemon_order_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    lemon_invoice_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    lemon_subscription_id: Mapped[str | None] = mapped_column(String(255), index=True)

    credits_amount: Mapped[int | None] = mapped_column(Integer)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    claimed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    claimed_by: Mapped["User | None"] = relationship(back_populates="claimed_payments")
