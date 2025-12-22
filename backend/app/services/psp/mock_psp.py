from __future__ import annotations

import hashlib
from typing import Any, Dict, Tuple

from .psp_interface import PSPResult, PSPStatus


_PROVIDER_NAME = "mockpsp"


class MockPSP:
    """Deterministic mock PSP adapter.

    - No external calls; everything is pure and in-memory.
    - Idempotent per (action, psp_idem_key): same inputs -> same PSPResult.
    - Deterministic provider_ref and provider_event_id for reproducible tests.
    """

    def __init__(self) -> None:
        # In-memory idempotency store: (action, psp_idem_key) -> PSPResult
        self._store: Dict[Tuple[str, str], PSPResult] = {}

    def _hash_idem(self, psp_idem_key: str) -> str:
        h = hashlib.sha256(psp_idem_key.encode("utf-8")).hexdigest()
        return h[:8]

    def _build_result(self, *, action: str, tx_id: str, psp_idem_key: str, status: PSPStatus) -> PSPResult:
        key = (action, psp_idem_key)
        if key in self._store:
            return self._store[key]

        provider_ref = f"{_PROVIDER_NAME}:{tx_id}"
        idem_hash = self._hash_idem(psp_idem_key)
        provider_event_id = f"{action}:{tx_id}:{idem_hash}"

        result = PSPResult(
            provider=_PROVIDER_NAME,
            provider_ref=provider_ref,
            provider_event_id=provider_event_id,
            status=status,
            raw={"action": action, "tx_id": tx_id, "psp_idem_key": psp_idem_key},
        )
        self._store[key] = result
        return result

    async def authorize_deposit(
        self,
        *,
        tx_id: str,
        tenant_id: str,
        player_id: str,
        amount: float,
        currency: str,
        psp_idem_key: str,
    ) -> PSPResult:
        """Authorize a deposit in a deterministic, idempotent way.

        For MockPSP we treat authorize as always succeeding.
        """

        return self._build_result(
            action="authorize_deposit",
            tx_id=tx_id,
            psp_idem_key=psp_idem_key,
            status=PSPStatus.AUTHORIZED,
        )

    async def capture_deposit(
        self,
        *,
        tx_id: str,
        tenant_id: str,
        player_id: str,
        amount: float,
        currency: str,
        psp_idem_key: str,
    ) -> PSPResult:
        """Capture a deposit; always succeeds and is idempotent."""

        return self._build_result(
            action="capture_deposit",
            tx_id=tx_id,
            psp_idem_key=psp_idem_key,
            status=PSPStatus.CAPTURED,
        )

    async def payout_withdrawal(
        self,
        *,
        tx_id: str,
        tenant_id: str,
        player_id: str,
        amount: float,
        currency: str,
        psp_idem_key: str,
    ) -> PSPResult:
        """Payout a withdrawal; always succeeds and is idempotent."""

        return self._build_result(
            action="payout_withdrawal",
            tx_id=tx_id,
            psp_idem_key=psp_idem_key,
            status=PSPStatus.PAID,
        )

    async def refund_deposit(
        self,
        *,
        tx_id: str,
        tenant_id: str,
        player_id: str,
        amount: float,
        currency: str,
        psp_idem_key: str,
    ) -> PSPResult:
        """Refund a deposit; modeled as REVERSED and idempotent."""

        return self._build_result(
            action="refund_deposit",
            tx_id=tx_id,
            psp_idem_key=psp_idem_key,
            status=PSPStatus.REVERSED,
        )


# Convenience factory for tests/routers

def get_mock_psp() -> MockPSP:
    return MockPSP()
