import pytest

from app.config import settings


@pytest.mark.asyncio
async def test_get_balance(client, test_user, auth_token):
    resp = await client.get("/credits/balance", headers={"Authorization": f"Bearer {auth_token}"})
    assert resp.status_code == 200
    assert resp.json()["credits"] == 10


@pytest.mark.asyncio
async def test_list_transactions_empty(client, test_user, auth_token):
    resp = await client.get(
        "/credits/transactions", headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_get_signup_bonus_is_public(client):
    resp = await client.get("/credits/signup-bonus")
    assert resp.status_code == 200
    assert resp.json() == {"credits": settings.initial_free_credits}


@pytest.mark.asyncio
async def test_get_signup_bonus_reflects_setting(client, monkeypatch):
    monkeypatch.setattr(settings, "initial_free_credits", 1234)
    resp = await client.get("/credits/signup-bonus")
    assert resp.status_code == 200
    assert resp.json() == {"credits": 1234}
