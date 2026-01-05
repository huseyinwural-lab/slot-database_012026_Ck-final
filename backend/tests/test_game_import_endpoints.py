import io
import json

import pytest
from sqlmodel import select

from app.models.game_models import Game
from app.models.sql_models import Tenant, AdminUser


@pytest.mark.asyncio
async def test_game_import_flow_json(client, session, admin_token):
    # Upload
    payload = {
        "items": [
            {"provider_id": "mock", "external_id": "g1", "name": "Game 1", "type": "slot", "rtp": 96.2},
            {"provider": "mock", "id": "g2", "name": "Game 2", "category": "slot"},
        ]
    }

    files = {
        "file": ("games.json", json.dumps(payload).encode("utf-8"), "application/json"),
    }

    res = await client.post(
        "/api/v1/game-import/manual/upload",
        files=files,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    job_id = res.json()["job_id"]

    # Job status
    res2 = await client.get(
        f"/api/v1/game-import/jobs/{job_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res2.status_code == 200
    body = res2.json()
    assert body["job_id"] == job_id
    assert body["status"] in {"ready", "completed"}
    assert body["total_items"] == 2

    # Import
    res3 = await client.post(
        f"/api/v1/game-import/jobs/{job_id}/import",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res3.status_code == 200
    assert res3.json()["status"] == "completed"
    assert res3.json()["imported_count"] >= 1

    # DB assertions (games created)
    stmt = select(Game).where(Game.external_id.in_(["g1", "g2"]))
    rows = (await session.execute(stmt)).scalars().all()
    assert len(rows) >= 2


@pytest.mark.asyncio
async def test_game_import_tenant_isolation_owner_header_scope(client, session):
    # Create two tenants and an owner admin
    t1 = Tenant(name="T1", type="owner", features={})
    t2 = Tenant(name="T2", type="renter", features={})
    session.add(t1)
    session.add(t2)
    await session.commit()
    await session.refresh(t1)
    await session.refresh(t2)

    owner = AdminUser(
        tenant_id=t1.id,
        username="owner",
        email="owner@test.com",
        full_name="Owner",
        password_hash="noop_hash",
        role="Admin",
        is_platform_owner=True,
    )
    session.add(owner)
    await session.commit()
    await session.refresh(owner)

    from app.utils.auth import create_access_token
    from datetime import timedelta

    token = create_access_token(
        data={"sub": owner.id, "email": owner.email, "tenant_id": owner.tenant_id, "role": "Admin"},
        expires_delta=timedelta(days=1),
    )

    # Create a job under tenant1 using direct DB insert (simpler than upload here)
    from app.models.game_import_sql import GameImportJob

    job = GameImportJob(tenant_id=t1.id, created_by_admin_id=owner.id, status="ready")
    session.add(job)
    await session.commit()
    await session.refresh(job)

    # Scope to tenant2 via header, should NOT see tenant1 job
    res = await client.get(
        f"/api/v1/game-import/jobs/{job.id}",
        headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": t2.id},
    )
    assert res.status_code == 404
