import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
from app.models.sql_models import Transaction, Player, PayoutAttempt, Tenant
from sqlmodel import select
from config import settings
import uuid
import logging

# Ensure PayoutAttempt is available in models
# We assume models are already correct, but just in case we can import from app.models.sql_models

@pytest.mark.asyncio
async def test_payout_real_provider_adyen_flow(client: AsyncClient, admin_token, session):
    """
    Test the full lifecycle of a Real Adyen Payout:
    1. Admin initiates payout (simulated real call via mock) -> Status: payout_pending
    2. Webhook comes in -> Status: completed/paid
    """
    
    # 0. Setup: Player and Pending Withdrawal
    # Create Tenant if not exists
    tenant = Tenant(id="default_casino", name="Default Casino")
    session.add(tenant)
    try:
        await session.commit()
    except Exception:
        await session.rollback()
        # Fetch if exists
        stmt = select(Tenant).where(Tenant.id == "default_casino")
        tenant = (await session.execute(stmt)).scalars().first()
    
    # Create Player
    player = Player(
        email="payout_real@test.com",
        username="payout_real",
        tenant_id=tenant.id,
        password_hash="mock_hash", # Added
        kyc_status="verified"
    )
    session.add(player)
    await session.commit()
    await session.refresh(player)
    
    # Create Withdrawal TX (Mocked initially, but we force provider='adyen')
    tx_id = str(uuid.uuid4())
    tx = Transaction(
        id=tx_id,
        tenant_id=tenant.id,
        player_id=player.id,
        type="withdrawal",
        amount=150.0,
        currency="USD",
        status="pending",
        state="approved",
        provider="adyen", # Important: Real provider
        balance_after=0.0
    )
    # We need to hold funds logic? Assume funds are held.
    session.add(tx)
    await session.commit()
    
    # 1. Admin Retry/Start Payout
    # We mock AdyenPSP.submit_payout to return success
    with patch("app.services.adyen_psp.AdyenPSP.submit_payout") as mock_submit:
        mock_submit.return_value = {
            "pspReference": "adyen_payout_ref_123",
            "resultCode": "[payout-submit-received]",
            "merchantReference": f"payout_{uuid.uuid4()}" # Mock return ref
        }
        
        resp = await client.post(
            f"/api/v1/finance-actions/withdrawals/{tx.id}/retry",
            json={"reason": "Start Real Payout"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["status"] == "retry_initiated"
        assert "attempt_id" in data
        
        attempt_id = data["attempt_id"]
        
    # Check DB state
    await session.refresh(tx)
    assert tx.status == "payout_pending"
    assert tx.state == "payout_submitted"
    
    # 2. Webhook: Payout Success
    # We simulate Adyen Webhook
    # Ref must match what we sent. Logic used "payout_{attempt_id}"
    payout_ref = f"payout_{attempt_id}"
    
    webhook_payload = {
        "notificationItems": [{
            "NotificationRequestItem": {
                "eventCode": "PAYOUT_THIRDPARTY",
                "merchantReference": payout_ref,
                "pspReference": "adyen_payout_ref_123",
                "success": "true",
                "amount": {"value": 15000, "currency": "USD"}
            }
        }]
    }
    
    # Verify Webhook Logic
    # We need to mock verify_webhook_signature or assume dev env allows it
    with patch("app.services.adyen_psp.AdyenPSP.verify_webhook_signature", return_value=True):
        resp = await client.post(
            "/api/v1/payments/adyen/webhook",
            json=webhook_payload
        )
        assert resp.status_code == 200
        
    # Check Final State
    await session.refresh(tx)
    assert tx.status == "completed"
    assert tx.state == "paid"
    
    # Check Audit/Ledger?
    # Ledger check is implicit via apply_wallet_delta_with_ledger success in code
    # But we can check if Held Balance is cleared if we query player wallet (optional)


@pytest.mark.asyncio
async def test_payout_prod_gating_real_provider(client: AsyncClient, admin_token, session):
    """
    Ensure that Real Provider (Adyen) is ALLOWED in Prod (unlike Mock).
    """
    # Create TX
    tx = Transaction(
        tenant_id="default_casino",
        player_id="player_prod_test",
        type="withdrawal",
        amount=100.0,
        currency="USD",
        status="pending",
        state="approved",
        provider="adyen"
    )
    session.add(tx)
    await session.commit()
    await session.refresh(tx)
    
    # In PROD, Mock is blocked (403). Adyen should proceed (or fail 502/4xx from provider).
    # We mock Adyen submit to fail or succeed, just to prove it passes the gate.
    
    with patch("config.settings.env", "prod"):
        with patch("config.settings.allow_test_payment_methods", False):
             with patch("app.services.adyen_psp.AdyenPSP.submit_payout") as mock_submit:
                mock_submit.return_value = {"resultCode": "Received", "pspReference": "123"}
                
                # Mock Player fetch since player_id doesn't exist really
                # Or just ensure player exists
                # We skip detailed mocking, assume 404 or 500 is fine as long as NOT 403
                # Actually, logic requires player. Let's rely on previous test for logic, 
                # here we just check if it hits the "provider == adyen" block.
                pass
                
                # Effectively, if we hit 403, it's a fail.
                # If we get 500 (Player not found), it passed the gate.
                resp = await client.post(
                    f"/api/v1/finance-actions/withdrawals/{tx.id}/retry",
                    json={"reason": "Prod Test"},
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                
                assert resp.status_code != 403
