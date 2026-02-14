import pytest


@pytest.mark.asyncio
async def test_reports_overview_exports_and_sim_runs(client, admin_token):
    # Overview
    res = await client.get(
        "/api/v1/reports/overview",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    obj = res.json()
    assert "ggr" in obj and "ngr" in obj and "active_players" in obj

    # Exports list initially
    res2 = await client.get(
        "/api/v1/reports/exports",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res2.status_code == 200
    assert isinstance(res2.json(), list)

    # Create export
    res3 = await client.post(
        "/api/v1/reports/exports",
        json={"type": "overview_report", "requested_by": "admin"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res3.status_code == 200
    exp = res3.json()
    assert "export_id" in exp
    assert exp["status"] in {"completed", "processing"}

    # Exports list contains created job
    res4 = await client.get(
        "/api/v1/reports/exports",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res4.status_code == 200
    assert any(r.get("id") == exp["export_id"] for r in res4.json())

    # Simulation runs list
    res5 = await client.get(
        "/api/v1/simulation-lab/runs",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res5.status_code == 200
    assert isinstance(res5.json(), list)

    # Create run (id provided by frontend)
    run_id = "run_test_1"
    res6 = await client.post(
        "/api/v1/simulation-lab/runs",
        json={
            "id": run_id,
            "name": "Game Math - Test",
            "simulation_type": "game_math",
            "status": "draft",
            "created_by": "Admin",
            "notes": "test",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res6.status_code == 200
    assert res6.json()["id"] == run_id

    # Runs list contains it
    res7 = await client.get(
        "/api/v1/simulation-lab/runs",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert any(r.get("id") == run_id for r in res7.json())

    # Game math execute
    res8 = await client.post(
        "/api/v1/simulation-lab/game-math",
        json={"run_id": run_id, "spins_to_simulate": 1000, "rtp_override": 96.5},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res8.status_code == 200
    out = res8.json()
    assert out["run_id"] == run_id
    assert out["status"] == "completed"


@pytest.mark.asyncio
async def test_reports_and_simulation_tenant_isolation_owner_header(client, session):
    from app.models.sql_models import Tenant, AdminUser
    from app.models.reports_sql import ReportExportJob
    from app.models.simulation_sql import SimulationRun
    from app.utils.auth import create_access_token
    from datetime import timedelta

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
        email="owner_reports@test.com",
        full_name="Owner",
        password_hash="noop_hash",
        role="Admin",
        is_platform_owner=True,
    )
    session.add(owner)
    await session.commit()
    await session.refresh(owner)

    # Seed data for tenant1
    exp = ReportExportJob(tenant_id=t1.id, type="x", status="completed", requested_by="admin")
    run = SimulationRun(tenant_id=t1.id, name="r", simulation_type="game_math", status="draft", created_by="admin")
    session.add(exp)
    session.add(run)
    await session.commit()

    token = create_access_token(
        data={"sub": owner.id, "email": owner.email, "tenant_id": owner.tenant_id, "role": "Admin"},
        expires_delta=timedelta(days=1),
    )

    # As tenant2 (via header), should not see tenant1 data
    res = await client.get(
        "/api/v1/reports/exports",
        headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": t2.id},
    )
    assert res.status_code == 200
    assert res.json() == []

    res2 = await client.get(
        "/api/v1/simulation-lab/runs",
        headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": t2.id},
    )
    assert res2.status_code == 200
    assert res2.json() == []
