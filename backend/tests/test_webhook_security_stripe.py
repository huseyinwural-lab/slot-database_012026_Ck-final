import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
from app.models.sql_models import Transaction
import stripe

@pytest.mark.asyncio
async def test_stripe_webhook_signature_failure(client: AsyncClient, session):
    """
    Test that invalid signature returns 401/400.
    """
    with patch("config.settings.webhook_signature_enforced", True):
        with patch("config.settings.stripe_webhook_secret", "whsec_test"):
            # We need to mock the stripe.Webhook.construct_event to raise error
            with patch("stripe.Webhook.construct_event", side_effect=stripe.error.SignatureVerificationError("Invalid sig", "sig", "body")):
                resp = await client.post(
                    "/api/v1/payments/stripe/webhook",
                    content=b"{}",
                    headers={"stripe-signature": "invalid"}
                )
                # The code catches Exception and raises 400
                assert resp.status_code == 400
                assert "Webhook Error" in resp.json()["detail"]

@pytest.mark.asyncio
async def test_stripe_webhook_replay_protection(client: AsyncClient, session):
    """
    Test that replaying the same webhook (same provider_event_id) returns 200 no-op.
    """
    # 1. Create a completed transaction first
    tx = Transaction(
        tenant_id="default_casino",
        player_id="player1",
        type="deposit",
        amount=100.0,
        currency="USD",
        status="completed",
        state="completed",
        provider="stripe",
        provider_event_id="evt_replay_test"
    )
    session.add(tx)
    await session.commit()

    # 2. Mock construct_event to return an event with that ID
    mock_event = MagicMock()
    mock_event.type = "checkout.session.completed"
    
    # Nested mock object for data.object.id
    mock_session_obj = MagicMock()
    mock_session_obj.id = "evt_replay_test"
    mock_event.data.object = mock_session_obj
    
    with patch("config.settings.stripe_webhook_secret", "whsec_test"):
         with patch("stripe.Webhook.construct_event", return_value=mock_event):
            resp = await client.post(
                "/api/v1/payments/stripe/webhook",
                content=b"{}",
                headers={"stripe-signature": "valid"}
            )
            
            assert resp.status_code == 200
            assert resp.json()["status"] == "success"
            # It should be idempotent (no double spend) - handled by tx status check
