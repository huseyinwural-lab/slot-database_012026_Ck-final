from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func
from typing import Optional

from app.core.database import get_session
from app.models.sql_models import Transaction, AdminUser
from app.repositories.ledger_repo import LedgerTransaction
from app.models.reconciliation import ReconciliationFinding
from app.services.audit import audit
from app.utils.auth import get_current_admin
from app.utils.tenant import get_current_tenant_id
from app.services.psp.webhook_parser import (
    verify_signature_and_parse,
    PSPWebhookEvent,
    WebhookSignatureError,
)
from app.services.ledger_shadow import shadow_apply_delta
from app.services.affiliate_p0_engine import accrue_on_first_deposit
from app.services.crm_engine import CRMEngine
from app.models.growth_models import GrowthEvent

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

        if not (event.tenant_id and event.player_id and event.tx_id):
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

            # --- GROWTH LOOP START ---
            # Check if First Deposit by counting successful deposits in Ledger
            stmt = select(func.count(Transaction.id)).where(
                Transaction.tenant_id == event.tenant_id,
                Transaction.player_id == event.player_id,
                Transaction.type == "deposit",
                Transaction.status == "deposit_captured"
            )
            dep_count = (await session.execute(stmt)).scalar() or 0
            
            # Since we just appended the event above, count should be 1 for the first time
            if dep_count == 1:
                # 1. Affiliate Commission (P0: CPA on first deposit)
                try:
                    await accrue_on_first_deposit(
                        session,
                        tenant_id=event.tenant_id,
                        player_id=event.player_id,
                        deposit_amount=event.amount,
                        currency=event.currency,
                    )
                except Exception:
                    # best-effort, do not break deposits
                    pass
                
                # 2. CRM Trigger
                crm_engine = CRMEngine()
                growth_event = GrowthEvent(
                    tenant_id=event.tenant_id,
                    event_type="FIRST_DEPOSIT",
                    player_id=event.player_id,
                    payload={"amount": event.amount, "currency": event.currency, "tx_id": event.tx_id}
                )
                session.add(growth_event)
                await session.commit() # Save event ID
                await session.refresh(growth_event)
                await crm_engine.process_event(session, growth_event)
            # --- GROWTH LOOP END ---

    elif status == "withdraw_paid":
        # Payout confirmed -> finalize pending (debit)
        from app.repositories.ledger_repo import append_event

        if not (event.tenant_id and event.player_id and event.tx_id):
            raise HTTPException(status_code=400, detail={"error_code": "MISSING_IDS"})

        ledger_event, created = await append_event(
            session,
            tenant_id=event.tenant_id,
            player_id=event.player_id,
            tx_id=event.tx_id,
            type="withdraw",
            direction="debit",
            amount=event.amount,
            currency=event.currency,
            status="withdraw_paid",
            provider=event.provider,
            provider_ref=event.provider_ref,
            provider_event_id=event.provider_event_id,
        )

        if created:
            # Created-gated: finalize pending only once
            await shadow_apply_delta(
                session=session,
                tenant_id=event.tenant_id,
                player_id=event.player_id,
                currency=event.currency,
                delta_available=0.0,
                delta_pending=-event.amount,
            )

    # Other statuses (failed/reversed) can be wired in PSP-04.

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



@router.get("/reconciliation/findings")
async def list_reconciliation_findings(
    request: Request,
    provider: Optional[str] = None,
    status: Optional[str] = None,
    tenant_id: Optional[str] = None,
    finding_type: Optional[str] = None,
    severity: Optional[str] = None,
    player_id: Optional[str] = None,
    tx_id: Optional[str] = None,
    provider_event_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    """List reconciliation findings for the current tenant.

    - Admin auth is required.
    - Results are scoped to the admin's tenant unless an explicit tenant_id is
      provided (for multi-tenant/platform owners).
    """

    # Clamp pagination
    if limit <= 0:
        limit = 50
    limit = min(limit, 200)
    if offset < 0:
        offset = 0

    effective_tenant_id = tenant_id or await get_current_tenant_id(
        request, current_admin, session=session
    )

    query = select(ReconciliationFinding).where(
        ReconciliationFinding.tenant_id == effective_tenant_id
    )

    if provider:
        query = query.where(ReconciliationFinding.provider == provider)
    if status:
        query = query.where(ReconciliationFinding.status == status)
    if finding_type:
        query = query.where(ReconciliationFinding.finding_type == finding_type)
    if severity:
        query = query.where(ReconciliationFinding.severity == severity)
    if player_id:
        query = query.where(ReconciliationFinding.player_id == player_id)
    if tx_id:
        query = query.where(ReconciliationFinding.tx_id == tx_id)
    if provider_event_id:
        query = query.where(ReconciliationFinding.provider_event_id == provider_event_id)

    total_query = query.with_only_columns(func.count()).order_by(None)
    total = (await session.execute(total_query)).scalar() or 0

    query = query.order_by(ReconciliationFinding.created_at.desc()).offset(offset).limit(limit)
    items = (await session.execute(query)).scalars().all()

    return {
        "items": [
            {
                "id": f.id,
                "provider": f.provider,
                "tenant_id": f.tenant_id,
                "player_id": f.player_id,
                "tx_id": f.tx_id,
                "provider_event_id": f.provider_event_id,
                "provider_ref": f.provider_ref,
                "finding_type": f.finding_type,
                "severity": f.severity,
                "status": f.status,
                "message": f.message,
                "created_at": f.created_at,
                "updated_at": f.updated_at,
            }
            for f in items
        ],
        "meta": {"total": total, "limit": limit, "offset": offset},
    }


@router.post("/reconciliation/run")
async def run_reconciliation(
    request: Request,
    provider: str = "mockpsp",
    tenant_id: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    """Trigger reconciliation job for a given provider/tenant.

    This is an admin-only endpoint intended for ops usage.
    """

    effective_tenant_id = tenant_id or await get_current_tenant_id(
        request, current_admin, session=session
    )

    from app.jobs.reconcile_psp import reconcile_mockpsp_vs_ledger

    if provider != "mockpsp":
        raise HTTPException(status_code=400, detail={"error_code": "UNSUPPORTED_PROVIDER"})

    await reconcile_mockpsp_vs_ledger(session, tenant_id=effective_tenant_id)

    return {"status": "ok"}


@router.post("/reconciliation/findings/{finding_id}/resolve")
async def resolve_reconciliation_finding(
    finding_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    """Mark a reconciliation finding as RESOLVED.

    - Admin auth required.
    - If finding.tenant_id is set, it must match the admin's tenant.
    - If tenant_id is None, allow resolve but rely on audit/logs for tracking.
    """

    effective_tenant_id = await get_current_tenant_id(
        request, current_admin, session=session
    )

    finding = await session.get(ReconciliationFinding, finding_id)
    if not finding:
        raise HTTPException(status_code=404, detail={"error_code": "FINDING_NOT_FOUND"})

    if finding.tenant_id and finding.tenant_id != effective_tenant_id:
        raise HTTPException(status_code=403, detail={"error_code": "FORBIDDEN"})

    finding.status = "RESOLVED"
    from datetime import datetime as dt

    finding.updated_at = dt.utcnow()
    session.add(finding)
    await session.commit()
    await session.refresh(finding)

    return {"id": finding.id, "status": finding.status}
