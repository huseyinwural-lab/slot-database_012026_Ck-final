import pytest


@pytest.mark.asyncio
async def test_players_export_csv_200_and_headers(client, admin_token):
    res = await client.get(
        "/api/v1/players/export",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    assert res.headers.get("content-type", "").startswith("text/csv")
    cd = res.headers.get("content-disposition", "")
    assert "attachment" in cd
    assert "players_" in cd
    body = res.text
    assert "id,username,email" in body.splitlines()[0]


@pytest.mark.asyncio
async def test_players_export_csv_tenant_isolation_owner_header(client, session):
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
        email="owner_players@test.com",
        full_name="Owner",
        password_hash="noop_hash",
        role="Admin",
        is_platform_owner=True,
    )
    session.add(owner)
    await session.commit()
    await session.refresh(owner)

    # player under tenant1
    p1 = Player(tenant_id=t1.id, username="u1", email="u1@test.com", password_hash="x")
    session.add(p1)
    await session.commit()

    token = create_access_token(
        data={"sub": owner.id, "email": owner.email, "tenant_id": owner.tenant_id, "role": "Admin"},
        expires_delta=timedelta(days=1),
    )

    # impersonate tenant2: should not include u1
    res = await client.get(
        "/api/v1/players/export",
        headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": t2.id},
    )
    assert res.status_code == 200
    assert "u1@test.com" not in res.text
