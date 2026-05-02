from unittest.mock import AsyncMock, patch

import httpx
import pytest


@pytest.mark.asyncio
async def test_transcribe_no_credits(client, db_session, test_user, auth_token):
    test_user.credits = 0
    await db_session.commit()

    resp = await client.post(
        "/transcribe",
        headers={"Authorization": f"Bearer {auth_token}"},
        content=b"audio-data",
    )
    assert resp.status_code == 402


@pytest.mark.asyncio
async def test_transcribe_success(client, test_user, auth_token):
    mock_response = httpx.Response(200, json={"text": "Hello world", "language_code": "en"})

    with patch("app.routers.transcribe.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        resp = await client.post(
            "/transcribe",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "multipart/form-data; boundary=abc",
            },
            content=b"audio-data",
        )
        assert resp.status_code == 200
        assert resp.json()["text"] == "Hello world"


@pytest.mark.asyncio
async def test_transcribe_deducts_credit(client, test_user, auth_token):
    initial_credits = test_user.credits
    mock_response = httpx.Response(200, json={"text": "test"})

    with patch("app.routers.transcribe.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        await client.post(
            "/transcribe",
            headers={"Authorization": f"Bearer {auth_token}"},
            content=b"audio-data",
        )

    balance_resp = await client.get(
        "/credits/balance", headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert balance_resp.json()["credits"] == initial_credits - 1
