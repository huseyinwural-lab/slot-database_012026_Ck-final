import uuid

import pytest
import pytest_asyncio
from sqlmodel import select

from app.models.sql_models import AdminUser, Player, Tenant
from app.utils.auth import create_access_token


OWNER_EMAIL = "owner@casino.test"
TENANT_ADMIN_EMAIL = "tenant.admin@demo-renter.test"


def _make_admin_token(*, admin_id: str, tenant_id: str, email: str) -> str:
    from datetime import timedelta

    return create_access_token(
        data={"sub": admin_id, "email": email, "tenant_id": tenant_id, "role": "Admin"},
        expires_delta=timedelta(days=1),
    )


@pytest_asyncio.fixture(scope="function")
async def seeded(async_session_factory):
    """Seed two tenants + owner + tenant-admin + one player.

    This test suite is intentionally *in-process* (no external server, no password login)
    to be deterministic and CI-friendly.
    """

    async with async_session_factory() as session:
        # Tenants must match IDs used in tenant-context header logic.
        # Tenants must match IDs used in tenant-context header logic.
        for tenant_id, name, ttype in (
            ("default_casino", "Default Casino", "owner"),
            ("demo_renter", "Demo Renter", "renter"),
        ):
            existing = await session.get(Tenant, tenant_id)
            if not existing:
                session.add(Tenant(id=tenant_id, name=name, type=ttype, features={}))

        # Owner (platform) admin
        res = await session.execute(select(AdminUser).where(AdminUser.email == OWNER_EMAIL))
        owner = res.scalars().first()
        if not owner:
            owner = AdminUser(
                tenant_id="default_casino",
                username="owner",
                email=OWNER_EMAIL,
                full_name="Owner",
                password_hash="noop_hash",
                role="Admin",
                tenant_role="tenant_admin",
                is_platform_owner=True,
                status="active",
                is_active=True,
            )
            session.add(owner)

        # Tenant admin (non-owner)
        res = await session.execute(select(AdminUser).where(AdminUser.email == TENANT_ADMIN_EMAIL))
        tenant_admin = res.scalars().first()
        if not tenant_admin:
            tenant_admin = AdminUser(
                tenant_id="demo_renter",
                username="tenant_admin",
                email=TENANT_ADMIN_EMAIL,
                full_name="Tenant Admin",
                password_hash="noop_hash",
                role="Admin",
                tenant_role="tenant_admin",
                is_platform_owner=False,
                status="active",
                is_active=True,
            )
            session.add(tenant_admin)

        # Player in default tenant
        res = await session.execute(select(Player).where(Player.email == "isolation_test_player@casino.test"))
        player = res.scalars().first()
        if not player:
            player = Player(
                id=str(uuid.uuid4()),
                tenant_id="default_casino",
                username="iso_player",
                email="isolation_test_player@casino.test",
                password_hash="noop_hash",
            )
            session.add(player)

        await session.commit()
        await session.refresh(owner)
        await session.refresh(tenant_admin)
        await session.refresh(player)

        return {
            "owner_token": _make_admin_token(admin_id=owner.id, tenant_id=owner.tenant_id, email=owner.email),
            "tenant_token": _make_admin_token(
                admin_id=tenant_admin.id, tenant_id=tenant_admin.tenant_id, email=tenant_admin.email
            ),
            "player_id": player.id,
        }


@pytest.mark.asyncio
async def test_tenant_admin_header_forbidden_403(client, seeded):
    r = await client.get(
        "/api/v1/api-keys/",
        headers={
            "Authorization": f"Bearer {seeded['tenant_token']}",
            "X-Tenant-ID": "default_casino",
        },
    )

    assert r.status_code == 403, r.text
    body = r.json()
    assert body.get("error_code") == "TENANT_HEADER_FORBIDDEN"


@pytest.mark.asyncio
async def test_owner_invalid_header_400(client, seeded):
    r = await client.get(
        "/api/v1/api-keys/",
        headers={
            "Authorization": f"Bearer {seeded['owner_token']}",
            "X-Tenant-ID": "__does_not_exist__",
        },
    )

    assert r.status_code == 400, r.text
    body = r.json()
    assert body.get("error_code") == "INVALID_TENANT_HEADER"


@pytest.mark.asyncio
async def test_owner_headerless_default_scope_200(client, seeded):
    r = await client.get(
        "/api/v1/api-keys/",
        headers={"Authorization": f"Bearer {seeded['owner_token']}"},
    )

    assert r.status_code == 200, r.text


@pytest.mark.asyncio
async def test_cross_tenant_detail_access_404(client, seeded):
    # Wrong tenant token trying to read player from another tenant must look like not found (404).
    r = await client.get(
        f"/api/v1/players/{seeded['player_id']}",
        headers={"Authorization": f"Bearer {seeded['tenant_token']}"},
    )

    assert r.status_code == 404, r.text


@pytest.mark.asyncio
async def test_owner_impersonation_works_for_other_tenant_200(client, seeded):
    r = await client.get(
        "/api/v1/tenants/capabilities",
        headers={"Authorization": f"Bearer {seeded['owner_token']}", "X-Tenant-ID": "demo_renter"},
    )

    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("tenant_id") == "demo_renter"



@pytest.mark.asyncio
async def test_list_wrong_tenant_returns_empty_200(client, seeded):
    # List endpoints must not leak cross-tenant data.
    r = await client.get(
        "/api/v1/players?page=1&page_size=10",
        headers={"Authorization": f"Bearer {seeded['tenant_token']}"},
    )

    assert r.status_code == 200, r.text
    body = r.json()
    items = body.get("items") or []
    assert items == [], "Expected empty list for wrong-tenant list query"


@pytest.mark.asyncio
async def test_same_tenant_insufficient_role_403(client, seeded):
    # Role boundary (not tenant boundary): same tenant but non-owner calling owner-only endpoint -> 403.
    payload = {
        "email": "new.tenant.admin@demo-renter.test",
        "tenant_id": "demo_renter",
        "password": "TenantAdmin123!",
        "full_name": "Tenant Admin",
    }

    r = await client.post(
        "/api/v1/admin/create-tenant-admin",
        json=payload,
        headers={"Authorization": f"Bearer {seeded['tenant_token']}"},
    )

    assert r.status_code == 403, r.text
