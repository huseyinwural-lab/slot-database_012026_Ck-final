import os
import sys

import pytest

sys.path.append(os.path.abspath("/app/backend"))




@pytest.mark.usefixtures("client", "player_with_token")
@pytest.mark.asyncio
async def test_withdraw_hold_invariant(client, player_with_token):
    tenant, player, token = player_with_token

    # Seed initial balance
    # For simplicity, call deposit once to give player balance
    headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": "dep-001"}
    r_dep = await client.post(
        "/api/v1/player/wallet/deposit",
        json={"amount": 100, "method": "card"},
        headers=headers,
    )
    assert r_dep.status_code in (200, 201)

    # Capture balances before withdraw
    r_bal_before = await client.get("/api/v1/player/wallet/balance", headers={"Authorization": f"Bearer {token}"})
    assert r_bal_before.status_code == 200
    bal_before = r_bal_before.json()
    avail_before = bal_before["available_real"]
    held_before = bal_before["held_real"]
    total_before = bal_before["total_real"]

    # Perform withdraw
    wd_headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": "wd-001"}
    r_wd = await client.post(
        "/api/v1/player/wallet/withdraw",
        json={"amount": 30, "method": "bank", "address": "addr"},
        headers=wd_headers,
    )
    assert r_wd.status_code in (200, 201)

    # Balances after withdraw
    r_bal_after = await client.get("/api/v1/player/wallet/balance", headers={"Authorization": f"Bearer {token}"})
    assert r_bal_after.status_code == 200
    bal_after = r_bal_after.json()
    avail_after = bal_after["available_real"]
    held_after = bal_after["held_real"]
    total_after = bal_after["total_real"]

    assert avail_after == pytest.approx(avail_before - 30)
    assert held_after == pytest.approx(held_before + 30)
    assert total_after == pytest.approx(total_before)
