from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import User
from app.schemas.transcription import TranscriptionResult
from app.services import transcribe_service

router = APIRouter(prefix="/transcribe", tags=["transcribe"])


@router.post("", response_model=TranscriptionResult)
async def transcribe(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    content_type = request.headers.get("content-type", "")
    body = await request.body()
    result = await transcribe_service.transcribe(db, user, body, content_type)
    await db.commit()
    return result
