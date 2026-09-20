import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.models import User
from app.schemas import UserRead

router = APIRouter(prefix="/users", tags=["users"])
logger = logging.getLogger(__name__)


@router.get("/me", response_model=UserRead)
async def read_current_user(user: Annotated[User, Depends(get_current_user)]):
    logger.info("GET /users/me user_id=%s", user.id)
    return UserRead.model_validate(user)
