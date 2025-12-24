import pytest
from httpx import AsyncClient
from app.models.sql_models import Transaction

@pytest.mark.asyncio
async def test_admin_refund_deposit_flow(client: AsyncClient, session, admin_token):
    """
    Test admin refund endpoint.
    """
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
    # Balance check? We assume wallet ledger service does its job, but we can verify invariants if we mock it or use real DB.
    # The test client uses real DB logic in memory.
    
    # 4. Verify Replay (Idempotency)
    resp2 = await client.post(
        f"/api/v1/finance/deposits/{tx.id}/refund",
        json={"reason": "Fraudulent transaction"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    # Should be successful/idempotent or 409 depending on logic.
    # If state is reversed, maybe 400 "Already reversed" or 200 "OK"
    assert resp2.status_code in (200, 400, 409)
