import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
from app.models.sql_models import Transaction
from config import settings
from app.services.wallet_ledger import apply_wallet_delta_with_ledger

@pytest.mark.asyncio
async def test_admin_refund_deposit_flow(client: AsyncClient, session, admin_token):
    """
    Test admin refund endpoint.
    """
    # 0. Create Player
    from app.models.sql_models import Player
    player = Player(
        tenant_id="default_casino",
        id="player_refund_test",
        username="refund_user",
        email="refund@test.com",
        password_hash="hash",
        balance_real_available=100.0 # Match deposit amount
    )
    session.add(player)
    
    # 1. Create completed deposit
    tx = Transaction(
        tenant_id="default_casino",
        player_id="player_refund_test",
        type="deposit",
        amount=100.0,
        currency="USD",
        status="completed",
        state="completed",
        provider="stripe",
        provider_event_id="tx_evt_123", # Needs event id
        provider_ref="ref_123", # Needs provider ref for ledger
        balance_after=100.0
    )
    session.add(tx)
    await session.commit()
    await session.refresh(tx)

    # 2. Refund Call
    resp = await client.post(
        f"/api/v1/finance/deposits/{tx.id}/refund",
        json={"reason": "Fraudulent transaction"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "reversed"
    
    # 3. Verify Ledger / TX State
    await session.refresh(tx)
    assert tx.state == "reversed"
    
    await session.refresh(player)
    assert player.balance_real_available == 0.0 # 100 - 100 = 0
    
    # 4. Verify Replay (Idempotency)
    resp2 = await client.post(
        f"/api/v1/finance/deposits/{tx.id}/refund",
        json={"reason": "Fraudulent transaction"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    # Should be successful/idempotent or 409 depending on logic.
    assert resp2.status_code in (200, 400, 409)
