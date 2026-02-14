import os
import sys

import pytest

sys.path.append(os.path.abspath("/app/backend"))


from tests.conftest import _create_tenant, _create_player, _make_player_token


@pytest.mark.usefixtures("client")
def test_unverified_deposit_cap(client, async_session_factory, monkeypatch):
    # Set cap to 100 for test
    monkeypatch.setenv("KYC_UNVERIFIED_DAILY_DEPOSIT_CAP", "100")

    async def seed():
        async with async_session_factory() as session:
            tenant = await _create_tenant(session)
            # Unverified player
            player = await _create_player(session, tenant.id, kyc_status="pending")
            token = _make_player_token(player.id, tenant.id)
            return player, token

    import asyncio

    player, token = asyncio.run(seed())

    headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": "dep-cap-1"}

    # First deposit within cap
    r1 = client.post(
        "/api/v1/player/wallet/deposit",
        json={"amount": 60, "method": "card"},
        headers=headers,
    )
    assert r1.status_code in (200, 201)

    # Second deposit to hit cap exactly
    headers2 = {"Authorization": f"Bearer {token}", "Idempotency-Key": "dep-cap-2"}
    r2 = client.post(
        "/api/v1/player/wallet/deposit",
        json={"amount": 40, "method": "card"},
        headers=headers2,
    )
    assert r2.status_code in (200, 201)

    # Third deposit exceeding cap should be blocked
    headers3 = {"Authorization": f"Bearer {token}", "Idempotency-Key": "dep-cap-3"}
    r3 = client.post(
        "/api/v1/player/wallet/deposit",
        json={"amount": 10, "method": "card"},
        headers=headers3,
    )
    assert r3.status_code == 403
    body = r3.json()
    # AppError handler vs HTTPException(detail={error_code})
    assert body.get("error_code") == "KYC_DEPOSIT_LIMIT" or body.get("detail", {}).get("error_code") == "KYC_DEPOSIT_LIMIT"
