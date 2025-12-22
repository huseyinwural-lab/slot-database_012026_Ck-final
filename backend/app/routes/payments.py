from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from datetime import datetime, timezone
from typing import Optional

from app.core.database import get_session
from app.models.sql_models import Transaction, Player
from app.services.audit import audit

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])


@router.post("/webhook/{provider}")
async def payments_webhook(
    provider: str,
    payload: dict = Body(...),
    request: Request = None,
    session: AsyncSession = Depends(get_session),
):
    """Skeleton webhook endpoint.

    - Requires provider_event_id in payload
    - Idempotent on (provider, provider_event_id)
    - Emits FIN_WEBHOOK_RECEIVED on first call
    - Emits FIN_IDEMPOTENCY_HIT on duplicate
    """
    provider_event_id = payload.get("provider_event_id")
    if not provider_event_id:
        raise HTTPException(status_code=400, detail={"error_code": "PROVIDER_EVENT_ID_REQUIRED"})

    request_id = getattr(request.state, "request_id", "unknown") if request else "unknown"
    ip = request.client.host if request and request.client else None

    # Check existing by provider + provider_event_id
    stmt = select(Transaction).where(
        Transaction.provider == provider,
        Transaction.provider_event_id == provider_event_id,
    )
    existing = (await session.execute(stmt)).scalars().first()

    if existing:
        # Duplicate event -> no-op + FIN_IDEMPOTENCY_HIT
        await audit.log_event(
            session=session,
            request_id=request_id,
            actor_user_id="system",
            tenant_id=existing.tenant_id,
            action="FIN_IDEMPOTENCY_HIT",
            resource_type="payment_webhook",
            resource_id=existing.id,
            result="success",
            details={
                "tx_id": existing.id,
                "provider": provider,
                "provider_event_id": provider_event_id,
            },
            ip_address=ip,
        )
        await session.commit()
        return {"status": "ok", "idempotent": True}

    # New event -> create minimal transaction record
    player_id: Optional[str] = payload.get("player_id")
    tenant_id: Optional[str] = payload.get("tenant_id")
    amount: float = float(payload.get("amount", 0))
    currency: str = payload.get("currency", "USD")
    tx_type: str = payload.get("type", "deposit")

    tx = Transaction(
        tenant_id=tenant_id or "unknown",
        player_id=player_id or "unknown",
        type=tx_type,
        amount=amount,
        currency=currency,
        status="completed",
        state="completed",
        provider=provider,
        provider_event_id=provider_event_id,
        metadata_json={"raw_payload": payload},
        balance_after=0.0,
    )

    session.add(tx)

    await audit.log_event(
        session=session,
        request_id=request_id,
        actor_user_id="system",
        tenant_id=tenant_id or "unknown",
        action="FIN_WEBHOOK_RECEIVED",
        resource_type="payment_webhook",
        resource_id=tx.id,
        result="success",
        details={
            "tx_id": tx.id,
            "player_id": player_id,
            "amount": amount,
            "currency": currency,
            "provider": provider,
            "provider_event_id": provider_event_id,
        },
        ip_address=ip,
    )

    await session.commit()

    return {"status": "ok", "idempotent": False, "tx_id": tx.id}
