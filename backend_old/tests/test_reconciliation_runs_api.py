from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reconciliation_run import ReconciliationRun


@pytest.mark.asyncio
async def test_create_reconciliation_run_basic(client: AsyncClient, admin_token: str):
    now = datetime.now(timezone.utc)
    payload = {
        "provider": "mockpsp",
        "window_start": now.isoformat(),
        "window_end": (now + timedelta(hours=1)).isoformat(),
        "dry_run": True,
    }

    resp = await client.post("/api/v1/reconciliation/runs", json=payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["provider"] == "mockpsp"
    assert data["dry_run"] is True
    assert data["status"] == "queued"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_reconciliation_run_idempotent(client: AsyncClient, admin_token: str, session: AsyncSession):
    now = datetime.now(timezone.utc)
    idem_key = "mockpsp-2025-01-01-00-24h"
    payload = {
        "provider": "mockpsp",
        "window_start": now.isoformat(),
        "window_end": (now + timedelta(hours=1)).isoformat(),
        "dry_run": False,
        "idempotency_key": idem_key,
    }

    headers = {"Authorization": f"Bearer {admin_token}"}

    resp1 = await client.post("/api/v1/reconciliation/runs", json=payload, headers=headers)
    resp2 = await client.post("/api/v1/reconciliation/runs", json=payload, headers=headers)

    assert resp1.status_code == 200, resp1.text
    assert resp2.status_code == 200, resp2.text

    data1 = resp1.json()
    data2 = resp2.json()

    assert data1["id"] == data2["id"]


@pytest.mark.asyncio
async def test_get_and_list_reconciliation_runs(client: AsyncClient, admin_token: str, session: AsyncSession):
    # Seed a run directly
    now = datetime.now(timezone.utc)
    run = ReconciliationRun(
        provider="mockpsp",
        window_start=now,
        window_end=now + timedelta(hours=1),
        dry_run=False,
        status="queued",
    )
    session.add(run)
    await session.commit()
    await session.refresh(run)

    headers = {"Authorization": f"Bearer {admin_token}"}

    # GET
    resp_get = await client.get(f"/api/v1/reconciliation/runs/{run.id}", headers=headers)
    assert resp_get.status_code == 200
    data_get = resp_get.json()
    assert data_get["id"] == run.id

    # LIST
    resp_list = await client.get("/api/v1/reconciliation/runs", headers=headers)
    assert resp_list.status_code == 200
    data_list = resp_list.json()
    assert "items" in data_list
    assert any(item["id"] == run.id for item in data_list["items"])
