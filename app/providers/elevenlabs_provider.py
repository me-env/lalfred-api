import logging
import time

import httpx
from fastapi import HTTPException
from opentelemetry import metrics

from app.config import settings
from app.schemas.transcription import TranscriptionResult

logger = logging.getLogger(__name__)
meter = metrics.get_meter("lalfred.elevenlabs")

ELEVENLABS_SCRIBE_URL = "https://api.elevenlabs.io/v1/speech-to-text"


requests_counter = meter.create_counter(
    "elevenlabs.requests",
    description="The number of ElevenLabs requests",
)
request_duration = meter.create_histogram(
    "elevenlabs.transcribe.duration",
    description="Duration of ElevenLabs API requests",
)

async def transcribe(
    audio: bytes,
    content_type: str,
    *,
    model_id: str = "scribe_v2",
    no_verbatim: bool = True,
    tag_audio_events: bool = False,
    keyterms: list[str] | None = None,
) -> TranscriptionResult:
    headers = {"xi-api-key": settings.elevenlabs_api_key}
    files: list[tuple[str, tuple[str | None, str | bytes, str | None]]] = [
        ("model_id", (None, model_id, None)),
        ("no_verbatim", (None, str(no_verbatim).lower(), None)),
        ("tag_audio_events", (None, str(tag_audio_events).lower(), None)),
        ("file", ("audio", audio, content_type)),
    ]
    if keyterms:
        files.extend(("keyterms", (None, term, None)) for term in keyterms)

    start = time.monotonic()
    async with httpx.AsyncClient(timeout=300.0) as client:
        resp = await client.post(
            ELEVENLABS_SCRIBE_URL, headers=headers, files=files,
        )
    elapsed = time.monotonic() - start

    logger.info(f"ElevenLabs transcribe duration: {elapsed}s, model_id: {model_id}, http.status_code: {resp.status_code}")
    requests_counter.add(1, attributes={"model_id": model_id, "http.status_code": resp.status_code})
    request_duration.record(elapsed, attributes={"model_id": model_id})

    if resp.status_code != 200:
        logger.error("ElevenLabs API error: %d %s", resp.status_code, resp.text)
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"ElevenLabs API error: {resp.text}",
        )
    return TranscriptionResult.model_validate(resp.json())
