import pytest
from httpx import AsyncClient
from app.models.sql_models import Transaction, AuditEvent
from sqlmodel import select

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
        provider_event_id="tx_evt_123", 
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
    assert player.balance_real_available == 0.0 
    
    # 4. Verify Replay (Idempotency)
    resp2 = await client.post(
        f"/api/v1/finance/deposits/{tx.id}/refund",
        json={"reason": "Fraudulent transaction"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    # Should be 200 idempotent
    assert resp2.status_code == 200
    assert resp2.json()["message"] == "Already reversed"

    # 5. Verify Audit Logs
    stmt = select(AuditEvent).where(AuditEvent.resource_id == tx.id).order_by(AuditEvent.timestamp)
    audits = (await session.execute(stmt)).scalars().all()
    
    actions = [a.action for a in audits]
    assert "FIN_DEPOSIT_REFUND_REQUESTED" in actions
    assert "FIN_DEPOSIT_REFUND_COMPLETED" in actions

@pytest.mark.asyncio
async def test_admin_refund_invalid_state(client: AsyncClient, session, admin_token):
    # Create pending deposit
    tx = Transaction(
        tenant_id="default_casino",
        player_id="player_refund_test", # Reusing player from previous test might be risky if parallel, but fixtures usually reset DB or we use different ID
        type="deposit",
        amount=50.0,
        currency="USD",
        status="pending",
        state="pending_provider",
        provider="stripe"
    )
    session.add(tx)
    await session.commit()
    await session.refresh(tx)
    
    resp = await client.post(
        f"/api/v1/finance/deposits/{tx.id}/refund",
        json={"reason": "Premature refund"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert resp.status_code == 400
    assert "not in completed state" in resp.json()["detail"]
    
    # Verify Audit REJECTED
    stmt = select(AuditEvent).where(
        AuditEvent.resource_id == tx.id, 
        AuditEvent.action == "FIN_DEPOSIT_REFUND_REJECTED"
    )
    audit = (await session.execute(stmt)).scalars().first()
    assert audit is not None
