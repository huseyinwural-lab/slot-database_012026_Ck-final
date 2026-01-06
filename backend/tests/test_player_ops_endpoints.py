import pytest


@pytest.mark.asyncio
async def test_player_ops_credit_debit_bonus_suspend_force_logout(client, session, admin_token):
    # Seed a player under the SAME tenant as admin_token
    from app.models.sql_models import Tenant, Player
    from sqlmodel import select
    from jose import jwt
    from config import settings

    payload = jwt.decode(admin_token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    tenant_id = payload["tenant_id"]

    # ensure tenant exists in DB
    t = (await session.execute(select(Tenant).where(Tenant.id == tenant_id))).scalars().first()
    if not t:
        t = Tenant(id=tenant_id, name="Test Casino", type="owner", features={})
        session.add(t)
        await session.commit()

    p = Player(tenant_id=tenant_id, username="opsplayer", email="ops_player@test.com", password_hash="noop_hash")
    session.add(p)
    await session.commit()
    await session.refresh(p)

    pid = p.id

    # credit
    r = await client.post(
        f"/api/v1/players/{pid}/credit",
        json={"amount": 10, "currency": "USD", "reason": "manual credit"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 200

    # debit insufficient
    r2 = await client.post(
        f"/api/v1/players/{pid}/debit",
        json={"amount": 999999, "currency": "USD", "reason": "manual debit"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r2.status_code == 409

    # suspend
    r3 = await client.post(
        f"/api/v1/players/{pid}/suspend",
        json={"reason": "fraud"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r3.status_code == 200
    assert r3.json()["status"] == "suspended"

    # unsuspend
    r4 = await client.post(
        f"/api/v1/players/{pid}/unsuspend",
        json={"reason": "resolved"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r4.status_code == 200
    assert r4.json()["status"] == "active"

    # bonus grant (cash)
    r5 = await client.post(
        f"/api/v1/players/{pid}/bonuses",
        json={"bonus_type": "cash", "amount": 5, "reason": "promo"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r5.status_code == 200
    grant_id = r5.json()["id"]

    # list bonuses
    r6 = await client.get(
        f"/api/v1/players/{pid}/bonuses",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r6.status_code == 200
    assert any(b["id"] == grant_id for b in r6.json())

    # force logout
    r7 = await client.post(
        f"/api/v1/players/{pid}/force-logout",
        json={"reason": "ops"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r7.status_code == 200


@pytest.mark.asyncio
async def test_player_ops_requires_reason(client, admin_token):
    # Seed a player under the SAME tenant as admin_token
    from app.models.sql_models import Tenant, Player
    from sqlmodel import select
    from jose import jwt
    from config import settings

    payload = jwt.decode(admin_token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    tenant_id = payload["tenant_id"]

    t = (await session.execute(select(Tenant).where(Tenant.id == tenant_id))).scalars().first()
    if not t:
        t = Tenant(id=tenant_id, name="Test Casino", type="owner", features={})
        session.add(t)
        await session.commit()

    p = Player(tenant_id=tenant_id, username="opsplayer2", email="ops_player2@test.com", password_hash="noop_hash")
    session.add(p)
    await session.commit()
    await session.refresh(p)

    pid = p.id

    r = await client.post(
        f"/api/v1/players/{pid}/credit",
        json={"amount": 10, "currency": "USD"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 400
