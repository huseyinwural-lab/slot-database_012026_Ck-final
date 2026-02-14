import os
import sys

import pytest
from sqlmodel import select

sys.path.append(os.path.abspath("/app/backend"))

from server import app  # noqa: F401
from tests.conftest import _create_tenant, _create_player
from app.models.sql_models import Transaction, Player, PayoutAttempt, AdminUser
from app.repositories.ledger_repo import LedgerTransaction
from app.utils.auth import create_access_token


async def _seed_admin_player_and_balance(async_session_factory):
    """Create tenant + player with balance and an admin token for recheck tests."""

    async with async_session_factory() as session:
        tenant = await _create_tenant(session)
        player = await _create_player(
            session,
            tenant.id,
            kyc_status="verified",
            balance_available=100.0,
        )

        # Get-or-create admin to avoid unique email violations across tests
        existing = (
            await session.execute(
                select(AdminUser).where(AdminUser.email == "payout-recheck-admin@test.local")
            )
        ).scalars().first()
        if existing:
            admin = existing
        else:
            admin = AdminUser(
                tenant_id=tenant.id,
                username="payout-recheck-admin",
                email="payout-recheck-admin@test.local",
                full_name="Payout Recheck Admin",
                password_hash="noop",
                role="Admin",
                is_platform_owner=False,
            )
            session.add(admin)
            await session.commit()
            await session.refresh(admin)

        from datetime import timedelta

        admin_token = create_access_token({"email": admin.email}, timedelta(minutes=60))

        return tenant, player, admin, admin_token


async def _force_state_payout_pending(async_session_factory, tx_id: str):
    from app.services.transaction_state_machine import transition_transaction

    async with async_session_factory() as session:
        tx = await session.get(Transaction, tx_id)
        transition_transaction(tx, "payout_pending")
        session.add(tx)
        await session.commit()
        await session.refresh(tx)
        return tx


@pytest.mark.usefixtures("client")
@pytest.mark.asyncio
async def test_recheck_paid_finalizes_pending_and_writes_single_withdraw_paid_ledger(
    client, async_session_factory
):
    tenant, player, admin, admin_token = await _seed_admin_player_and_balance(async_session_factory)

    from tests.conftest import _make_player_token

    player_token = _make_player_token(player.id, tenant.id)

    # Player initiates withdrawal
    headers_player = {"Authorization": f"Bearer {player_token}", "Idempotency-Key": "recheck-paid-wd"}
    r_wd = await client.post(
        "/api/v1/player/wallet/withdraw",
        json={"amount": 30, "method": "bank", "address": "addr"},
        headers=headers_player,
    )
    assert r_wd.status_code in (200, 201)
    tx_id = r_wd.json()["transaction"]["id"]

    # Admin approves
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    r_app = await client.post(
        f"/api/v1/finance/withdrawals/{tx_id}/review",
        json={"action": "approve", "reason": "test:legacy_fix"},
        headers=headers_admin,
    )
    assert r_app.status_code == 200

    # Force state to payout_pending (simulate stuck payout)
    await _force_state_payout_pending(async_session_factory, tx_id)

    # Snapshot balances before recheck
    async with async_session_factory() as session:
        db_player_before = await session.get(Player, player.id)
        avail_before = db_player_before.balance_real_available
        held_before = db_player_before.balance_real_held

    # Recheck with paid outcome
    recheck_headers = {
        "Authorization": f"Bearer {admin_token}",
        "Idempotency-Key": "recheck-paid-1",
        "X-Mock-Outcome": "paid",
    }
    r_recheck = await client.post(
        f"/api/v1/finance/withdrawals/{tx_id}/recheck",
        headers=recheck_headers,
    )
    assert r_recheck.status_code == 200

    async with async_session_factory() as session:
        tx = await session.get(Transaction, tx_id)
        db_player_after = await session.get(Player, player.id)

        assert tx.state == "paid"
        assert db_player_after.balance_real_available == pytest.approx(avail_before)
        assert db_player_after.balance_real_held == pytest.approx(held_before - tx.amount)

        # Exactly one withdraw_paid ledger event
        stmt_ledger = select(LedgerTransaction).where(
            LedgerTransaction.tx_id == tx_id,
            LedgerTransaction.status == "withdraw_paid",
        )
        events = (await session.execute(stmt_ledger)).scalars().all()
        assert len(events) == 1


