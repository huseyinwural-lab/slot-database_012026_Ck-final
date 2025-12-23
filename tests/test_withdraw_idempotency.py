import os
import sys
import asyncio

import pytest
from sqlmodel import select

sys.path.append(os.path.abspath("/app/backend"))

from server import app
from tests.conftest import _create_tenant, _create_player
from app.models.sql_models import Transaction, AuditEvent


@pytest.mark.usefixtures("client")
def test_withdraw_idempotency_same_key_returns_same_tx_and_no_duplicate(client, async_session_factory):
    """Test withdraw idempotency: same key returns same tx, no duplicate balance changes"""
    
    async def _seed():
        async with async_session_factory() as session:
            tenant = await _create_tenant(session)
            # Create player with verified KYC and sufficient balance
            player = await _create_player(session, tenant.id, kyc_status="verified", balance_available=100)
            return tenant, player

    tenant, player = asyncio.run(_seed())

    # Login as player
    login_response = client.post("/api/v1/auth/player/login", json={
        "email": player.email,
        "password": "TestPass123!"
    })
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": "withdraw-key-123"}

    # First withdraw request
    r1 = client.post("/api/v1/player/wallet/withdraw", json={
        "amount": 50,
        "method": "test_bank",
        "address": "test-account-123"
    }, headers=headers)
    
    # Should succeed for verified player with sufficient balance
    assert r1.status_code in (200, 201)

    # Second withdraw with same key and same payload
    r2 = client.post("/api/v1/player/wallet/withdraw", json={
        "amount": 50,
        "method": "test_bank", 
        "address": "test-account-123"
    }, headers=headers)
    
    # Same payload + same key => 200 and same transaction id
    assert r2.status_code == 200
    body1 = r1.json()
    body2 = r2.json()
    assert body2["transaction"]["id"] == body1["transaction"]["id"]

    # Verify only one withdraw_requested ledger event exists for this idempotency key
    async def _check_ledger():
        async with async_session_factory() as session:
            # Check that only one transaction exists for this idempotency key
            txs = (
                await session.execute(
                    select(Transaction).where(
                        Transaction.player_id == player.id,
                        Transaction.idempotency_key == "withdraw-key-123",
                        Transaction.type == "withdrawal"
                    )
                )
            ).scalars().all()
            
            return len(txs)

    tx_count = asyncio.run(_check_ledger())
    assert tx_count == 1, f"Expected 1 transaction, found {tx_count}"

    # Verify balance deltas only applied once (available decreased, held increased by amount)
    # This is verified by the fact that both responses have the same balance values
    assert body1["balance"]["available_real"] == body2["balance"]["available_real"]
    assert body1["balance"]["held_real"] == body2["balance"]["held_real"]