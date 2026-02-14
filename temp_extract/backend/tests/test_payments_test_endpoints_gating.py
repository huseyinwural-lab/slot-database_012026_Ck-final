import pytest
from httpx import AsyncClient
from unittest.mock import patch

@pytest.mark.asyncio
async def test_stripe_webhook_simulation_gated_in_prod(client: AsyncClient):
    """
    Verify that /api/v1/payments/stripe/test-trigger-webhook returns 403 in production.
    """
    # We patch the settings object instance that is already imported in the route modules
    with patch("config.settings.env", "prod"):
        resp = await client.post(
            "/api/v1/payments/stripe/test-trigger-webhook",
            json={"type": "checkout.session.completed", "session_id": "fake"}
        )
        assert resp.status_code == 403
        assert "Not available in production" in resp.json()["detail"]

@pytest.mark.asyncio
async def test_adyen_webhook_simulation_gated_in_prod(client: AsyncClient):
    """
    Verify that /api/v1/payments/adyen/test-trigger-webhook returns 403 in production.
    """
    with patch("config.settings.env", "prod"):
        resp = await client.post(
            "/api/v1/payments/adyen/test-trigger-webhook",
            json={"tx_id": "fake", "success": True}
        )
        assert resp.status_code == 403
        assert "Not available in production" in resp.json()["detail"]

@pytest.mark.asyncio
async def test_stripe_webhook_simulation_allowed_in_dev(client: AsyncClient):
    """
    Verify that in dev (default), it is reachable (might fail validation, but not 403).
    """
    # Assuming default env is dev or test
    resp = await client.post(
        "/api/v1/payments/stripe/test-trigger-webhook",
        json={"type": "checkout.session.completed", "session_id": "fake_allowed"}
    )
    # It might return 200 {"status": "ignored"} or similar, but definitely NOT 403
    assert resp.status_code != 403
