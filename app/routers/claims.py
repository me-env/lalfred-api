import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import User
from app.schemas.claims import ClaimRedeemRequest, ClaimRedeemResponse
from app.services import payment_claim_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/claims", tags=["claims"])


@router.post("/redeem", response_model=ClaimRedeemResponse)
async def redeem_claim(
    payload: ClaimRedeemRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ClaimRedeemResponse:
    result = await payment_claim_service.redeem(db, user=user, claim_key=payload.claim_key)
    await db.commit()
    logger.info("POST /claims/redeem committed user_id=%s type=%s", user.id, result.type)
    return ClaimRedeemResponse(
        type=result.type.value,  # pyright: ignore[reportArgumentType]
        credits_added=result.credits_added,
        subscription_starts_at=result.subscription_starts_at,
        subscription_ends_at=result.subscription_ends_at,
    )
