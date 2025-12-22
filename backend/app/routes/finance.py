from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlmodel import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime, timezone


from app.core.errors import AppError
from app.models.sql_models import Transaction, Player
from app.services.audit import audit
from app.services.ledger_shadow import shadow_append_event, shadow_apply_delta


from app.core.database import get_session
from app.models.sql_models import ReconciliationReport, ChargebackCase, AdminUser
from app.utils.auth import get_current_admin
from app.utils.tenant import get_current_tenant_id

router = APIRouter(prefix="/api/v1/finance", tags=["finance_advanced"])

@router.get("/withdrawals")
async def list_withdrawals(
    request: Request,
    state: str | None = None,
    limit: int = 50,
    offset: int = 0,
    player_id: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    query = select(Transaction).where(
        Transaction.tenant_id == tenant_id,
        Transaction.type == "withdrawal",
    )
    if state:
        query = query.where(Transaction.state == state)

    if player_id:
        query = query.where(Transaction.player_id == player_id)

    if date_from:
        query = query.where(Transaction.created_at >= date_from)
    if date_to:
        query = query.where(Transaction.created_at <= date_to)

    query = query.order_by(Transaction.created_at.desc()).offset(offset).limit(limit)
    result = await session.execute(query)
    items = result.scalars().all()

    # Simple offset pagination meta
    count_query = select(func.count()).where(
        Transaction.tenant_id == tenant_id,
        Transaction.type == "withdrawal",
    )
    if state:
        count_query = count_query.where(Transaction.state == state)
    if player_id:
        count_query = count_query.where(Transaction.player_id == player_id)
    if date_from:
        count_query = count_query.where(Transaction.created_at >= date_from)
    if date_to:
        count_query = count_query.where(Transaction.created_at <= date_to)

    total = (await session.execute(count_query)).scalar() or 0

    return {
        "items": [
            {
                "tx_id": tx.id,
                "player_id": tx.player_id,
                "amount": tx.amount,
                "currency": tx.currency,
                "state": tx.state,
                "status": tx.status,
                "created_at": tx.created_at,
                "reviewed_by": tx.reviewed_by,
                "reviewed_at": tx.reviewed_at,
                "balance_after": tx.balance_after,
            }
            for tx in items
        ],
        "meta": {
            "total": total,
            "limit": limit,
            "offset": offset,
        },
    }


@router.post("/withdrawals/{tx_id}/review")
async def review_withdrawal(
    request: Request,
    tx_id: str,
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    """Approve or reject a requested withdrawal.

    - approve: requested -> approved (no balance change)
    - reject: requested -> rejected (held rollback)
    """
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    action = (payload.get("action") or "").strip().lower()
    reason = (payload.get("reason") or "").strip() or None

    if action not in {"approve", "reject"}:
        raise HTTPException(status_code=400, detail={"error_code": "INVALID_ACTION"})

    if action == "reject" and not reason:
        raise HTTPException(status_code=400, detail={"error_code": "REASON_REQUIRED"})

    # Load transaction and player
    stmt = select(Transaction).where(
        Transaction.id == tx_id,
        Transaction.tenant_id == tenant_id,
        Transaction.type == "withdrawal",
    )
    tx = (await session.execute(stmt)).scalars().first()
    if not tx:
        raise HTTPException(status_code=404, detail={"error_code": "TX_NOT_FOUND"})

    from app.services.transaction_state_machine import transition_transaction

    try:
        transition_transaction(tx, "approved" if action == "approve" else "rejected")
    except HTTPException as exc:
        # Bubble up 409 with canonical error code
        raise exc

    player = await session.get(Player, tx.player_id)
    if not player:
        raise HTTPException(status_code=404, detail={"error_code": "PLAYER_NOT_FOUND"})

    before_available = player.balance_real_available
    before_held = player.balance_real_held
    old_state = tx.state

    # Approve/Reject – state change is validated by the shared state machine
    if action == "approve":
        tx.review_reason = None
    else:
        tx.review_reason = reason
        # held rollback: held -= amount, available += amount

    # Shadow ledger event for approve/reject
    if action == "approve":
        await shadow_append_event(
            session=session,
            tenant_id=tenant_id,
            player_id=tx.player_id,
            tx_id=str(tx.id),
            type="withdraw",
            direction="debit",
            amount=float(tx.amount),
            currency=tx.currency or "USD",
            status="withdraw_approved",
            idempotency_key=f"withdraw_review:approve:{tx.id}",
        )
    else:
        res = await shadow_append_event(
            session=session,
            tenant_id=tenant_id,
            player_id=tx.player_id,
            tx_id=str(tx.id),
            type="withdraw",
            direction="debit",
            amount=float(tx.amount),
            currency=tx.currency or "USD",
            status="withdraw_rejected",
            idempotency_key=f"withdraw_review:reject:{tx.id}",
        )
        if res and res.created:
            await shadow_apply_delta(
                session=session,
                tenant_id=tenant_id,
                player_id=tx.player_id,
                currency=tx.currency or "USD",
                delta_available=float(tx.amount),
                delta_pending=-float(tx.amount),
            )

        player.balance_real_held -= tx.amount
        player.balance_real_available += tx.amount

    tx.reviewed_by = current_admin.id
    tx.reviewed_at = datetime.now(timezone.utc)

    session.add(tx)
    session.add(player)

    # Shadow ledger event for approve/reject
    if action == "approve":
        await shadow_append_event(
            session=session,
            tenant_id=tenant_id,
            player_id=tx.player_id,
            tx_id=str(tx.id),
            type="withdraw",
            direction="debit",
            amount=float(tx.amount),
            currency=tx.currency or "USD",
            status="withdraw_approved",
            idempotency_key=f"withdraw_review:approve:{tx.id}",
        )
    else:
        res = await shadow_append_event(
            session=session,
            tenant_id=tenant_id,
            player_id=tx.player_id,
            tx_id=str(tx.id),
            type="withdraw",
            direction="debit",
            amount=float(tx.amount),
            currency=tx.currency or "USD",
            status="withdraw_rejected",
            idempotency_key=f"withdraw_review:reject:{tx.id}",
        )
        if res and res.created:
            await shadow_apply_delta(
                session=session,
                tenant_id=tenant_id,
                player_id=tx.player_id,
                currency=tx.currency or "USD",
                delta_available=float(tx.amount),
                delta_pending=-float(tx.amount),
            )

    request_id = getattr(request.state, "request_id", "unknown")
    ip = request.client.host if request.client else None

    after_available = player.balance_real_available
    after_held = player.balance_real_held

    audit_action = "FIN_WITHDRAW_APPROVED" if action == "approve" else "FIN_WITHDRAW_REJECTED"

    await audit.log_event(
        session=session,
        request_id=request_id,
        actor_user_id=str(current_admin.id),
        tenant_id=tenant_id,
        action=audit_action,
        resource_type="wallet_withdraw",
        resource_id=tx.id,
        result="success",
        details={
            "tx_id": tx.id,
            "player_id": tx.player_id,
            "amount": tx.amount,
            "currency": tx.currency,
            "old_state": old_state,
            "new_state": tx.state,
            "reviewed_by": str(current_admin.id),
            "reviewed_at": tx.reviewed_at.isoformat(),
            "request_id": request_id,
            "balance_available_before": before_available,
            "balance_available_after": after_available,
            "balance_held_before": before_held,
            "balance_held_after": after_held,
            "reason": reason,
        },
        ip_address=ip,
    )

    await session.commit()
    await session.refresh(tx)

    return {"transaction": tx}


@router.post("/withdrawals/{tx_id}/mark-paid")
async def mark_withdrawal_paid(
    request: Request,
    tx_id: str,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    """Mark an approved withdrawal as paid.

    - approved -> paid
    - held -= amount (available unchanged)
    """
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    stmt = select(Transaction).where(
        Transaction.id == tx_id,
        Transaction.tenant_id == tenant_id,
        Transaction.type == "withdrawal",
    )
    tx = (await session.execute(stmt)).scalars().first()
    if not tx:
        raise HTTPException(status_code=404, detail={"error_code": "TX_NOT_FOUND"})

    from app.services.transaction_state_machine import transition_transaction

    try:
        transition_transaction(tx, "paid")
    except HTTPException as exc:
        # Bubble up 409 with canonical error code
        raise exc

    player = await session.get(Player, tx.player_id)
    if not player:
        raise HTTPException(status_code=404, detail={"error_code": "PLAYER_NOT_FOUND"})

    before_available = player.balance_real_available
    before_held = player.balance_real_held
    old_state = tx.state

    # held -= amount, total düşer
    player.balance_real_held -= tx.amount
    tx.state = "paid"

    session.add(player)
    session.add(tx)

    # PSP integration (MockPSP) + ledger: payout + withdraw_paid
    from app.services.psp import get_psp
    from app.services.psp.psp_interface import build_psp_idem_key

    psp = get_psp()
    psp_idem_key = build_psp_idem_key(str(tx.id))

    psp_res = await psp.payout_withdrawal(
        tx_id=str(tx.id),
        tenant_id=tenant_id,
        player_id=tx.player_id,
        amount=float(tx.amount),
        currency=tx.currency or "USD",
        psp_idem_key=psp_idem_key,
    )

    # Shadow ledger: withdraw_paid + finalize pending
    res = await shadow_append_event(
        session=session,
        tenant_id=tenant_id,
        player_id=tx.player_id,
        tx_id=str(tx.id),
        type="withdraw",
        direction="debit",
        amount=float(tx.amount),
        currency=tx.currency or "USD",
        status="withdraw_paid",
        idempotency_key=f"withdraw_mark_paid:{tx.id}",
        provider=psp_res.provider,
        provider_ref=psp_res.provider_ref,
        provider_event_id=psp_res.provider_event_id,
    )
    if res and res.created:
        await shadow_apply_delta(
            session=session,
            tenant_id=tenant_id,
            player_id=tx.player_id,
            currency=tx.currency or "USD",
            delta_available=0.0,
            delta_pending=-float(tx.amount),
        )

    request_id = getattr(request.state, "request_id", "unknown")
    ip = request.client.host if request.client else None

    after_available = player.balance_real_available
    after_held = player.balance_real_held

    await audit.log_event(
        session=session,
        request_id=request_id,
        actor_user_id=str(current_admin.id),
        tenant_id=tenant_id,
        action="FIN_WITHDRAW_MARK_PAID",
        resource_type="wallet_withdraw",
        resource_id=tx.id,
        result="success",
        details={
            "tx_id": tx.id,
            "player_id": tx.player_id,
            "amount": tx.amount,
            "currency": tx.currency,
            "old_state": old_state,
            "new_state": tx.state,
            "reviewed_by": str(current_admin.id),
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
            "request_id": request_id,
            "balance_available_before": before_available,
            "balance_available_after": after_available,
            "balance_held_before": before_held,
            "balance_held_after": after_held,
            "reason": None,
        },
        ip_address=ip,
    )

    await session.commit()
    await session.refresh(tx)

    return {"transaction": tx}


@router.get("/reconciliation")
async def get_reconciliations(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    query = select(ReconciliationReport).where(ReconciliationReport.tenant_id == tenant_id)
    result = await session.execute(query)
    return result.scalars().all()

@router.get("/chargebacks")
async def get_chargebacks(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    query = select(ChargebackCase).where(ChargebackCase.tenant_id == tenant_id)
    result = await session.execute(query)
    return result.scalars().all()
