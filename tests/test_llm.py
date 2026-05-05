from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.pricing import llm_credits

MOCK_OPENAI_RESPONSE = {
    "id": "chatcmpl-abc123",
    "object": "chat.completion",
    "model": "gpt-4.1",
    "choices": [
        {
            "index": 0,
            "message": {"role": "assistant", "content": "Hello!"},
            "finish_reason": "stop",
        }
    ],
    "usage": {
        "prompt_tokens": 10,
        "completion_tokens": 5,
        "total_tokens": 15,
    },
}

EXPECTED_CREDITS = llm_credits(10, 5, "gpt-4.1")
CHAT_BODY = {
    "model": "gpt-4.1",
    "messages": [{"role": "user", "content": "Hi"}],
}


def _patch_openai(response_json: dict | None = None, status_code: int = 200):
    json_data = response_json or MOCK_OPENAI_RESPONSE
    mock_response = httpx.Response(status_code, json=json_data)
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    return patch(
        "app.providers.openai_provider.httpx.AsyncClient",
        return_value=mock_client,
    )


@pytest.mark.asyncio
async def test_chat_success(client, test_user, auth_token):
    with _patch_openai():
        resp = await client.post(
            "/llm/chat",
            headers={"Authorization": f"Bearer {auth_token}"},
            json=CHAT_BODY,
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["choices"][0]["message"]["content"] == "Hello!"
    assert data["credits_used"] == EXPECTED_CREDITS


@pytest.mark.asyncio
async def test_chat_deducts_credits(client, test_user, auth_token):
    initial_credits = test_user.credits

    with _patch_openai():
        await client.post(
            "/llm/chat",
            headers={"Authorization": f"Bearer {auth_token}"},
            json=CHAT_BODY,
        )

    balance_resp = await client.get(
        "/credits/balance", headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert balance_resp.json()["credits"] == initial_credits - EXPECTED_CREDITS


@pytest.mark.asyncio
async def test_chat_negative_balance_rejected(client, db_session, test_user, auth_token):
    test_user.credits = -1
    await db_session.commit()

    resp = await client.post(
        "/llm/chat",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=CHAT_BODY,
    )
    assert resp.status_code == 402


@pytest.mark.asyncio
async def test_chat_invalid_model_rejected(client, test_user, auth_token):
    body = {**CHAT_BODY, "model": "gpt-3.5-turbo"}
    resp = await client.post(
        "/llm/chat",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=body,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_chat_mini_model(client, test_user, auth_token):
    mini_response = {
        **MOCK_OPENAI_RESPONSE,
        "model": "gpt-4.1-mini",
    }
    body = {**CHAT_BODY, "model": "gpt-4.1-mini"}

    with _patch_openai(mini_response):
        resp = await client.post(
            "/llm/chat",
            headers={"Authorization": f"Bearer {auth_token}"},
            json=body,
        )
    assert resp.status_code == 200
    assert resp.json()["model"] == "gpt-4.1-mini"


@pytest.mark.asyncio
async def test_chat_unauthenticated(client):
    resp = await client.post("/llm/chat", json=CHAT_BODY)
    assert resp.status_code in (401, 403)
