import os
import sys
import asyncio

import pytest

sys.path.append(os.path.abspath("/app/backend"))

from server import app  # noqa: F401
from app.models.reconciliation import ReconciliationFinding
from tests.test_finance_withdraw_admin_api import _seed_admin_and_player


@pytest.mark.usefixtures("client")
def test_findings_list_requires_admin_auth(client, async_session_factory):
    # Anonymous request should fail
    r = client.get("/api/v1/payments/reconciliation/findings")
    assert r.status_code in (401, 403)


@pytest.mark.usefixtures("client")
def test_findings_list_filters_and_pagination(client, async_session_factory):
    tenant, player, admin, player_token, admin_token = asyncio.run(_seed_admin_and_player(async_session_factory))

    async def _seed_findings():
        async with async_session_factory() as session:
            f1 = ReconciliationFinding(
                provider="mockpsp",
                tenant_id=tenant.id,
                player_id=player.id,
                tx_id="tx-1",
                provider_event_id="evt-1",
                finding_type="missing_in_ledger",
                severity="WARN",
                status="OPEN",
                message="test1",
            )
            f2 = ReconciliationFinding(
                provider="mockpsp",
                tenant_id=tenant.id,
                player_id=player.id,
                tx_id="tx-2",
                provider_event_id="evt-2",
                finding_type="missing_in_psp",
                severity="INFO",
                status="RESOLVED",
                message="test2",
            )
            session.add(f1)
            session.add(f2)
            await session.commit()

    asyncio.run(_seed_findings())

    headers_admin = {"Authorization": f"Bearer {admin_token}"}

    r = client.get(
        "/api/v1/payments/reconciliation/findings",
        params={"provider": "mockpsp", "status": "OPEN", "limit": 10, "offset": 0},
        headers=headers_admin,
    )
    assert r.status_code == 200
    data = r.json()
    assert "items" in data and "meta" in data
    assert data["meta"]["total"] >= 1
    assert all(item["status"] == "OPEN" for item in data["items"])


@pytest.mark.usefixtures("client")
def test_findings_resolve_happy_path(client, async_session_factory):
    tenant, player, admin, player_token, admin_token = asyncio.run(_seed_admin_and_player(async_session_factory))

    async def _seed_open_finding():
        async with async_session_factory() as session:
            f = ReconciliationFinding(
                provider="mockpsp",
                tenant_id=tenant.id,
                player_id=player.id,
                tx_id="tx-open",
                provider_event_id="evt-open",
                finding_type="missing_in_ledger",
                severity="WARN",
                status="OPEN",
            )
            session.add(f)
            await session.commit()
            await session.refresh(f)
            return f.id

    finding_id = asyncio.run(_seed_open_finding())

    headers_admin = {"Authorization": f"Bearer {admin_token}"}

    r = client.post(
        f"/api/v1/payments/reconciliation/findings/{finding_id}/resolve",
        headers=headers_admin,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == finding_id
    assert body["status"] == "RESOLVED"

    async def _load():
        async with async_session_factory() as session:
            f = await session.get(ReconciliationFinding, finding_id)
            return f

    finding = asyncio.run(_load())
    assert finding.status == "RESOLVED"


@pytest.mark.usefixtures("client")
def test_findings_resolve_404(client, async_session_factory):
    tenant, player, admin, player_token, admin_token = asyncio.run(_seed_admin_and_player(async_session_factory))
    headers_admin = {"Authorization": f"Bearer {admin_token}"}

    r = client.post(
        "/api/v1/payments/reconciliation/findings/non-existent-id/resolve",
        headers=headers_admin,
    )
    assert r.status_code == 404
