import uuid

import pytest
import pytest_asyncio
from sqlmodel import select

from app.models.sql_models import AdminUser, Tenant
from jose import jwt


def _token(*, admin_id: str, email: str, tenant_id: str, role: str) -> str:
    # IMPORTANT: app-side auth uses config.settings (root config.py), not backend.config.
    # Use the same settings to generate tokens deterministically.
    from config import settings
    from datetime import datetime, timezone

    payload = {
        "sub": admin_id,
        "email": email,
        "tenant_id": tenant_id,
        "role": role,
        "exp": int(datetime.utcnow().timestamp() + 3600),
    }
    now = datetime.now(timezone.utc)
    payload["iat"] = int(now.timestamp())

    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


@pytest_asyncio.fixture(scope="function")
async def seeded_admins(async_session_factory):
    async with async_session_factory() as session:
        # Tenants
        for tid, name, ttype in (
            ("default_casino", "Default Casino", "owner"),
            ("demo_renter", "Demo Renter", "renter"),
        ):
            existing = await session.get(Tenant, tid)
            if not existing:
                session.add(Tenant(id=tid, name=name, type=ttype, features={}))

        # Admin in default tenant
        admin_email = "p1bs_admin@casino.test"
        admin = (await session.execute(select(AdminUser).where(AdminUser.email == admin_email))).scalars().first()
        if not admin:
            admin = AdminUser(
                tenant_id="default_casino",
                username="p1bs_admin",
                email=admin_email,
                full_name="P1BS Admin",
                password_hash="noop",
                role="Admin",
                tenant_role="tenant_admin",
                is_platform_owner=False,
                status="active",
                is_active=True,
            )
            session.add(admin)

        # Non-admin role in default tenant
        viewer_email = "p1bs_viewer@casino.test"
        viewer = (await session.execute(select(AdminUser).where(AdminUser.email == viewer_email))).scalars().first()
        if not viewer:
            viewer = AdminUser(
                tenant_id="default_casino",
                username="p1bs_viewer",
                email=viewer_email,
                full_name="P1BS Viewer",
                password_hash="noop",
                role="Viewer",
                tenant_role="tenant_viewer",
                is_platform_owner=False,
                status="active",
                is_active=True,
            )
            session.add(viewer)

        # Admin in demo tenant
        demo_email = "p1bs_demo_admin@casino.test"
        demo_admin = (await session.execute(select(AdminUser).where(AdminUser.email == demo_email))).scalars().first()
        if not demo_admin:
            demo_admin = AdminUser(
                tenant_id="demo_renter",
                username="p1bs_demo_admin",
                email=demo_email,
                full_name="P1BS Demo Admin",
                password_hash="noop",
                role="Admin",
                tenant_role="tenant_admin",
                is_platform_owner=False,
                status="active",
                is_active=True,
            )
            session.add(demo_admin)

        await session.commit()
        await session.refresh(admin)
        await session.refresh(viewer)
        await session.refresh(demo_admin)

        return {
            "admin_token": _token(admin_id=admin.id, email=admin.email, tenant_id=admin.tenant_id, role=admin.role),
            "viewer_token": _token(
                admin_id=viewer.id, email=viewer.email, tenant_id=viewer.tenant_id, role=viewer.role
            ),
            "demo_admin_token": _token(
                admin_id=demo_admin.id,
                email=demo_admin.email,
                tenant_id=demo_admin.tenant_id,
                role=demo_admin.role,
            ),
        }


@pytest.mark.asyncio
async def test_admin_create_player_success_201(client, seeded_admins):
    username = f"p1bs_{uuid.uuid4().hex[:8]}"
    r = await client.post(
        "/api/v1/players",
        json={
            "username": username,
            "email": f"{username}@example.com",
            "password": "TempPass!123",
        },
        headers={"Authorization": f"Bearer {seeded_admins['admin_token']}"},
    )

    assert r.status_code == 201, r.text
    body = r.json()
    assert body.get("player_id"), body
    assert body.get("username") == username
    assert body.get("status") == "active"


@pytest.mark.asyncio
async def test_admin_create_player_non_admin_role_403(client, seeded_admins):
    r = await client.post(
        "/api/v1/players",
        json={"username": "p1bs_forbidden", "email": "x@example.com", "password": "TempPass!123"},
        headers={"Authorization": f"Bearer {seeded_admins['viewer_token']}"},
    )
    assert r.status_code == 403, r.text


@pytest.mark.asyncio
async def test_admin_create_player_validation_username_missing(client, seeded_admins):
    r = await client.post(
        "/api/v1/players",
        json={"email": "x@example.com", "password": "TempPass!123"},
        headers={"Authorization": f"Bearer {seeded_admins['admin_token']}"},
    )
    assert r.status_code in (400, 422)


@pytest.mark.asyncio
async def test_admin_create_player_validation_password_missing(client, seeded_admins):
    r = await client.post(
        "/api/v1/players",
        json={"username": "p1bs_nopw", "email": "x@example.com"},
        headers={"Authorization": f"Bearer {seeded_admins['admin_token']}"},
    )
    assert r.status_code in (400, 422)


@pytest.mark.asyncio
async def test_admin_create_player_uniqueness_same_tenant_409(client, seeded_admins):
    username = f"p1bs_{uuid.uuid4().hex[:8]}"
    payload = {"username": username, "email": f"{username}@example.com", "password": "TempPass!123"}

    r1 = await client.post(
        "/api/v1/players",
        json=payload,
        headers={"Authorization": f"Bearer {seeded_admins['admin_token']}"},
    )
    assert r1.status_code == 201, r1.text

    r2 = await client.post(
        "/api/v1/players",
        json=payload,
        headers={"Authorization": f"Bearer {seeded_admins['admin_token']}"},
    )
    assert r2.status_code in (409, 400), r2.text
    assert r2.status_code != 405


@pytest.mark.asyncio
async def test_admin_create_player_same_username_other_tenant_allowed(client, seeded_admins):
    username = f"p1bs_{uuid.uuid4().hex[:8]}"
    payload = {"username": username, "email": f"{username}@example.com", "password": "TempPass!123"}

    r1 = await client.post(
        "/api/v1/players",
        json=payload,
        headers={"Authorization": f"Bearer {seeded_admins['admin_token']}"},
    )
    assert r1.status_code == 201, r1.text

    # Same username in other tenant should be allowed (tenant-scoped uniqueness)
    r2 = await client.post(
        "/api/v1/players",
        json={**payload, "email": f"other_{username}@example.com"},
        headers={"Authorization": f"Bearer {seeded_admins['demo_admin_token']}"},
    )
    assert r2.status_code == 201, r2.text
    assert r2.json().get("username") == username
