from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.models import User
from app.schemas import UserRead

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def read_current_user(user: User = Depends(get_current_user)):
    return user
