import pytest
from httpx import AsyncClient
from unittest.mock import patch
from app.models.sql_models import Transaction

@pytest.mark.asyncio
async def test_adyen_webhook_signature_failure(client: AsyncClient):
    """
    Test Adyen webhook signature failure.
    """
    # Assuming AdyenPSP logic uses settings.adyen_hmac_key
    with patch("config.settings.adyen_hmac_key", "hmac_key"):
        # We need to mock the verification logic inside AdyenPSP or the route
        # Since I'll implement verify_webhook_signature in AdyenPSP, I can patch it
        with patch("app.services.adyen_psp.AdyenPSP.verify_webhook_signature", return_value=False):
            resp = await client.post(
                "/api/v1/payments/adyen/webhook",
                json={"notificationItems": [{"NotificationRequestItem": {"eventCode": "AUTHORISATION"}}]}
            )
            # Depending on implementation, might be 401 or 403 or 200 with "ignored"
            # But hardening spec says 401 WEBHOOK_SIGNATURE_INVALID ideally
            assert resp.status_code == 401
            assert "WEBHOOK_SIGNATURE_INVALID" in resp.json()["detail"]

@pytest.mark.asyncio
async def test_adyen_webhook_replay_protection(client: AsyncClient, session):
    """
    Test Adyen replay protection.
    """
    # 1. Completed TX
    tx = Transaction(
        tenant_id="default_casino",
        player_id="player1",
        type="deposit",
        amount=50.0,
        currency="EUR",
        status="completed",
        state="completed",
        provider="adyen",
        provider_event_id="psp_ref_replay",
        provider_ref="psp_ref_replay"
    )
    session.add(tx)
    await session.commit()
    
    with patch("app.services.adyen_psp.AdyenPSP.verify_webhook_signature", return_value=True):
        payload = {
            "notificationItems": [{
                "NotificationRequestItem": {
                    "eventCode": "AUTHORISATION",
                    "merchantReference": tx.id,
                    "pspReference": "psp_ref_replay",
                    "success": "true"
                }
            }]
        }
        resp = await client.post(
            "/api/v1/payments/adyen/webhook",
            json=payload
        )
        assert resp.status_code == 200
        # Should not throw error
