import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import UsageStats
from app.services import stats_service

router = APIRouter(prefix="/stats", tags=["stats"])
logger = logging.getLogger(__name__)


@router.get("/usage", response_model=UsageStats)
async def get_usage_stats(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    window_days: Annotated[int, Query(ge=1, le=365)] = stats_service.DEFAULT_WINDOW_DAYS,
):
    logger.info("GET /stats/usage user_id=%s window_days=%s", user.id, window_days)
    return await stats_service.compute_usage_stats(db, user, window_days=window_days)
