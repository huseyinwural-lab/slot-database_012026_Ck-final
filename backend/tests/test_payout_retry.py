import os
import sys

import pytest
from sqlmodel import select

sys.path.append(os.path.abspath("/app/backend"))

from server import app  # noqa: F401
from tests.conftest import _create_tenant, _create_player
from app.models.sql_models import Transaction, Player, PayoutAttempt
from app.repositories.ledger_repo import LedgerTransaction
from app.utils.auth import create_access_token


async def _seed_admin_player_and_balance(async_session_factory):
    async with async_session_factory() as session:
        tenant = await _create_tenant(session)
        player = await _create_player(
            session,
            tenant.id,
            kyc_status="verified",
            balance_available=40.0,
        )

        from app.models.sql_models import AdminUser

        existing = (
            await session.execute(
                select(AdminUser).where(AdminUser.email == "payout-retry-admin@test.local")
            )
        ).scalars().first()
        if existing:
            admin = existing
        else:
            admin = AdminUser(
                tenant_id=tenant.id,
                username="payout-retry-admin",
                email="payout-retry-admin@test.local",
                full_name="Payout Retry Admin",
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
async def test_payout_retry_after_fail_reduces_held_once(client, async_session_factory):
    """TCK-P05-RETRY-001: fail -> retry success should drop held exactly once."""

    tenant, player, admin, admin_token = await _seed_admin_player_and_balance(async_session_factory)

    from tests.conftest import _make_player_token

    player_token = _make_player_token(player.id, tenant.id)

    # 1) Withdraw 30 (requested)
    headers_player = {"Authorization": f"Bearer {player_token}", "Idempotency-Key": "payout-retry-wd"}
    r_wd = await client.post(
        "/api/v1/player/wallet/withdraw",
        json={"amount": 30, "method": "test_bank", "address": "addr"},
        headers=headers_player,
    )
    assert r_wd.status_code in (200, 201)
    tx_id = r_wd.json()["transaction"]["id"]

    async with async_session_factory() as session:
        db_player_before = await session.get(Player, player.id)
        avail_before = db_player_before.balance_real_available
        held_before = db_player_before.balance_real_held

    assert avail_before == pytest.approx(10.0)
    assert held_before == pytest.approx(30.0)

    # 2) Admin approve -> approved
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    r_app = await client.post(
        f"/api/v1/finance/withdrawals/{tx_id}/review",
        json={"action": "approve", "reason": "test:legacy_fix"},
        headers=headers_admin,
    )
    assert r_app.status_code == 200

    # 3) Payout fail
    payout_headers_fail = {
        "Authorization": f"Bearer {admin_token}",
        "Idempotency-Key": "payout-retry-fail-1",
        "X-Mock-Outcome": "fail",
    }
    r_payout_fail = await client.post(
        f"/api/v1/finance/withdrawals/{tx_id}/payout",
        headers=payout_headers_fail,
    )
    assert r_payout_fail.status_code == 200

    async with async_session_factory() as session:
        tx = await session.get(Transaction, tx_id)
        db_player_after_fail = await session.get(Player, player.id)

        assert tx.state == "payout_failed"
        assert db_player_after_fail.balance_real_available == pytest.approx(avail_before)
        assert db_player_after_fail.balance_real_held == pytest.approx(held_before)

        stmt_ledger = select(LedgerTransaction).where(
            LedgerTransaction.tx_id == tx_id,
            LedgerTransaction.status == "withdraw_paid",
        )
        events = (await session.execute(stmt_ledger)).scalars().all()
        assert len(events) == 0

    # 4) Payout retry success
    payout_headers_success = {
        "Authorization": f"Bearer {admin_token}",
        "Idempotency-Key": "payout-retry-success-1",
        "X-Mock-Outcome": "success",
    }
    r_payout_success = await client.post(
        f"/api/v1/finance/withdrawals/{tx_id}/payout",
        headers=payout_headers_success,
    )
    assert r_payout_success.status_code == 200

    async with async_session_factory() as session:
        tx = await session.get(Transaction, tx_id)
        db_player_after_success = await session.get(Player, player.id)

        assert tx.state == "paid"
        # Held should drop to zero, available unchanged vs fail
        assert db_player_after_success.balance_real_available == pytest.approx(avail_before)
        assert db_player_after_success.balance_real_held == pytest.approx(0.0)

        # Exactly one withdraw_paid ledger event
        stmt_ledger = select(LedgerTransaction).where(
            LedgerTransaction.tx_id == tx_id,
            LedgerTransaction.status == "withdraw_paid",
        )
        events = (await session.execute(stmt_ledger)).scalars().all()
        assert len(events) == 1

        # Two payout attempts with different idempotency keys
        stmt_pa = select(PayoutAttempt).where(PayoutAttempt.withdraw_tx_id == tx_id)
        attempts = (await session.execute(stmt_pa)).scalars().all()
        assert len(attempts) == 2
