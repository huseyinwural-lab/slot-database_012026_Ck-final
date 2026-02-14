import pytest


@pytest.mark.asyncio
async def test_api_keys_toggle_patch(client, admin_token):
    # create key
    create = await client.post(
        "/api/v1/api-keys/",
        json={"name": "Backoffice", "scopes": []},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create.status_code == 200
    key_id = create.json()["key"]["id"]

    # list
    res = await client.get(
        "/api/v1/api-keys/",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    assert any(k["id"] == key_id and k["active"] is True for k in res.json())

    # disable
    patch = await client.patch(
        f"/api/v1/api-keys/{key_id}",
        json={"active": False},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert patch.status_code == 200
    assert patch.json()["id"] == key_id
    assert patch.json()["active"] is False

    # persistence
    res2 = await client.get(
        "/api/v1/api-keys/",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res2.status_code == 200
    assert any(k["id"] == key_id and k["active"] is False for k in res2.json())


@pytest.mark.asyncio
async def test_api_keys_toggle_tenant_isolation_returns_404(client, session):
    # setup tenants + owner
    from app.models.sql_models import Tenant, AdminUser, APIKey
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
        email="owner2@test.com",
        full_name="Owner",
        password_hash="noop_hash",
        role="Admin",
        is_platform_owner=True,
    )
    session.add(owner)
    await session.commit()
    await session.refresh(owner)

    key = APIKey(tenant_id=t1.id, name="Key", key_hash="hash", scopes="", status="active")
    session.add(key)
    await session.commit()
    await session.refresh(key)

    token = create_access_token(
        data={"sub": owner.id, "email": owner.email, "tenant_id": owner.tenant_id, "role": "Admin"},
        expires_delta=timedelta(days=1),
    )

    # act as tenant2 via header; key belongs to tenant1
    patch = await client.patch(
        f"/api/v1/api-keys/{key.id}",
        json={"active": False},
        headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": t2.id},
    )
    assert patch.status_code == 404


@pytest.mark.asyncio
async def test_api_keys_toggle_invalid_body_422(client, admin_token):
    # create key
    create = await client.post(
        "/api/v1/api-keys/",
        json={"name": "Backoffice", "scopes": []},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    key_id = create.json()["key"]["id"]

    # invalid body
    patch = await client.patch(
        f"/api/v1/api-keys/{key_id}",
        json={"active": "nope"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert patch.status_code == 422
