from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import User
from app.schemas.transcription import TranscriptionResult
from app.services import transcribe_service

router = APIRouter(prefix="/transcribe", tags=["transcribe"])


@router.post("", response_model=TranscriptionResult)
async def transcribe(
    file: UploadFile = File(...),
    keyterms: list[str] | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    audio = await file.read()
    content_type = file.content_type or "application/octet-stream"
    result = await transcribe_service.transcribe(
        db, user, audio, content_type, keyterms=keyterms,
    )
    await db.commit()
    return result
