import os
import sys
import asyncio

import pytest

sys.path.append(os.path.abspath("/app/backend"))

from app.services.psp.psp_interface import PSPStatus, build_psp_idem_key
from app.services.psp.mock_psp import MockPSP
from app.services.psp import _reset_psp_singleton_for_tests


def test_psp_mock_idempotent_results_per_action_and_idem_key():
    async def _run():
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
