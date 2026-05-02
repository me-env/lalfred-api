import pytest


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