@pytest.mark.usefixtures("client")
@pytest.mark.asyncio
async def test_recheck_failed_transitions_to_payout_failed_and_writes_no_ledger(
    client, async_session_factory
):
    tenant, player, admin, admin_token = await _seed_admin_player_and_balance(async_session_factory)

    from tests.conftest import _make_player_token

    player_token = _make_player_token(player.id, tenant.id)

    headers_player = {"Authorization": f"Bearer {player_token}", "Idempotency-Key": "recheck-fail-wd"}
    r_wd = await client.post(
        "/api/v1/player/wallet/withdraw",
        json={"amount": 20, "method": "bank", "address": "addr"},
        headers=headers_player,
    )
    assert r_wd.status_code in (200, 201)
    tx_id = r_wd.json()["transaction"]["id"]

    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    r_app = await client.post(
        f"/api/v1/finance/withdrawals/{tx_id}/review",
        json={"action": "approve", "reason": "test:legacy_fix"},
        headers=headers_admin,
    )
    assert r_app.status_code == 200

    await _force_state_payout_pending(async_session_factory, tx_id)

    async with async_session_factory() as session:
        db_player_before = await session.get(Player, player.id)
        avail_before = db_player_before.balance_real_available
        held_before = db_player_before.balance_real_held

    recheck_headers = {
        "Authorization": f"Bearer {admin_token}",
        "Idempotency-Key": "recheck-fail-1",
        "X-Mock-Outcome": "failed",
    }
    r_recheck = await client.post(
        f"/api/v1/finance/withdrawals/{tx_id}/recheck",
        headers=recheck_headers,
    )
    assert r_recheck.status_code == 200

    async with async_session_factory() as session:
        tx = await session.get(Transaction, tx_id)
        db_player_after = await session.get(Player, player.id)

        assert tx.state == "payout_failed"
        assert db_player_after.balance_real_available == pytest.approx(avail_before)
        assert db_player_after.balance_real_held == pytest.approx(held_before)

        stmt_ledger = select(LedgerTransaction).where(
            LedgerTransaction.tx_id == tx_id,
            LedgerTransaction.status == "withdraw_paid",
        )
        events = (await session.execute(stmt_ledger)).scalars().all()
        assert len(events) == 0


@pytest.mark.usefixtures("client")
@pytest.mark.asyncio
async def test_recheck_pending_outcome_keeps_payout_pending_and_writes_no_ledger(
    client, async_session_factory
):
    tenant, player, admin, admin_token = await _seed_admin_player_and_balance(async_session_factory)

    from tests.conftest import _make_player_token

    player_token = _make_player_token(player.id, tenant.id)

    headers_player = {"Authorization": f"Bearer {player_token}", "Idempotency-Key": "recheck-pending-wd"}
    r_wd = await client.post(
        "/api/v1/player/wallet/withdraw",
        json={"amount": 15, "method": "bank", "address": "addr"},
        headers=headers_player,
    )
    assert r_wd.status_code in (200, 201)
    tx_id = r_wd.json()["transaction"]["id"]

    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    r_app = await client.post(
        f"/api/v1/finance/withdrawals/{tx_id}/review",
        json={"action": "approve", "reason": "test:legacy_fix"},
        headers=headers_admin,
    )
    assert r_app.status_code == 200

    await _force_state_payout_pending(async_session_factory, tx_id)

    async with async_session_factory() as session:
        db_player_before = await session.get(Player, player.id)
        avail_before = db_player_before.balance_real_available
        held_before = db_player_before.balance_real_held

    recheck_headers = {
        "Authorization": f"Bearer {admin_token}",
        "Idempotency-Key": "recheck-pending-1",
        "X-Mock-Outcome": "pending",
    }
    r_recheck = await client.post(
        f"/api/v1/finance/withdrawals/{tx_id}/recheck",
        headers=recheck_headers,
    )
    assert r_recheck.status_code == 200

    async with async_session_factory() as session:
        tx = await session.get(Transaction, tx_id)
        db_player_after = await session.get(Player, player.id)

        assert tx.state == "payout_pending"
        assert db_player_after.balance_real_available == pytest.approx(avail_before)
        assert db_player_after.balance_real_held == pytest.approx(held_before)

        stmt_ledger = select(LedgerTransaction).where(
            LedgerTransaction.tx_id == tx_id,
            LedgerTransaction.status == "withdraw_paid",
        )
        events = (await session.execute(stmt_ledger)).scalars().all()
        assert len(events) == 0


@pytest.mark.usefixtures("client")
@pytest.mark.asyncio
async def test_recheck_replay_same_idempotency_key_is_noop(
    client, async_session_factory
):
    tenant, player, admin, admin_token = await _seed_admin_player_and_balance(async_session_factory)

    from tests.conftest import _make_player_token

    player_token = _make_player_token(player.id, tenant.id)

    headers_player = {"Authorization": f"Bearer {player_token}", "Idempotency-Key": "recheck-replay-wd"}
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
        json={"action": "approve", "reason": "test:legacy_fix"},
        headers=headers_admin,
    )
    assert r_app.status_code == 200

    await _force_state_payout_pending(async_session_factory, tx_id)

    recheck_headers = {
        "Authorization": f"Bearer {admin_token}",
        "Idempotency-Key": "recheck-replay-1",
        "X-Mock-Outcome": "paid",
    }

    # First recheck call
    r_recheck_1 = await client.post(
        f"/api/v1/finance/withdrawals/{tx_id}/recheck",
        headers=recheck_headers,
    )
    assert r_recheck_1.status_code == 200

    # Replay same idempotency key multiple times
    for _ in range(3):
        r_recheck_n = await client.post(
            f"/api/v1/finance/withdrawals/{tx_id}/recheck",
            headers=recheck_headers,
        )
        assert r_recheck_n.status_code == 200

    async with async_session_factory() as session:
        tx = await session.get(Transaction, tx_id)
        assert tx.state == "paid"

        stmt_ledger = select(LedgerTransaction).where(
            LedgerTransaction.tx_id == tx_id,
            LedgerTransaction.status == "withdraw_paid",
        )
        ledger_events = (await session.execute(stmt_ledger)).scalars().all()
        assert len(ledger_events) == 1

        stmt_pa = select(PayoutAttempt).where(
            PayoutAttempt.withdraw_tx_id == tx_id,
            PayoutAttempt.idempotency_key == "recheck-replay-1",
        )
        attempts = (await session.execute(stmt_pa)).scalars().all()
        assert len(attempts) == 1
