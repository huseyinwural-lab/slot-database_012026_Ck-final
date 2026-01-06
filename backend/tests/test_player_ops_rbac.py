import pytest


@pytest.mark.asyncio
async def test_player_ops_rbac_support_forbidden_for_mutations(async_client, seed_tenant_player_and_admin_token):
    tenant, player, token = seed_tenant_player_and_admin_token(role="Support")

    # Support can view bonuses list
    r = await async_client.get(
        f"/api/v1/players/{player.id}/bonuses",
        headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": tenant.id},
    )
    assert r.status_code == 200

    # Credit forbidden
    r = await async_client.post(
        f"/api/v1/players/{player.id}/credit",
        json={"amount": 10, "currency": "USD", "reason": "test"},
        headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": tenant.id, "X-Reason": "test"},
    )
    assert r.status_code == 403

    # Suspend forbidden
    r = await async_client.post(
        f"/api/v1/players/{player.id}/suspend",
        json={"reason": "test"},
        headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": tenant.id, "X-Reason": "test"},
    )
    assert r.status_code == 403

    # Force logout forbidden
    r = await async_client.post(
        f"/api/v1/players/{player.id}/force-logout",
        json={"reason": "test"},
        headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": tenant.id, "X-Reason": "test"},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_player_ops_rbac_ops_only_ops_actions(async_client, seed_tenant_player_and_admin_token):
    tenant, player, token = seed_tenant_player_and_admin_token(role="Ops")

    # Ops can suspend
    r = await async_client.post(
        f"/api/v1/players/{player.id}/suspend",
        json={"reason": "test"},
        headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": tenant.id, "X-Reason": "test"},
    )
    assert r.status_code == 200

    # Ops can force-logout
    r = await async_client.post(
        f"/api/v1/players/{player.id}/force-logout",
        json={"reason": "test"},
        headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": tenant.id, "X-Reason": "test"},
    )
    assert r.status_code == 200

    # Ops cannot credit
    r = await async_client.post(
        f"/api/v1/players/{player.id}/credit",
        json={"amount": 10, "currency": "USD", "reason": "test"},
        headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": tenant.id, "X-Reason": "test"},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_player_ops_rbac_admin_all_allowed(async_client, seed_tenant_player_and_admin_token):
    tenant, player, token = seed_tenant_player_and_admin_token(role="Admin")

    r = await async_client.post(
        f"/api/v1/players/{player.id}/credit",
        json={"amount": 10, "currency": "USD", "reason": "test"},
        headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": tenant.id, "X-Reason": "test"},
    )
    assert r.status_code == 200

    r = await async_client.post(
        f"/api/v1/players/{player.id}/force-logout",
        json={"reason": "test"},
        headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": tenant.id, "X-Reason": "test"},
    )
    assert r.status_code == 200
