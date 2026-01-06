import pytest


@pytest.mark.asyncio
async def test_player_ops_credit_debit_bonus_suspend_force_logout(client, session, admin_token):
    # Create a player under default tenant by using existing endpoint
    create = await client.post(
        "/api/v1/auth/player/register",
        json={"email": "ops_player@test.com", "username": "opsplayer", "password": "Test12345!"},
    )
    assert create.status_code in (200, 400)

    # Fetch players list to get id
    res = await client.get(
        "/api/v1/players",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    pid = res.json()["items"][0]["id"]

    # credit
    r = await client.post(
        f"/api/v1/players/{pid}/credit",
        json={"amount": 10, "currency": "USD", "reason": "manual credit"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 200

    # debit insufficient
    r2 = await client.post(
        f"/api/v1/players/{pid}/debit",
        json={"amount": 999999, "currency": "USD", "reason": "manual debit"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r2.status_code == 409

    # suspend
    r3 = await client.post(
        f"/api/v1/players/{pid}/suspend",
        json={"reason": "fraud"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r3.status_code == 200
    assert r3.json()["status"] == "suspended"

    # unsuspend
    r4 = await client.post(
        f"/api/v1/players/{pid}/unsuspend",
        json={"reason": "resolved"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r4.status_code == 200
    assert r4.json()["status"] == "active"

    # bonus grant (cash)
    r5 = await client.post(
        f"/api/v1/players/{pid}/bonuses",
        json={"bonus_type": "cash", "amount": 5, "reason": "promo"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r5.status_code == 200
    grant_id = r5.json()["id"]

    # list bonuses
    r6 = await client.get(
        f"/api/v1/players/{pid}/bonuses",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r6.status_code == 200
    assert any(b["id"] == grant_id for b in r6.json())

    # force logout
    r7 = await client.post(
        f"/api/v1/players/{pid}/force-logout",
        json={"reason": "ops"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r7.status_code == 200


@pytest.mark.asyncio
async def test_player_ops_requires_reason(client, admin_token):
    # get a player id
    res = await client.get(
        "/api/v1/players",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    pid = res.json()["items"][0]["id"]

    r = await client.post(
        f"/api/v1/players/{pid}/credit",
        json={"amount": 10, "currency": "USD"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 400
