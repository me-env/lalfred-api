from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.models import User
from app.schemas import CreditBalance, CreditTransactionRead, SignupBonus
from app.services import credit_service

router = APIRouter(prefix="/credits", tags=["credits"])


@router.get("/signup-bonus", response_model=SignupBonus)
async def get_signup_bonus():
    """Public endpoint: amount of free credits granted on first sign-up."""
    return SignupBonus(credits=settings.initial_free_credits)


@router.get("/balance", response_model=CreditBalance)
async def get_balance(user: User = Depends(get_current_user)):
    return CreditBalance(credits=user.credits)


@router.get("/transactions", response_model=list[CreditTransactionRead])
async def list_transactions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    return await credit_service.list_transactions(db, user.id, limit=limit, offset=offset)
