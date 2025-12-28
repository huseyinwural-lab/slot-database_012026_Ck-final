import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_kyc_mock_endpoints_gated_when_flag_off(client: AsyncClient, admin_token: str):
    # If feature flag is off, we should fail-closed (404)
    # However, the feature_required dependency may return 403 first
    from config import settings

    old = settings.kyc_mock_enabled
    settings.kyc_mock_enabled = False
    try:
        resp = await client.get(
            "/api/v1/kyc/dashboard",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        # Accept either 403 (feature disabled) or 404 (mock gated)
        assert resp.status_code in [403, 404]

        resp = await client.get(
            "/api/v1/kyc/queue",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        # Accept either 403 (feature disabled) or 404 (mock gated)
        assert resp.status_code in [403, 404]
    finally:
        settings.kyc_mock_enabled = old