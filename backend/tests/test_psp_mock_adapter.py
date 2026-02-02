import os
import sys
import asyncio


sys.path.append(os.path.abspath("/app/backend"))

from app.services.psp.psp_interface import PSPStatus, build_psp_idem_key
from app.services.psp.mock_psp import MockPSP
from app.services.psp import _reset_psp_singleton_for_tests


def test_psp_mock_idempotent_results_per_action_and_idem_key():
    async def _run():
        _reset_psp_singleton_for_tests()
        psp = MockPSP()
        tx_id = "tx-123"
        idem = build_psp_idem_key(tx_id)

        r1 = await psp.authorize_deposit(
            tx_id=tx_id,
            tenant_id="t1",
            player_id="p1",
            amount=10.0,
            currency="USD",
            psp_idem_key=idem,
        )
        r2 = await psp.authorize_deposit(
            tx_id=tx_id,
            tenant_id="t1",
            player_id="p1",
            amount=10.0,
            currency="USD",
            psp_idem_key=idem,
        )

        assert r1 is r2  # same object from in-memory store
        assert r1.status == PSPStatus.AUTHORIZED

        # Different action uses a different idempotent bucket
        c1 = await psp.capture_deposit(
            tx_id=tx_id,
            tenant_id="t1",
            player_id="p1",
            amount=10.0,
            currency="USD",
            psp_idem_key=idem,
        )
        c2 = await psp.capture_deposit(
            tx_id=tx_id,
            tenant_id="t1",
            player_id="p1",
            amount=10.0,
            currency="USD",
            psp_idem_key=idem,
        )

        assert c1 is c2
        assert c1.status == PSPStatus.CAPTURED

    asyncio.run(_run())


def test_psp_mock_payout_and_refund_statuses():
    async def _run():
        _reset_psp_singleton_for_tests()
        psp = MockPSP()
        tx_id = "tx-456"
        idem = build_psp_idem_key(tx_id)

        payout = await psp.payout_withdrawal(
            tx_id=tx_id,
            tenant_id="t1",
            player_id="p1",
            amount=50.0,
            currency="USD",
            psp_idem_key=idem,
        )
        assert payout.status == PSPStatus.PAID
        assert payout.provider_ref.startswith("mockpsp:")

        refund = await psp.refund_deposit(
            tx_id=tx_id,
            tenant_id="t1",
            player_id="p1",
            amount=50.0,
            currency="USD",
            psp_idem_key=idem,
        )
        assert refund.status == PSPStatus.REVERSED
        assert refund.provider_ref == payout.provider_ref

    asyncio.run(_run())


def test_psp_mock_outcome_override_fail_and_idempotency():
    async def _run():
        _reset_psp_singleton_for_tests()
        psp = MockPSP()
        tx_id = "tx-789"
        idem = build_psp_idem_key(tx_id)

        # First register a fail outcome override (simulating dev/test env)
        psp.register_outcome_override(idem, "fail")

        r1 = await psp.capture_deposit(
            tx_id=tx_id,
            tenant_id="t1",
            player_id="p1",
            amount=10.0,
            currency="USD",
            psp_idem_key=idem,
        )
        r2 = await psp.capture_deposit(
            tx_id=tx_id,
            tenant_id="t1",
            player_id="p1",
            amount=10.0,
            currency="USD",
            psp_idem_key=idem,
        )

        # Outcome is deterministically FAILED and idempotent for the same key
        assert r1 is r2
        assert r1.status == PSPStatus.FAILED

    asyncio.run(_run())




def test_psp_mock_outcome_override_ignored_in_non_dev_env():
    async def _run():
        from config import settings as config_settings

        old_env = config_settings.env
        config_settings.env = "staging"
        try:
            _reset_psp_singleton_for_tests()
            psp = MockPSP()
            tx_id = "tx-non-dev"
            idem = build_psp_idem_key(tx_id)

            # Attempt to register a fail outcome in a non-dev env
            psp.register_outcome_override(idem, "fail")

            r1 = await psp.capture_deposit(
                tx_id=tx_id,
                tenant_id="t1",
                player_id="p1",
                amount=10.0,
                currency="USD",
                psp_idem_key=idem,
            )
            r2 = await psp.capture_deposit(
                tx_id=tx_id,
                tenant_id="t1",
                player_id="p1",
                amount=10.0,
                currency="USD",
                psp_idem_key=idem,
            )

            # Override must be ignored; default CAPTURED status should remain
            assert r1 is r2
            assert r1.status == PSPStatus.CAPTURED
        finally:
            config_settings.env = old_env

    asyncio.run(_run())



def test_psp_mock_payout_fail_with_outcome_override():
    async def _run():
        _reset_psp_singleton_for_tests()
        psp = MockPSP()
        tx_id = "tx-999"
        idem = build_psp_idem_key(tx_id)

        # Force a fail outcome for this idempotency key
        psp.register_outcome_override(idem, "fail")

        payout1 = await psp.payout_withdrawal(
            tx_id=tx_id,
            tenant_id="t1",
            player_id="p1",
            amount=50.0,
            currency="USD",
            psp_idem_key=idem,
        )
        payout2 = await psp.payout_withdrawal(
            tx_id=tx_id,
            tenant_id="t1",
            player_id="p1",
            amount=50.0,
            currency="USD",
            psp_idem_key=idem,
        )

        assert payout1 is payout2
        assert payout1.status == PSPStatus.FAILED

    asyncio.run(_run())
