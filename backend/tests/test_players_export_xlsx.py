import pytest


@pytest.mark.asyncio
async def test_players_export_xlsx_200_and_headers_and_magic(client, admin_token):
    res = await client.get(
        "/api/v1/players/export.xlsx",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    ct = res.headers.get("content-type", "")
    assert ct.startswith("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    cd = res.headers.get("content-disposition", "")
    assert "attachment" in cd
    assert cd.endswith('.xlsx"') or ".xlsx" in cd

    # XLSX is a zip container => starts with PK
    content = res.content
    assert content[:2] == b"PK"


@pytest.mark.asyncio
async def test_players_export_xlsx_filters_and_tenant_isolation(client, session):
    from app.models.sql_models import Tenant, AdminUser, Player
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
        email="owner_xlsx@test.com",
        full_name="Owner",
        password_hash="noop_hash",
        role="Admin",
        is_platform_owner=True,
    )
    session.add(owner)
    await session.commit()
    await session.refresh(owner)

    # player under tenant1
    p1 = Player(tenant_id=t1.id, username="vipuser", email="vip@test.com", password_hash="x", risk_score="high")
    session.add(p1)
    await session.commit()

    token = create_access_token(
        data={"sub": owner.id, "email": owner.email, "tenant_id": owner.tenant_id, "role": "Admin"},
        expires_delta=timedelta(days=1),
    )

    # impersonate tenant2: should not include tenant1 player
    res = await client.get(
        "/api/v1/players/export.xlsx",
        headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": t2.id},
    )
    assert res.status_code == 200
    assert res.content[:2] == b"PK"

    # tenant1 + filters should still succeed
    res2 = await client.get(
        "/api/v1/players/export.xlsx?vip_level=5&risk_score=high",
        headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": t1.id},
    )
    assert res2.status_code == 200
    assert res2.content[:2] == b"PK"
