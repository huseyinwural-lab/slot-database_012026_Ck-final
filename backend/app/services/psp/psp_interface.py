from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Protocol


class PSPStatus(str, Enum):
    """Canonical PSP status values used across providers.

    These are intentionally coarse-grained and provider-agnostic so that
    ledger + business logic do not depend on vendor-specific enums.
    """

    AUTHORIZED = "AUTHORIZED"
    CAPTURED = "CAPTURED"
    FAILED = "FAILED"
    REVERSED = "REVERSED"
    PAID = "PAID"


@dataclass
class PSPResult:
    """Standardized result returned by PSP adapters.

    Attributes:
        provider: Logical provider name (e.g. "mockpsp", "stripe").
        provider_ref: Provider-side reference for the payment/instruction.
        provider_event_id: Unique identifier for the specific event/webhook.
        status: PSPStatus describing the outcome.
        raw: Optional raw payload/metadata from the PSP (for logging/debug).
    """

    provider: str
    provider_ref: str
    provider_event_id: str
    status: PSPStatus
    raw: Optional[Dict[str, Any]] = None


class PaymentProvider(Protocol):
    """High-level PSP adapter contract.

    Any real PSP implementation (Stripe, Adyen, etc.) or the MockPSP must
    conform to this interface so that business logic can remain provider
    agnostic.
    """

    async def authorize_deposit(
        self,
        *,
        tx_id: str,
        tenant_id: str,
        player_id: str,
        amount: float,
        currency: str,
        psp_idem_key: str,
    ) -> "PSPResult":
        ...

    async def capture_deposit(
        self,
        *,
        tx_id: str,
        tenant_id: str,
        player_id: str,
        amount: float,
        currency: str,
        psp_idem_key: str,
    ) -> "PSPResult":
        ...

    async def payout_withdrawal(
        self,
        *,
        tx_id: str,
        tenant_id: str,
        player_id: str,
        amount: float,
        currency: str,
        psp_idem_key: str,
    ) -> "PSPResult":
        ...

    async def refund_deposit(
        self,
        *,
        tx_id: str,
        tenant_id: str,
        player_id: str,
        amount: float,
        currency: str,
        psp_idem_key: str,
    ) -> "PSPResult":
        ...




def build_psp_idem_key(tx_id: str) -> str:
    """Canonical PSP idempotency key builder.

    All PSP calls should use this helper to standardize idempotency keys.
    Example: "tx_<tx_id>".
    """

    return f"tx_{tx_id}"


# --- Interface functions ----------------------------------------------------

async def authorize_deposit(
    *,
    tx_id: str,
    tenant_id: str,
    player_id: str,
    amount: float,
    currency: str,
    psp_idem_key: str,
) -> PSPResult:
    """Authorize a deposit with the PSP.

    For some providers this may be a no-op (immediate capture), but the
    interface treats it as a separate step to support auth/capture models.
    Implementations must be idempotent with respect to psp_idem_key.
    """

    raise NotImplementedError


async def capture_deposit(
    *,
    tx_id: str,
    tenant_id: str,
    player_id: str,
    amount: float,
    currency: str,
    psp_idem_key: str,
) -> PSPResult:
    """Capture a previously authorized deposit.

    Implementations must be idempotent for a given psp_idem_key.
    """

    raise NotImplementedError


async def payout_withdrawal(
    *,
    tx_id: str,
    tenant_id: str,
    player_id: str,
    amount: float,
    currency: str,
    psp_idem_key: str,
) -> PSPResult:
    """Trigger a payout/withdrawal to the player.

    Called typically when an approved withdrawal is being marked as paid.
    Implementations must be idempotent for a given psp_idem_key.
    """

    raise NotImplementedError


async def refund_deposit(
    *,
    tx_id: str,
    tenant_id: str,
    player_id: str,
    amount: float,
    currency: str,
    psp_idem_key: str,
) -> PSPResult:
    """(Optional) Refund a previously captured deposit.

    This is a placeholder to keep the interface future-proof; implementations
    may raise NotImplementedError if refunds are not supported.
    """

    raise NotImplementedError
