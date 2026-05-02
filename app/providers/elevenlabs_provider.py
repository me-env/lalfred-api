import logging

import httpx
from fastapi import HTTPException

from app.config import settings

logger = logging.getLogger(__name__)

ELEVENLABS_SCRIBE_URL = "https://api.elevenlabs.io/v1/speech-to-text"


async def transcribe(body: bytes, content_type: str) -> dict:
    headers = {
        "xi-api-key": settings.elevenlabs_api_key,
        "Content-Type": content_type,
    }
    async with httpx.AsyncClient(timeout=300.0) as client:
        resp = await client.post(ELEVENLABS_SCRIBE_URL, content=body, headers=headers)

    if resp.status_code != 200:
        logger.error("ElevenLabs API error: %d %s", resp.status_code, resp.text)
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"ElevenLabs API error: {resp.text}",
        )
    return resp.json()
