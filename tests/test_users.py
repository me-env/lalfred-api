import pytest


@pytest.mark.asyncio
async def test_get_me(client, test_user, auth_token):
    resp = await client.get("/users/me", headers={"Authorization": f"Bearer {auth_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "test@example.com"
    assert data["credits"] == 10


@pytest.mark.asyncio
async def test_get_me_no_auth(client):
    resp = await client.get("/users/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_invalid_token(client):
    resp = await client.get("/users/me", headers={"Authorization": "Bearer invalid-token"})
    assert resp.status_code == 401
