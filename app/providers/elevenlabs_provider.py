import logging

import httpx
from fastapi import HTTPException

from app.config import settings
from app.schemas.transcription import TranscriptionResult

logger = logging.getLogger(__name__)

ELEVENLABS_SCRIBE_URL = "https://api.elevenlabs.io/v1/speech-to-text"


async def transcribe(
    audio: bytes,
    content_type: str,
    *,
    keyterms: list[str] | None = None,
) -> TranscriptionResult:
    headers = {"xi-api-key": settings.elevenlabs_api_key}
    files: list[tuple[str, tuple[str | None, str | bytes, str | None]]] = [
        ("model_id", (None, "scribe_v2", None)),
        ("no_verbatim", (None, "true", None)),
        ("tag_audio_events", (None, "false", None)),
        ("file", ("audio", audio, content_type)),
    ]
    if keyterms:
        files.extend(("keyterms", (None, term, None)) for term in keyterms)

    async with httpx.AsyncClient(timeout=300.0) as client:
        resp = await client.post(
            ELEVENLABS_SCRIBE_URL, headers=headers, files=files,
        )

    if resp.status_code != 200:
        logger.error("ElevenLabs API error: %d %s", resp.status_code, resp.text)
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"ElevenLabs API error: {resp.text}",
        )
    return TranscriptionResult.model_validate(resp.json())
