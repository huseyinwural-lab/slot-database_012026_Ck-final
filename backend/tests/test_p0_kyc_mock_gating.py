import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_kyc_mock_endpoints_gated_when_flag_off(client: AsyncClient, admin_token: str):
    # KYC is gated in two ways:
    # 1) feature flag: can_manage_kyc (403)
    # 2) mock kill-switch: KYC_MOCK_ENABLED (404)
    from config import settings

    old = settings.kyc_mock_enabled
    settings.kyc_mock_enabled = False
    try:
        resp = await client.get(
            "/api/v1/kyc/dashboard",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code in {403, 404}

        resp = await client.get(
            "/api/v1/kyc/queue",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code in {403, 404}
    finally:
        settings.kyc_mock_enabled = old
