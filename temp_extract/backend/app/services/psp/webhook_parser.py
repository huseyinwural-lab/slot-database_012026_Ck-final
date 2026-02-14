from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional
import hashlib
import hmac
import json

from config import settings


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


def _verify_mockpsp_signature(payload: Dict[str, Any], headers: Dict[str, str]) -> None:
    """Verify MockPSP webhook signature when enforcement is enabled.

    Scheme (simple but realistic enough for tests):
    - Secret: settings.webhook_secret_mockpsp
    - Header: X-MockPSP-Signature
    - Computation: sha256(secret + json.dumps(payload, sort_keys=True))
    """

    if not settings.webhook_signature_enforced:
        return

    secret = getattr(settings, "webhook_secret_mockpsp", None)
    if not secret:
        raise WebhookSignatureError("Missing webhook secret for mockpsp")

    provided = headers.get("X-MockPSP-Signature") or ""
    if not provided:
        raise WebhookSignatureError("Missing X-MockPSP-Signature header")

    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    expected = hashlib.sha256((secret + body.decode("utf-8")).encode("utf-8")).hexdigest()

    # Constant-time compare not critical for mock, but keep pattern similar.
    if not hmac.compare_digest(provided, expected):
        raise WebhookSignatureError("Invalid MockPSP signature")


async def verify_signature_and_parse(
    *, provider: str, payload: Dict[str, Any], headers: Dict[str, str]
) -> PSPWebhookEvent:
    """Verify signature (provider-specific) and parse into PSPWebhookEvent.

    - For provider == "mockpsp":
      * If settings.webhook_signature_enforced is True, require a valid
        X-MockPSP-Signature header.
      * Otherwise, allow missing/invalid signatures (dev/test convenience).
    - For other providers: placeholder for future real verification.
    """

    if provider == "mockpsp":
        _verify_mockpsp_signature(payload, headers)
    # TODO: add branches for real PSP providers here.

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
