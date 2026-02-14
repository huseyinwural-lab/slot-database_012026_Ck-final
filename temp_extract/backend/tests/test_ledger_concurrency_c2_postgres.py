import os
import sys
import asyncio

import pytest
from sqlmodel import select

sys.path.append(os.path.abspath("/app/backend"))

from config import settings
from app.repositories.ledger_repo import WalletBalance
from app.models.sql_models import Player
from tests.conftest import _create_tenant, _create_player, _make_player_token
from server import app  # noqa: F401  - ensure app import for fixtures


def _should_run_postgres_tests() -> bool:
    """Return True only when Postgres-backed tests are explicitly enabled.

    This is intentionally strict so that the C2 concurrency test only runs in
    environments that:
    - set RUN_POSTGRES_TESTS=1, and
    - use a Postgres DATABASE_URL
    """

    if os.getenv("RUN_POSTGRES_TESTS") != "1":
        return False

    url = (getattr(settings, "database_url", "") or "").lower()
    return url.startswith("postgres")


@pytest.mark.postgres_only
@pytest.mark.usefixtures("client")
def test_C2_postgres_concurrent_withdraw_single_success(async_session_factory, client):
    """C2: Postgres-only concurrency sanity – enforce ON + lock_for_update ON.

    Scenario (when actually run on Postgres):
    - Player funded to 100 via deposit (which also seeds WalletBalance snapshot).
    - ledger_enforce_balance=True and ledger_shadow_write=True.
    - Two concurrent withdraw attempts for 80, with different Idempotency-Keys.

    Expected:
    - Exactly one request succeeds (200/201).
    - The other fails with 400 and error_code=INSUFFICIENT_FUNDS.
    - WalletBalance snapshot reflects a single hold: available=20, pending=80.

    NOTE: In this environment (SQLite test DB), this test is always skipped
    unless RUN_POSTGRES_TESTS=1 *and* DATABASE_URL is Postgres.
    """

    if not _should_run_postgres_tests():
        pytest.skip(
            "Postgres-only concurrency test (set RUN_POSTGRES_TESTS=1 with postgres DATABASE_URL)"
        )

    # Enforce ledger snapshot for funds checks and ensure shadow writes are on.
    old_enforce = settings.ledger_enforce_balance
    old_shadow = settings.ledger_shadow_write
    settings.ledger_enforce_balance = True
    settings.ledger_shadow_write = True

    async def _run():
        async with async_session_factory() as session:
            tenant = await _create_tenant(session)
            player = await _create_player(
                session,
                tenant.id,
                balance_available=0.0,
                kyc_status="verified",
            )
            token = _make_player_token(player.id, tenant.id)

        # Fund via deposit so both legacy player balance and WalletBalance start from 100.
        dep_headers = {
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": "idem-c2-deposit",
        }
        r_dep = client.post(
            "/api/v1/player/wallet/deposit",
            json={"amount": 100.0, "method": "test"},
            headers=dep_headers,
        )
        assert r_dep.status_code in (200, 201)

        async def do_withdraw(idem_key: str):
            """Run a withdraw call in a threadpool to allow real parallelism.

            TestClient is sync; using run_in_executor gives us two overlapping
            HTTP calls against the same FastAPI app + Postgres backend.
            """

            loop = asyncio.get_running_loop()

            def _call():
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Idempotency-Key": idem_key,
                }
                return client.post(
                    "/api/v1/player/wallet/withdraw",
                    json={"amount": 80.0, "method": "test_bank", "address": "c2"},
                    headers=headers,
                )

            return await loop.run_in_executor(None, _call)

        # Fire two concurrent withdraw attempts with different idempotency keys.
        res1, res2 = await asyncio.gather(
            do_withdraw("idem-c2-w1"),
            do_withdraw("idem-c2-w2"),
        )

        statuses = {res1.status_code, res2.status_code}
        assert any(code in (200, 201) for code in statuses), statuses
        assert 400 in statuses, statuses

        # Validate error shape for the failure response.
        for r in (res1, res2):
            if r.status_code == 400:
                body = r.json()
                err = body.get("error_code") or body.get("detail", {}).get("error_code")
                assert err == "INSUFFICIENT_FUNDS"

        # Snapshot invariant: exactly one hold applied (available=20, pending=80).
        async with async_session_factory() as session:
            wb = (
                await session.execute(
                    select(WalletBalance).where(
                        WalletBalance.tenant_id == tenant.id,
                        WalletBalance.player_id == player.id,
                        WalletBalance.currency == "USD",
                    )
                )
            ).scalars().first()
            assert wb is not None
            assert wb.balance_real_available == pytest.approx(20.0)
            assert wb.balance_real_pending == pytest.approx(80.0)

            # Legacy Player aggregate must agree with WalletBalance snapshot
            db_player = await session.get(Player, player.id)
            assert db_player is not None
            assert db_player.balance_real_available == pytest.approx(wb.balance_real_available)
            assert db_player.balance_real_held == pytest.approx(wb.balance_real_pending)

    try:
        asyncio.run(_run())
    finally:
        # Restore global settings to avoid leaking state into other tests.
        settings.ledger_enforce_balance = old_enforce
        settings.ledger_shadow_write = old_shadow
