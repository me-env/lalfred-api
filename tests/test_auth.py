from unittest.mock import AsyncMock, patch

import httpx
import pytest
from sqlalchemy import select

from app.models import User


@pytest.mark.asyncio
async def test_google_login_returns_url(client):
    resp = await client.get("/auth/google/login")
    assert resp.status_code == 200
    data = resp.json()
    assert "url" in data
    assert "accounts.google.com" in data["url"]


@pytest.mark.asyncio
async def test_google_callback_creates_user(client, db_session):
    mock_token_response = httpx.Response(
        200,
        json={
            "access_token": "mock-access-token",
            "token_type": "Bearer",
            "id_token": "mock-id-token",
        },
    )
    mock_userinfo_response = httpx.Response(
        200,
        json={
            "sub": "new-google-sub-456",
            "email": "newuser@example.com",
            "name": "New User",
            "picture": "https://example.com/photo.jpg",
        },
    )

    with patch("app.providers.google_provider.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_token_response)
        mock_client.get = AsyncMock(return_value=mock_userinfo_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        resp = await client.get("/auth/google/callback", params={"code": "test-code"})
        assert resp.status_code == 200

    user = (
        await db_session.execute(
            select(User).where(User.google_sub == "new-google-sub-456")
        )
    ).scalar_one()
    assert user.email == "newuser@example.com"
    assert user.name == "New User"


@pytest.mark.asyncio
async def test_google_callback_existing_user_updates(client, test_user):
    mock_token_response = httpx.Response(
        200,
        json={"access_token": "mock-access-token", "token_type": "Bearer"},
    )
    mock_userinfo_response = httpx.Response(
        200,
        json={
            "sub": test_user.google_sub,
            "email": "updated@example.com",
            "name": "Updated Name",
            "picture": "https://example.com/new.jpg",
        },
    )

    with patch("app.providers.google_provider.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_token_response)
        mock_client.get = AsyncMock(return_value=mock_userinfo_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        resp = await client.get("/auth/google/callback", params={"code": "test-code"})
        assert resp.status_code == 200
