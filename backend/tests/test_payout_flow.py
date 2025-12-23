import os
import sys

import pytest
from sqlmodel import select

sys.path.append(os.path.abspath("/app/backend"))

from server import app
from tests.conftest import _create_tenant, _create_player
from app.models.sql_models import Transaction, Player
from app.repositories.ledger_repo import LedgerTransaction
from app.core.database import async_session
from app.utils.auth import create_access_token


async def _seed_admin_player_and_balance(async_session_factory):
    """Create tenant + player with balance and an admin token for tests.

    We bypass KYC caps by marking the player as verified and seeding balance
    directly on the Player model.
    """

    async with async_session_factory() as session:
        tenant = await _create_tenant(session)
        player = await _create_player(
            session,
            tenant.id,
            kyc_status="verified",
            balance_available=100.0,
        )

        # Create a simple admin bound to the same tenant
        from app.models.sql_models import AdminUser

        admin = AdminUser(
            tenant_id=tenant.id,
            username="payout-admin",
            email="payout-admin@test.local",
            full_name="Payout Admin",
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


@pytest.mark.usefixtures("client")
@pytest.mark.asyncio
async def test_payout_success_transitions_to_paid_and_writes_single_withdraw_paid_ledger(
    client, async_session_factory
):
    tenant, player, admin, admin_token = await _seed_admin_player_and_balance(async_session_factory)

    # Player initiates withdrawal
    from tests.conftest import _make_player_token

    player_token = _make_player_token(player.id, tenant.id)

    headers_player = {"Authorization": f"Bearer {player_token}", "Idempotency-Key": "payout-success-wd"}
    r_wd = await client.post(
        "/api/v1/player/wallet/withdraw",
        json={"amount": 30, "method": "bank", "address": "addr"},
        headers=headers_player,
    )
    assert r_wd.status_code in (200, 201)
    tx_id = r_wd.json()["transaction"]["id"]

    # Snapshot balances before payout
    async with async_session_factory() as session:
        db_player_before = await session.get(Player, player.id)
        avail_before = db_player_before.balance_real_available
        held_before = db_player_before.balance_real_held

    # Admin approves
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    r_app = await client.post(
        f"/api/v1/finance/withdrawals/{tx_id}/review",
        json={"action": "approve"},
        headers=headers_admin,
    )
    assert r_app.status_code == 200

    # Start payout with success outcome
    payout_headers = {
        "Authorization": f"Bearer {admin_token}",
        "Idempotency-Key": "payout-success-1",
        "X-Mock-Outcome": "success",
    }
    r_payout = await client.post(
        f"/api/v1/finance/withdrawals/{tx_id}/payout",
        headers=payout_headers,
    )
    assert r_payout.status_code == 200

    # Verify tx state, balances and ledger
    async with async_session_factory() as session:
        tx = await session.get(Transaction, tx_id)
        db_player_after = await session.get(Player, player.id)

        assert tx.state == "paid"
        assert db_player_after.balance_real_available == pytest.approx(avail_before)
        assert db_player_after.balance_real_held == pytest.approx(held_before - tx.amount)

        # Exactly one withdraw_paid ledger event
        stmt = select(LedgerTransaction).where(
            LedgerTransaction.tx_id == tx_id,
            LedgerTransaction.status == "withdraw_paid",
        )
        events = (await session.execute(stmt)).scalars().all()
        assert len(events) == 1


@pytest.mark.usefixtures("client")
@pytest.mark.asyncio
async def test_payout_fail_transitions_to_payout_failed_and_writes_no_ledger(
    client, async_session_factory
):
    tenant, player, admin, admin_token = await _seed_admin_player_and_balance(async_session_factory)

    from tests.conftest import _make_player_token

    player_token = _make_player_token(player.id, tenant.id)

    headers_player = {"Authorization": f"Bearer {player_token}", "Idempotency-Key": "payout-fail-wd"}
    r_wd = await client.post(
        "/api/v1/player/wallet/withdraw",
        json={"amount": 20, "method": "bank", "address": "addr"},
        headers=headers_player,
    )
    assert r_wd.status_code in (200, 201)
    tx_id = r_wd.json()["transaction"]["id"]

    async with async_session_factory() as session:
        db_player_before = await session.get(Player, player.id)
        avail_before = db_player_before.balance_real_available
        held_before = db_player_before.balance_real_held

    # Approve withdrawal
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    r_app = await client.post(
        f"/api/v1/finance/withdrawals/{tx_id}/review",
        json={"action": "approve"},
        headers=headers_admin,
    )
    assert r_app.status_code == 200

    # Start payout with forced fail outcome
    payout_headers = {
        "Authorization": f"Bearer {admin_token}",
        "Idempotency-Key": "payout-fail-1",
        "X-Mock-Outcome": "fail",
    }
    r_payout = await client.post(
        f"/api/v1/finance/withdrawals/{tx_id}/payout",
        headers=payout_headers,
    )
    assert r_payout.status_code == 200

    async with async_session_factory() as session:
        tx = await session.get(Transaction, tx_id)
        db_player_after = await session.get(Player, player.id)

        assert tx.state == "payout_failed"
        # Held and available must be unchanged vs before payout
        assert db_player_after.balance_real_available == pytest.approx(avail_before)
        assert db_player_after.balance_real_held == pytest.approx(held_before)

        stmt = select(LedgerTransaction).where(
            LedgerTransaction.tx_id == tx_id,
            LedgerTransaction.status == "withdraw_paid",
        )
        events = (await session.execute(stmt)).scalars().all()
        assert len(events) == 0


@pytest.mark.usefixtures("client")
@pytest.mark.asyncio
async def test_payout_replay_same_idempotency_key_no_duplicate_ledger_or_attempt(
    client, async_session_factory
):
    tenant, player, admin, admin_token = await _seed_admin_player_and_balance(async_session_factory)

    from tests.conftest import _make_player_token

    player_token = _make_player_token(player.id, tenant.id)

    headers_player = {"Authorization": f"Bearer {player_token}", "Idempotency-Key": "payout-replay-wd"}
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
        json={"action": "approve"},
        headers=headers_admin,
    )
    assert r_app.status_code == 200

    payout_headers = {
        "Authorization": f"Bearer {admin_token}",
        "Idempotency-Key": "payout-replay-1",
        "X-Mock-Outcome": "success",
    }

    # First payout call
    r_payout_1 = await client.post(
        f"/api/v1/finance/withdrawals/{tx_id}/payout",
        headers=payout_headers,
    )
    assert r_payout_1.status_code == 200

    # Replay same idempotency key multiple times
    for _ in range(4):
        r_payout_n = await client.post(
            f"/api/v1/finance/withdrawals/{tx_id}/payout",
            headers=payout_headers,
        )
        assert r_payout_n.status_code == 200

    # Verify: single ledger event + single payout attempt row
    async with async_session_factory() as session:
        tx = await session.get(Transaction, tx_id)
        assert tx.state == "paid"

        stmt_ledger = select(LedgerTransaction).where(
            LedgerTransaction.tx_id == tx_id,
            LedgerTransaction.status == "withdraw_paid",
        )
        ledger_events = (await session.execute(stmt_ledger)).scalars().all()
        assert len(ledger_events) == 1

        from app.models.sql_models import PayoutAttempt

        stmt_pa = select(PayoutAttempt).where(
            PayoutAttempt.withdraw_tx_id == tx_id,
            PayoutAttempt.idempotency_key == "payout-replay-1",
        )
        attempts = (await session.execute(stmt_pa)).scalars().all()
        assert len(attempts) == 1
