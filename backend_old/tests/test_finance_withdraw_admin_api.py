import os
import sys

import pytest
from sqlmodel import select

sys.path.append(os.path.abspath("/app/backend"))

from tests.conftest import _create_tenant, _create_player, _make_player_token
from app.models.sql_models import Transaction, Player, AdminUser
from config import settings
from app.utils.auth import create_access_token

# Ensure withdraw admin tests run with legacy funds check (enforce OFF) while
# still writing shadow ledger for telemetry.
settings.ledger_shadow_write = True
settings.ledger_enforce_balance = False
settings.ledger_balance_mismatch_log = False


async def _get_or_create_admin(session, tenant_id: str, email: str) -> AdminUser:
    existing = (
        await session.execute(
            select(AdminUser).where(AdminUser.email == email)
        )
    ).scalars().first()
    if existing:
        return existing

    admin = AdminUser(
        tenant_id=tenant_id,
        username=email.split("@")[0],
        email=email,
        full_name="Test Admin",
        password_hash="noop",
        role="Admin",
        is_platform_owner=False,
    )
    session.add(admin)
    await session.commit()
    await session.refresh(admin)
    return admin


async def _seed_admin_and_player(async_session_factory):
    # For admin withdraw tests we rely on legacy Player-based funds checks,
    # not ledger-enforced balance. Ensure enforce is OFF here so that previous
    # tests (e.g. LEDGER-02B) don't leak their settings into this suite.
    settings.ledger_enforce_balance = False
    settings.ledger_balance_mismatch_log = False
    settings.ledger_shadow_write = True

    async with async_session_factory() as session:
        tenant = await _create_tenant(session)
        player = await _create_player(session, tenant.id, kyc_status="verified", balance_available=100)

        # Create admin bound to same tenant (idempotent)
        import uuid

        admin_email = f"admin+{uuid.uuid4().hex}@test.local"
        admin = await _get_or_create_admin(session, tenant_id=tenant.id, email=admin_email)

        player_token = _make_player_token(player.id, tenant.id)
        # Admin token uses email in payload per get_current_admin
        from datetime import timedelta

        admin_token = create_access_token({"email": admin.email}, timedelta(minutes=60))

        return tenant, player, admin, player_token, admin_token


@pytest.mark.usefixtures("client")
@pytest.mark.asyncio
async def test_approve_requested_withdraw_does_not_change_balance(client, async_session_factory):
    tenant, player, admin, player_token, admin_token = await _seed_admin_and_player(async_session_factory)

    # Player makes a withdrawal request
    headers_player = {"Authorization": f"Bearer {player_token}", "Idempotency-Key": "wd-admin-1"}
    r_wd = await client.post(
        "/api/v1/player/wallet/withdraw",
        json={"amount": 30, "method": "bank", "address": "addr"},
        headers=headers_player,
    )
    assert r_wd.status_code in (200, 201)

    body = r_wd.json()
    tx_id = body["transaction"]["id"]

    # Snapshot balances before admin action
    async def _load_before():
        async with async_session_factory() as session:
            db_player = await session.get(Player, player.id)
            return db_player.balance_real_available, db_player.balance_real_held

    before_available, before_held = await _load_before()

    # Admin approves
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    r_app = await client.post(
        f"/api/v1/finance/withdrawals/{tx_id}/review",
        json={"action": "approve"},
        headers=headers_admin,
    )
    assert r_app.status_code == 200

    # Verify state and balances
    async def _load_after():
        async with async_session_factory() as session:
            tx = await session.get(Transaction, tx_id)
            db_player = await session.get(Player, player.id)
            return tx, db_player

    tx, db_player = await _load_after()

    assert tx.state == "approved"
    assert db_player.balance_real_available == pytest.approx(before_available)
    assert db_player.balance_real_held == pytest.approx(before_held)


@pytest.mark.usefixtures("client")
@pytest.mark.asyncio
async def test_reject_requested_withdraw_rolls_back_hold(client, async_session_factory):
    tenant, player, admin, player_token, admin_token = await _seed_admin_and_player(async_session_factory)

    headers_player = {"Authorization": f"Bearer {player_token}", "Idempotency-Key": "wd-admin-2"}
    r_wd = await client.post(
        "/api/v1/player/wallet/withdraw",
        json={"amount": 40, "method": "bank", "address": "addr"},
        headers=headers_player,
    )
    assert r_wd.status_code in (200, 201)
    tx_id = r_wd.json()["transaction"]["id"]

    async def _load_before():
        async with async_session_factory() as session:
            db_player = await session.get(Player, player.id)
            return db_player.balance_real_available, db_player.balance_real_held

    before_available, before_held = await _load_before()

    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    r_rej = await client.post(
        f"/api/v1/finance/withdrawals/{tx_id}/review",
        json={"action": "reject", "reason": "test"},
        headers=headers_admin,
    )
    assert r_rej.status_code == 200

    async def _load_after():
        async with async_session_factory() as session:
            tx = await session.get(Transaction, tx_id)
            db_player = await session.get(Player, player.id)
            return tx, db_player

    tx, db_player = await _load_after()

    assert tx.state == "rejected"
    assert db_player.balance_real_available == pytest.approx(before_available + tx.amount)
    assert db_player.balance_real_held == pytest.approx(before_held - tx.amount)


