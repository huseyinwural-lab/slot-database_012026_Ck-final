import pytest


@pytest.mark.asyncio
async def test_player_ops_rbac_support_forbidden_for_mutations(client, session, admin_token):
    # Create a Support admin and a player under same tenant
    from app.models.sql_models import Tenant, Player, AdminUser
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

    support = AdminUser(
        email="support_rbac@test.com",
        username="support_rbac",
        full_name="Support",
        role="Support",
        tenant_role="support",
        tenant_id=tenant_id,
        password_hash="noop_hash",
        is_platform_owner=False,
        status="active",
    )
    session.add(support)

    p = Player(tenant_id=tenant_id, username="rbacplayer1", email="rbac_player1@test.com", password_hash="noop_hash")
    session.add(p)
    await session.commit()
    await session.refresh(support)
    await session.refresh(p)

    # login as support (test client uses JWT auth; easiest is to mint a token by calling login is not available here)
    # In tests we reuse admin_token auth middleware, so we validate RBAC by directly swapping role on admin record
    # (The auth dependency reads role from DB).
    
    # overwrite the admin from token to Support role
    admin = (await session.execute(select(AdminUser).where(AdminUser.email == payload["email"]))).scalars().first()
    if admin:
        admin.role = "Support"
        admin.tenant_role = "support"
        session.add(admin)
        await session.commit()

    token = admin_token
    player = p

    # Support can view bonuses list
    r = await client.get(
        f"/api/v1/players/{player.id}/bonuses",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200

    # Credit forbidden
    r = await client.post(
        f"/api/v1/players/{player.id}/credit",
        json={"amount": 10, "currency": "USD", "reason": "test"},
        headers={"Authorization": f"Bearer {token}", "X-Reason": "test"},
    )
    assert r.status_code == 403

    # Suspend forbidden
    r = await client.post(
        f"/api/v1/players/{player.id}/suspend",
        json={"reason": "test"},
        headers={"Authorization": f"Bearer {token}", "X-Reason": "test"},
    )
    assert r.status_code == 403

    # Force logout forbidden
    r = await client.post(
        f"/api/v1/players/{player.id}/force-logout",
        json={"reason": "test"},
        headers={"Authorization": f"Bearer {token}", "X-Reason": "test"},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_player_ops_rbac_ops_only_ops_actions(client, session, admin_token):
    from app.models.sql_models import AdminUser
    from sqlmodel import select
    from jose import jwt
    from config import settings

    payload = jwt.decode(admin_token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    admin = (await session.execute(select(AdminUser).where(AdminUser.email == payload["email"]))).scalars().first()
    if admin:
        admin.role = "Ops"
        admin.tenant_role = "operations"
        session.add(admin)
        await session.commit()

    # create player under same tenant
    from app.models.sql_models import Player
    p = Player(tenant_id=payload["tenant_id"], username="rbacplayer2", email="rbac_player2@test.com", password_hash="noop_hash")
    session.add(p)
    await session.commit()
    await session.refresh(p)

    token = admin_token
    tenant = None
    player = p

    # Ops can suspend
    r = await client.post(
        f"/api/v1/players/{player.id}/suspend",
        json={"reason": "test"},
        headers={"Authorization": f"Bearer {token}", "X-Reason": "test"},
    )
    assert r.status_code == 200

    # Ops can force-logout
    r = await client.post(
        f"/api/v1/players/{player.id}/force-logout",
        json={"reason": "test"},
        headers={"Authorization": f"Bearer {token}", "X-Reason": "test"},
    )
    assert r.status_code == 200

    # Ops cannot credit
    r = await client.post(
        f"/api/v1/players/{player.id}/credit",
        json={"amount": 10, "currency": "USD", "reason": "test"},
        headers={"Authorization": f"Bearer {token}", "X-Reason": "test"},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_player_ops_rbac_admin_all_allowed(client, session, admin_token):
    from app.models.sql_models import AdminUser
    from sqlmodel import select
    from jose import jwt
    from config import settings

    payload = jwt.decode(admin_token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    admin = (await session.execute(select(AdminUser).where(AdminUser.email == payload["email"]))).scalars().first()
    if admin:
        admin.role = "Admin"
        admin.tenant_role = "tenant_admin"
        session.add(admin)
        await session.commit()

    from app.models.sql_models import Player
    p = Player(tenant_id=payload["tenant_id"], username="rbacplayer3", email="rbac_player3@test.com", password_hash="noop_hash")
    session.add(p)
    await session.commit()
    await session.refresh(p)

    token = admin_token
    tenant = None
    player = p

    r = await client.post(
        f"/api/v1/players/{player.id}/credit",
        json={"amount": 10, "currency": "USD", "reason": "test"},
        headers={"Authorization": f"Bearer {token}", "X-Reason": "test"},
    )
    assert r.status_code == 200

    r = await client.post(
        f"/api/v1/players/{player.id}/force-logout",
        json={"reason": "test"},
        headers={"Authorization": f"Bearer {token}", "X-Reason": "test"},
    )
    assert r.status_code == 200
