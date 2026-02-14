import pytest


@pytest.mark.asyncio
async def test_settings_brands_returns_array_and_matches_ui_shape(client, admin_token):
    res = await client.get(
        "/api/v1/settings/brands",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    if data:
        b = data[0]
        assert "id" in b
        assert "brand_name" in b
        assert "default_currency" in b
        assert "default_language" in b
        assert "created_at" in b


@pytest.mark.asyncio
async def test_settings_brands_create_owner_only(client, session):
    from app.models.sql_models import Tenant, AdminUser
    from app.utils.auth import create_access_token
    from datetime import timedelta

    t = Tenant(name="T1", type="renter", features={})
    session.add(t)
    await session.commit()
    await session.refresh(t)

    admin = AdminUser(
        tenant_id=t.id,
        username="a",
        email="a@t.com",
        full_name="A",
        password_hash="noop_hash",
        role="Admin",
        is_platform_owner=False,
    )
    session.add(admin)
    await session.commit()
    await session.refresh(admin)

    token = create_access_token(
        data={"sub": admin.id, "email": admin.email, "tenant_id": admin.tenant_id, "role": "Admin"},
        expires_delta=timedelta(days=1),
    )

    res = await client.post(
        "/api/v1/settings/brands",
        json={"brand_name": "B2", "default_currency": "USD", "default_language": "en"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403