@pytest.mark.usefixtures("client")
@pytest.mark.asyncio
async def test_mark_paid_from_approved_reduces_held(client, async_session_factory):
    tenant, player, admin, player_token, admin_token = await _seed_admin_and_player(async_session_factory)

    headers_player = {"Authorization": f"Bearer {player_token}", "Idempotency-Key": "wd-admin-3"}
    r_wd = await client.post(
        "/api/v1/player/wallet/withdraw",
        json={"amount": 25, "method": "bank", "address": "addr"},
        headers=headers_player,
    )
    assert r_wd.status_code in (200, 201)
    tx_id = r_wd.json()["transaction"]["id"]

    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    r_app = await client.post(
        f"/api/v1/finance/withdrawals/{tx_id}/review",
        json={"action": "approve"},
        headers=headers_admin,
    )
    assert r_app.status_code == 200

    async def _load_before():
        async with async_session_factory() as session:
            db_player = await session.get(Player, player.id)
            return db_player.balance_real_available, db_player.balance_real_held

    before_available, before_held = await _load_before()

    r_paid = await client.post(
        f"/api/v1/finance/withdrawals/{tx_id}/mark-paid",
        headers=headers_admin,
    )
    assert r_paid.status_code == 200

    async def _load_after_paid():
        async with async_session_factory() as session:
            tx = await session.get(Transaction, tx_id)
            db_player = await session.get(Player, player.id)
            return tx, db_player

    tx, db_player = await _load_after_paid()

    assert tx.state == "paid"
    assert db_player.balance_real_available == pytest.approx(before_available)
    assert db_player.balance_real_held == pytest.approx(before_held - tx.amount)


@pytest.mark.usefixtures("client")
@pytest.mark.asyncio
async def test_invalid_state_transitions_return_409(client, async_session_factory):
    tenant, player, admin, player_token, admin_token = await _seed_admin_and_player(async_session_factory)

    headers_player = {"Authorization": f"Bearer {player_token}", "Idempotency-Key": "wd-admin-4"}
    r_wd = await client.post(
        "/api/v1/player/wallet/withdraw",
        json={"amount": 10, "method": "bank", "address": "addr"},
        headers=headers_player,
    )
    assert r_wd.status_code in (200, 201)
    tx_id = r_wd.json()["transaction"]["id"]

    # Try mark-paid directly from requested -> should be 409
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    r_paid = await client.post(
        f"/api/v1/finance/withdrawals/{tx_id}/mark-paid",
        headers=headers_admin,
    )
    assert r_paid.status_code == 409
    assert r_paid.json().get("detail", {}).get("error_code") == "ILLEGAL_TRANSACTION_STATE_TRANSITION"

    # Approve first
    r_app = await client.post(
        f"/api/v1/finance/withdrawals/{tx_id}/review",
        json={"action": "approve"},
        headers=headers_admin,
    )
    assert r_app.status_code == 200

    # Second approve is idempotent (state already approved) and should stay 200
    r_app2 = await client.post(
        f"/api/v1/finance/withdrawals/{tx_id}/review",
        json={"action": "approve"},
        headers=headers_admin,
    )
    assert r_app2.status_code == 200


@pytest.mark.usefixtures("client")
@pytest.mark.asyncio
async def test_withdrawals_list_pagination_and_fields(client, async_session_factory):
    tenant, player, admin, player_token, admin_token = await _seed_admin_and_player(async_session_factory)

    headers_player = {"Authorization": f"Bearer {player_token}", "Idempotency-Key": "wd-admin-5"}
    # create two withdrawals
    for i in range(2):
        await client.post(
            "/api/v1/player/wallet/withdraw",
            json={"amount": 5 + i, "method": "bank", "address": "addr"},
            headers={**headers_player, "Idempotency-Key": f"wd-admin-5-{i}"},
        )

    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    r_list = await client.get(
        "/api/v1/finance/withdrawals",
        params={"state": "requested", "limit": 10, "offset": 0},
        headers=headers_admin,
    )
    assert r_list.status_code == 200
    data = r_list.json()
    assert "items" in data and "meta" in data
    assert data["meta"]["total"] >= 2

    item = data["items"][0]
    for key in [
        "tx_id",
        "player_id",
        "amount",
        "currency",
        "state",
        "status",
        "created_at",
        "reviewed_by",
        "reviewed_at",
        "balance_after",
    ]:
        assert key in item
