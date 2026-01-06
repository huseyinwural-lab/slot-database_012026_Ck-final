import pytest


@pytest.mark.asyncio
async def test_suspended_player_login_blocked(client, session):
    # create tenant + player
    from app.models.sql_models import Tenant, Player
    from app.utils.auth import get_password_hash

    tenant = Tenant(id="t_enforce", name="Enforce Casino", type="owner", features={})
    session.add(tenant)

    player = Player(
        tenant_id=tenant.id,
        email="suspended_player@test.com",
        username="suspended_player",
        password_hash=get_password_hash("whatever"),
        status="suspended",
    )
    session.add(player)
    await session.commit()

    # login should be blocked
    r = await client.post(
        "/api/v1/auth/player/login",
        json={"email": player.email, "password": "whatever", "tenant_id": tenant.id},
    )
    assert r.status_code == 403
    assert r.json().get("detail", {}).get("error_code") == "PLAYER_SUSPENDED"


@pytest.mark.asyncio
async def test_force_logout_revokes_old_token(client, session):
    """Flow:
    - Create player (active)
    - Login -> token1
    - Call a protected player endpoint -> 200
    - Admin triggers force-logout -> revoked_at
    - token1 now returns 401 TOKEN_REVOKED
    - New login -> token2 works
    """

    from datetime import datetime, timezone, timedelta
    from app.models.sql_models import Tenant, Player, AdminUser
    from app.utils.auth import get_password_hash

    tenant = Tenant(id="t_rev", name="Rev Casino", type="owner", features={})
    session.add(tenant)

    # Create player
    player_password = "Password123!"
    player = Player(
        tenant_id=tenant.id,
        email="rev_player@test.com",
        username="rev_player",
        password_hash=get_password_hash(player_password),
        status="active",
    )
    session.add(player)

    # Create admin for force-logout
    admin = AdminUser(
        email="rev_admin@test.com",
        username="rev_admin",
        full_name="Rev Admin",
        role="Admin",
        tenant_role="tenant_admin",
        tenant_id=tenant.id,
        password_hash=get_password_hash("Admin123!"),
        is_platform_owner=False,
        status="active",
    )
    session.add(admin)
    await session.commit()
    await session.refresh(player)
    await session.refresh(admin)

    # Login player token1
    r1 = await client.post(
        "/api/v1/auth/player/login",
        json={"email": player.email, "password": player_password, "tenant_id": tenant.id},
    )
    assert r1.status_code == 200
    token1 = r1.json()["access_token"]

    # Call a protected player endpoint (use /api/v1/players/me if exists; fallback to payouts list)
    # In this codebase, payouts endpoints use get_current_player
    r_ok = await client.get(
        "/api/v1/player/wallet/balance",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert r_ok.status_code == 200

    # Admin token
    from app.utils.auth import create_access_token

    admin_token = create_access_token(
        data={"email": admin.email},
        expires_delta=timedelta(days=1),
    )

    # Force logout
    r_fl = await client.post(
        f"/api/v1/players/{player.id}/force-logout",
        json={"reason": "test"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r_fl.status_code == 200

    # Old token should now be revoked
    r_rev = await client.get(
        "/api/v1/player/wallet/balance",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert r_rev.status_code == 401
    assert r_rev.json().get("detail", {}).get("error_code") == "TOKEN_REVOKED"

    # New login token2 should work
    r2 = await client.post(
        "/api/v1/auth/player/login",
        json={"email": player.email, "password": player_password, "tenant_id": tenant.id},
    )
    assert r2.status_code == 200
    token2 = r2.json()["access_token"]

    r_ok2 = await client.get(
        "/api/v1/payouts/methods",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert r_ok2.status_code in {200, 404}


@pytest.mark.asyncio
async def test_suspend_revokes_old_token(client, session):
    from datetime import timedelta
    from app.models.sql_models import Tenant, Player, AdminUser
    from app.utils.auth import get_password_hash, create_access_token

    tenant = Tenant(id="t_srev", name="SuspendRev Casino", type="owner", features={})
    session.add(tenant)

    player_password = "Password123!"
    player = Player(
        tenant_id=tenant.id,
        email="srev_player@test.com",
        username="srev_player",
        password_hash=get_password_hash(player_password),
        status="active",
    )
    session.add(player)

    admin = AdminUser(
        email="srev_admin@test.com",
        username="srev_admin",
        full_name="Suspend Admin",
        role="Ops",
        tenant_role="operations",
        tenant_id=tenant.id,
        password_hash=get_password_hash("Admin123!"),
        is_platform_owner=False,
        status="active",
    )
    session.add(admin)
    await session.commit()
    await session.refresh(player)
    await session.refresh(admin)

    # Login token1
    r1 = await client.post(
        "/api/v1/auth/player/login",
        json={"email": player.email, "password": player_password, "tenant_id": tenant.id},
    )
    assert r1.status_code == 200
    token1 = r1.json()["access_token"]

    # Suspend via ops
    admin_token = create_access_token(
        data={"email": admin.email},
        expires_delta=timedelta(days=1),
    )

    r_s = await client.post(
        f"/api/v1/players/{player.id}/suspend",
        json={"reason": "test"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r_s.status_code == 200

    # Old token should now be revoked
    r_rev = await client.get(
        "/api/v1/player/wallet/balance",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert r_rev.status_code == 401
    assert r_rev.json().get("detail", {}).get("error_code") == "TOKEN_REVOKED"
