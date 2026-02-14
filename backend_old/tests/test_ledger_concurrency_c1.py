import os
import sys
import asyncio
import pytest

sys.path.append(os.path.abspath("/app/backend"))

from app.repositories.ledger_repo import WalletBalance, apply_balance_delta, get_balance
from tests.conftest import _create_tenant, _create_player
from server import app  # noqa: F401  - ensure app import for fixtures


@pytest.mark.usefixtures("client")
def test_C1_01_get_balance_lock_flag_does_not_change_result(async_session_factory):
    """C1-01: get_balance(lock_for_update=True) returns same values as without lock.

    This is a functional regression guard for the new lock_for_update parameter.
    On SQLite, with_for_update() is effectively a no-op, but the API surface
    should behave identically in both cases.
    """

    async def _run():
        async with async_session_factory() as session:
            tenant = await _create_tenant(session)
            player = await _create_player(session, tenant.id, balance_available=0.0, kyc_status="verified")

            # Seed a WalletBalance row via apply_balance_delta so that get_balance
            # reads an existing snapshot.
            await apply_balance_delta(
                session,
                tenant_id=tenant.id,
                player_id=player.id,
                currency="USD",
                delta_available=123.45,
                delta_pending=6.78,
            )

            bal_unlocked = await get_balance(
                session,
                tenant_id=tenant.id,
                player_id=player.id,
                currency="USD",
                lock_for_update=False,
            )

            bal_locked = await get_balance(
                session,
                tenant_id=tenant.id,
                player_id=player.id,
                currency="USD",
                lock_for_update=True,
            )

            assert isinstance(bal_unlocked, WalletBalance)
            assert isinstance(bal_locked, WalletBalance)

            assert bal_unlocked.tenant_id == bal_locked.tenant_id
            assert bal_unlocked.player_id == bal_locked.player_id
            assert bal_unlocked.currency == bal_locked.currency
            assert bal_unlocked.balance_real_available == pytest.approx(
                bal_locked.balance_real_available
            )
            assert bal_unlocked.balance_real_pending == pytest.approx(
                bal_locked.balance_real_pending
            )

    asyncio.run(_run())
