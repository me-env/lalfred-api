import logging

import httpx
from fastapi import HTTPException, status

from app.config import settings
from app.schemas.llm import ChatRequest

logger = logging.getLogger(__name__)

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"


async def chat(request: ChatRequest) -> dict:
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    payload = request.model_dump(exclude_none=True)

    async with httpx.AsyncClient(timeout=300.0) as client:
        resp = await client.post(OPENAI_CHAT_URL, headers=headers, json=payload)

    if resp.status_code != 200:
        logger.error("OpenAI API error: %d %s", resp.status_code, resp.text)
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"OpenAI API error: {resp.text}",
        )
    return resp.json()
