import pytest
from httpx import AsyncClient
from app.services.metrics import metrics

@pytest.mark.asyncio
async def test_ops_dashboard(client: AsyncClient, admin_token: str):
    """
    Test the /api/v1/ops/dashboard endpoint.
    """
    # Simulate some activity
    metrics.increment_request()
    metrics.increment_error_4xx()
    metrics.record_webhook_event("stripe", "checkout.session.completed")
    metrics.record_reconciliation_result(5, 1)

    resp = await client.get(
        "/api/v1/ops/dashboard",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    
    assert "http" in data
    assert "webhooks" in data
    assert "reconciliation" in data
    
    assert data["http"]["total_requests"] >= 1
    assert data["http"]["errors_4xx"] >= 1
    
    assert data["webhooks"]["events"]["stripe_checkout.session.completed"] >= 1
    
    assert data["reconciliation"]["runs"] >= 1
    assert data["reconciliation"]["critical_findings"] >= 1

@pytest.mark.asyncio
async def test_metrics_middleware(client: AsyncClient):
    """
    Test that middleware captures requests.
    """
    initial_count = metrics.request_count
    
    # Make a request to a public endpoint (e.g. health)
    await client.get("/api/health")
    
    assert metrics.request_count == initial_count + 1
