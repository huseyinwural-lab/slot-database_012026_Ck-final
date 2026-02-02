import os
import sys

import pytest

sys.path.append(os.path.abspath("/app/backend"))


from tests.conftest import _create_tenant, _create_player, _make_player_token


@pytest.mark.usefixtures("client")
def test_kyc_withdraw_block(client, async_session_factory):
    # Create unverified player
    async def seed():
        async with async_session_factory() as session:
            tenant = await _create_tenant(session)
            player = await _create_player(session, tenant.id, kyc_status="pending")
            token = _make_player_token(player.id, tenant.id)
            return player, token

    import asyncio

    player, token = asyncio.run(seed())

    headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": "wd-kyc-001"}
    r = client.post(
        "/api/v1/player/wallet/withdraw",
        json={"amount": 10, "method": "bank", "address": "addr"},
        headers=headers,
    )
    assert r.status_code == 403
    body = r.json()
    # AppError handler wraps error_code at top level; HTTPException(detail={error_code}) puts it under 'detail'
    assert body.get("error_code") == "KYC_REQUIRED_FOR_WITHDRAWAL" or body.get("detail", {}).get("error_code") == "KYC_REQUIRED_FOR_WITHDRAWAL"
