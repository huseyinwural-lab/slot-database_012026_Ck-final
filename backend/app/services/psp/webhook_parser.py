from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class PSPWebhookEvent:
    """Canonical representation of a PSP webhook event.

    This struct is intentionally minimal and provider-agnostic. Individual
    adapters are responsible for mapping provider-specific payloads into this
    shape.
    """

    provider: str
    provider_event_id: str
    provider_ref: Optional[str]
    event_type: str  # e.g. deposit_authorized, deposit_captured, withdraw_paid
    tx_id: Optional[str]
    tenant_id: Optional[str]
    player_id: Optional[str]
    amount: float
    currency: str
    raw: Dict[str, Any]


class WebhookSignatureError(Exception):
    """Raised when a webhook signature is missing or invalid."""


async def verify_signature_and_parse(
    *, provider: str, payload: Dict[str, Any], headers: Dict[str, str]
) -> PSPWebhookEvent:
    """Verify signature (provider-specific) and parse into PSPWebhookEvent.

    For MockPSP in dev/test we accept all payloads without real signature
    verification. For real providers, this function will enforce signature
    checks in a later phase (PSP-02B).
    """

    # TODO(PSP-02B): Implement real signature verification per provider.
    # For now, treat all MockPSP events as trusted in test/dev.

    provider_event_id = str(payload.get("provider_event_id") or payload.get("event_id") or "")
    if not provider_event_id:
        raise ValueError("provider_event_id is required in webhook payload")

    provider_ref = payload.get("provider_ref") or payload.get("payment_intent_id")
    event_type = str(payload.get("event_type") or payload.get("type") or "").strip()
    tx_id = payload.get("tx_id")
    tenant_id = payload.get("tenant_id")
    player_id = payload.get("player_id")
    amount = float(payload.get("amount", 0.0))
    currency = str(payload.get("currency") or "USD")

    return PSPWebhookEvent(
        provider=provider,
        provider_event_id=provider_event_id,
        provider_ref=provider_ref,
        event_type=event_type,
        tx_id=tx_id,
        tenant_id=tenant_id,
        player_id=player_id,
        amount=amount,
        currency=currency,
        raw=payload,
    )
