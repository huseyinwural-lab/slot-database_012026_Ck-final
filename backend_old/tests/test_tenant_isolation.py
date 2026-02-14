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


        # Transaction in default tenant to validate list filtering does not leak
        from app.models.sql_models import Transaction
        from datetime import datetime

        existing_tx = (
            await session.execute(select(Transaction).where(Transaction.tenant_id == "default_casino"))
        ).scalars().first()
        if not existing_tx:
            session.add(
                Transaction(
                    tenant_id="default_casino",
                    player_id=player.id,
                    type="deposit",
                    amount=10.0,
                    currency="USD",
                    status="completed",
                    state="completed",
                    balance_after=10.0,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
            )
            await session.commit()

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



@pytest.mark.asyncio
async def test_withdrawals_list_wrong_tenant_empty_all_pages(client, seeded):
    # Critical: finance list endpoints must not leak across tenants.
    for url in (
        "/api/v1/finance/withdrawals?limit=50&offset=0",
        "/api/v1/finance/withdrawals?limit=50&offset=50",
    ):
        r = await client.get(
            url,
            headers={"Authorization": f"Bearer {seeded['tenant_token']}"},
        )

        assert r.status_code == 200, r.text
        body = r.json()
        items = body.get("items") or []
        assert items == [], f"Expected empty items for wrong tenant. url={url}"

        meta = body.get("meta") or {}
        if "total" in meta and meta.get("total") is not None:
            assert meta.get("total") == 0, f"Expected meta.total==0 for wrong tenant. url={url}"



@pytest.mark.asyncio
async def test_player_update_wrong_tenant_404(client, seeded):
    r = await client.put(
        f"/api/v1/players/{seeded['player_id']}",
        json={"username": "should_not_update"},
        headers={"Authorization": f"Bearer {seeded['tenant_token']}"},
    )
    assert r.status_code == 404, r.text


@pytest.mark.asyncio
async def test_player_disable_wrong_tenant_404(client, seeded):
    r = await client.delete(
        f"/api/v1/players/{seeded['player_id']}",
        headers={"Authorization": f"Bearer {seeded['tenant_token']}"},
    )
    assert r.status_code == 404, r.text


@pytest.mark.asyncio
async def test_player_disable_same_tenant_200_and_status_disabled(client, seeded):
    # Owner is in default_casino tenant, where seeded player exists.
    r = await client.delete(
        f"/api/v1/players/{seeded['player_id']}",
        headers={"Authorization": f"Bearer {seeded['owner_token']}"},
    )
    assert r.status_code == 200, r.text

    r2 = await client.get(
        f"/api/v1/players/{seeded['player_id']}",
        headers={"Authorization": f"Bearer {seeded['owner_token']}"},
    )
    assert r2.status_code == 200, r2.text
    assert r2.json().get("status") == "disabled"



@pytest.mark.asyncio
async def test_disabled_player_hidden_by_default_and_visible_with_include(client, seeded):
    # Disable the seeded player first
    r_del = await client.delete(
        f"/api/v1/players/{seeded['player_id']}",
        headers={"Authorization": f"Bearer {seeded['owner_token']}"},
    )
    assert r_del.status_code == 200, r_del.text

    # Default list must hide disabled
    r_list = await client.get(
        "/api/v1/players?page=1&page_size=50",
        headers={"Authorization": f"Bearer {seeded['owner_token']}"},
    )
    assert r_list.status_code == 200, r_list.text
    ids = [p["id"] for p in (r_list.json().get("items") or [])]
    assert seeded["player_id"] not in ids

    # include_disabled=1 must include disabled
    r_list2 = await client.get(
        "/api/v1/players?page=1&page_size=50&include_disabled=1",
        headers={"Authorization": f"Bearer {seeded['owner_token']}"},
    )
    assert r_list2.status_code == 200, r_list2.text
    items2 = r_list2.json().get("items") or []
    found = [p for p in items2 if p["id"] == seeded["player_id"]]
    assert found and found[0].get("status") == "disabled"

    # status=disabled should include; status wins over include_disabled
    r_list3 = await client.get(
        "/api/v1/players?page=1&page_size=50&status=disabled",
        headers={"Authorization": f"Bearer {seeded['owner_token']}"},
    )
    assert r_list3.status_code == 200, r_list3.text
    items3 = r_list3.json().get("items") or []
    assert any(p["id"] == seeded["player_id"] for p in items3)

    # status=active + include_disabled=1 -> should NOT include (status wins)
    r_list4 = await client.get(
        "/api/v1/players?page=1&page_size=50&status=active&include_disabled=1",
        headers={"Authorization": f"Bearer {seeded['owner_token']}"},
    )
    assert r_list4.status_code == 200, r_list4.text
    items4 = r_list4.json().get("items") or []
    assert not any(p["id"] == seeded["player_id"] for p in items4)
