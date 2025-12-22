from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from datetime import datetime, timezone
from typing import Optional

from app.core.database import get_session
from app.models.sql_models import Transaction, Player
from app.services.audit import audit
from app.services.psp.webhook_parser import (
    verify_signature_and_parse,
    PSPWebhookEvent,
    WebhookSignatureError,
)
from app.services.ledger_shadow import shadow_append_event, shadow_apply_delta

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])


@router.post("/webhook/{provider}")
async def payments_webhook(
    provider: str,
    request: Request,
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_session),
):
    """PSP-02 webhook endpoint.

    Responsibilities:
    - Verify signature (provider-specific; MockPSP currently bypassed).
    - Enforce replay guard on (provider, provider_event_id).
    - Map webhook into ledger events and created-gated balance deltas.
    - Maintain a minimal Transaction record for audit/debug.
    """

    # 1) Signature + canonical parsing
    try:
        event: PSPWebhookEvent = await verify_signature_and_parse(
            provider=provider,
            payload=payload,
            headers={k: v for k, v in request.headers.items()} if request else {},
        )
    except WebhookSignatureError as exc:
        raise HTTPException(status_code=401, detail={"error_code": "WEBHOOK_SIGNATURE_INVALID", "message": str(exc)})
    except Exception as exc:
        raise HTTPException(status_code=400, detail={"error_code": "INVALID_WEBHOOK", "message": str(exc)})

    request_id = getattr(request.state, "request_id", "unknown") if request else "unknown"
    ip = request.client.host if request and request.client else None

    # 2) Idempotent ledger write via (provider, provider_event_id)
    # We rely on ledger_repo.append_event's provider_event_id unique constraint
    # for strong replay guarantees. Here we just map the event_type to a
    # canonical ledger status + delta.

    # For MVP, support deposit_captured and withdraw_paid
    status = event.event_type or ""

    # Deposit captured -> credit available
    if status == "deposit_captured":
        # Append ledger event; created flag controls delta
        from app.repositories.ledger_repo import append_event

        if not (event.tenant_id and event.player_id):
            raise HTTPException(status_code=400, detail={"error_code": "MISSING_IDS"})

        ledger_event, created = await append_event(
            session,
            tenant_id=event.tenant_id,
            player_id=event.player_id,
            tx_id=event.tx_id,
            type="deposit",
            direction="credit",
            amount=event.amount,
            currency=event.currency,
            status="deposit_captured",
            provider=event.provider,
            provider_ref=event.provider_ref,
            provider_event_id=event.provider_event_id,
        )

        if created:
            # Apply created-gated delta to WalletBalance
            await shadow_apply_delta(
                session=session,
                tenant_id=event.tenant_id,
                player_id=event.player_id,
                currency=event.currency,
                delta_available=event.amount,
                delta_pending=0.0,
            )

    # withdraw_paid and other statuses can be wired here later in PSP-02D/PSP-04.

    # 3) Minimal Transaction record for audit/debug (existing behavior)
    # (Re-use old skeleton semantics: idempotent on (provider, provider_event_id))
    stmt = select(Transaction).where(
        Transaction.provider == provider,
        Transaction.provider_event_id == event.provider_event_id,
    )
    existing_tx = (await session.execute(stmt)).scalars().first()

    if existing_tx:
        await audit.log_event(
            session=session,
            request_id=request_id,
            actor_user_id="system",
            tenant_id=existing_tx.tenant_id,
            action="FIN_IDEMPOTENCY_HIT",
            resource_type="payment_webhook",
            resource_id=existing_tx.id,
            result="success",
            details={
                "tx_id": existing_tx.id,
                "provider": provider,
                "provider_event_id": event.provider_event_id,
            },
            ip_address=ip,
        )
        await session.commit()
        return {"status": "ok", "idempotent": True}

    tx = Transaction(
        tenant_id=event.tenant_id or "unknown",
        player_id=event.player_id or "unknown",
        type="deposit" if "deposit" in status else "other",
        amount=event.amount,
        currency=event.currency,
        status="completed",
        state="completed",
        provider=provider,
        provider_event_id=event.provider_event_id,
        metadata_json={"raw_payload": payload},
        balance_after=0.0,
    )

    session.add(tx)

    await audit.log_event(
        session=session,
        request_id=request_id,
        actor_user_id="system",
        tenant_id=event.tenant_id or "unknown",
        action="FIN_WEBHOOK_RECEIVED",
        resource_type="payment_webhook",
        resource_id=tx.id,
        result="success",
        details={
            "tx_id": tx.id,
            "player_id": event.player_id,
            "amount": event.amount,
            "currency": event.currency,
            "provider": provider,
            "provider_event_id": event.provider_event_id,
        },
        ip_address=ip,
    )

    await session.commit()

    return {"status": "ok", "idempotent": False, "tx_id": tx.id}
