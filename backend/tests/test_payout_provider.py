import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
async def test_payout_provider_mock_gated_in_prod(client: AsyncClient, admin_token, session):
    """
    Ensure mock payouts are gated in production.
    """
    # Assuming the finance_actions router checks settings.allow_test_payment_methods 
    # OR settings.env for mock provider logic.
    # The requirement is "prod’da mock payout kapalı (403)".
    
    # We haven't implemented the gating change in finance_actions.py yet, let's do TDD.
    # We need to find the route for payout approval or execution.
    pass 
