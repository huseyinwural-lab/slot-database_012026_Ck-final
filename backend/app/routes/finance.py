from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlmodel import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime, timezone


from app.core.errors import AppError
from app.models.sql_models import Transaction, Player, PayoutAttempt
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

        # held rollback: held -= amount, available += amount via canonical service
        from app.services.wallet_ledger import apply_wallet_delta_with_ledger

        await apply_wallet_delta_with_ledger(
            session,
            tenant_id=tenant_id,
            player_id=tx.player_id,
            tx_id=str(tx.id),
            event_type="withdraw_rejected",
            delta_available=float(tx.amount),
            delta_held=-float(tx.amount),
            currency=tx.currency or "USD",
            idempotency_key=f"withdraw_review:reject:{tx.id}",
        )

    tx.reviewed_by = current_admin.id
    tx.reviewed_at = datetime.now(timezone.utc)

    session.add(tx)

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

    session.add(player)
    session.add(tx)

    # PSP integration (MockPSP): payout call (no direct balance delta here)
    from app.services.psp import get_psp
    from app.services.psp.psp_interface import build_psp_idem_key
    from app.services.wallet_ledger import apply_wallet_delta_with_ledger

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

    # held -= amount, total düşer – via canonical wallet+ledger service
    await apply_wallet_delta_with_ledger(
        session,
        tenant_id=tenant_id,
        player_id=tx.player_id,
        tx_id=str(tx.id),
        event_type="withdraw_paid",
        delta_available=0.0,
        delta_held=-float(tx.amount),
        currency=tx.currency or "USD",
        idempotency_key=f"withdraw_mark_paid:{tx.id}",
        provider=psp_res.provider,
        provider_ref=psp_res.provider_ref,
        provider_event_id=psp_res.provider_event_id,
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


@router.post("/withdrawals/{tx_id}/payout")
async def start_payout(
    request: Request,
    tx_id: str,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    """Start a payout attempt for an approved withdrawal (idempotent).

    Semantics (P0-5 P3):
    - First call from state=approved creates a PayoutAttempt(status=pending),
      transitions withdrawal -> payout_pending and triggers MockPSP payout.
    - PSP outcome:
        * success  -> ledger withdraw_paid + held -= amount, state -> paid
        * fail     -> NO ledger, held unchanged, state -> payout_failed
    - Replays with the same Idempotency-Key are safe no-ops that return the
      existing attempt + transaction without double-debit.
    """

    from app.services.transaction_state_machine import transition_transaction
    from app.services.psp import get_psp
    from app.services.psp.psp_interface import build_psp_idem_key, PSPStatus
    from app.services.wallet_ledger import apply_wallet_delta_with_ledger

    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    request_id = getattr(request.state, "request_id", "unknown")
    ip = request.client.host if request.client else None

    idem_key = request.headers.get("Idempotency-Key")
    if not idem_key:
        raise HTTPException(status_code=400, detail={"error_code": "IDEMPOTENCY_KEY_REQUIRED"})

    # Load withdrawal transaction
    stmt = select(Transaction).where(
        Transaction.id == tx_id,
        Transaction.tenant_id == tenant_id,
        Transaction.type == "withdrawal",
    )
    tx = (await session.execute(stmt)).scalars().first()
    if not tx:
        raise HTTPException(status_code=404, detail={"error_code": "TX_NOT_FOUND"})

    # Idempotent behaviour based on attempt + tx state
    pa_stmt = select(PayoutAttempt).where(
        PayoutAttempt.withdraw_tx_id == tx_id,
        PayoutAttempt.idempotency_key == idem_key,
    )
    existing_attempt = (await session.execute(pa_stmt)).scalars().first()

    if existing_attempt:
        # If tx is already in a terminal state for this flow, treat as replay.
        if tx.state in {"paid", "payout_failed"}:
            # Audit idempotent hit
            request_id = getattr(request.state, "request_id", "unknown")
            ip = request.client.host if request.client else None
            await audit.log_event(
                session=session,
                request_id=request_id,
                actor_user_id=str(current_admin.id),
                tenant_id=tenant_id,
                action="FIN_IDEMPOTENCY_HIT",
                resource_type="wallet_payout",
                resource_id=tx.id,
                result="success",
                details={
                    "tx_id": tx.id,
                    "payout_attempt_id": existing_attempt.id,
                    "idempotency_key": idem_key,
                    "state": tx.state,
                },
                ip_address=ip,
            )
            await session.commit()
            return {"transaction": tx, "payout_attempt": existing_attempt}
        # If still pending, also treat as replay/no-op at this layer; webhook or
        # subsequent calls will drive it to terminal states.
        if tx.state == "payout_pending":
            return {"transaction": tx, "payout_attempt": existing_attempt}

    # Enforce state precondition for first call: must be approved
    if tx.state != "approved":
        raise HTTPException(
            status_code=409,
            detail={
                "error_code": "INVALID_STATE_TRANSITION",
                "from_state": tx.state,
                "to_state": "payout_pending",
                "tx_type": "withdrawal",
            },
        )

    # Determine mock outcome: default success, override via header in dev/test
    outcome = request.headers.get("X-Mock-Outcome", "success").strip().lower()
    if outcome not in {"success", "fail"}:
        outcome = "success"

    # Audit: payout started (only on the path where we actually trigger PSP)
    await audit.log_event(
        session=session,
        request_id=request_id,
        actor_user_id=str(current_admin.id),
        tenant_id=tenant_id,
        action="FIN_PAYOUT_STARTED",
        resource_type="wallet_payout",
        resource_id=tx.id,
        result="pending",
        details={
            "tx_id": tx.id,
            "player_id": tx.player_id,
            "amount": tx.amount,
            "currency": tx.currency,
            "idempotency_key": idem_key,
            "outcome_hint": outcome,
        },
        ip_address=ip,
    )

    psp = get_psp()
    psp_idem_key = build_psp_idem_key(str(tx.id))

    # For tests, allow deterministic fail via MockPSP override
    if outcome == "fail":
        try:
            psp.register_outcome_override(psp_idem_key, "fail")  # type: ignore[attr-defined]
        except Exception:
            # In prod, ignore if override is not supported
            pass

    # Trigger PSP payout
    psp_res = await psp.payout_withdrawal(
        tx_id=str(tx.id),
        tenant_id=tenant_id,
        player_id=tx.player_id,
        amount=float(tx.amount),
        currency=tx.currency or "USD",
        psp_idem_key=psp_idem_key,
    )

    # Create or reuse attempt row
    if existing_attempt:
        attempt = existing_attempt
    else:
        attempt = PayoutAttempt(
            withdraw_tx_id=tx.id,
            tenant_id=tenant_id,
            provider=psp_res.provider,
            provider_event_id=psp_res.provider_event_id,
            idempotency_key=idem_key,
            status="pending",
        )
        session.add(attempt)

    # Update attempt status based on PSP result
    if psp_res.status == PSPStatus.PAID:
        attempt.status = "succeeded"
        attempt.error_code = None
    else:
        attempt.status = "failed"
        attempt.error_code = "PSP_PAYOUT_FAILED"

    # Apply state + ledger transitions under a single transaction
    player = await session.get(Player, tx.player_id)
    if not player:
        raise HTTPException(status_code=404, detail={"error_code": "PLAYER_NOT_FOUND"})

    # First time from approved -> payout_pending
    if tx.state == "approved":
        transition_transaction(tx, "payout_pending")

    if psp_res.status == PSPStatus.PAID:
        # Success path: payout_pending -> paid + single withdraw_paid ledger
        transition_transaction(tx, "paid")

        await apply_wallet_delta_with_ledger(
            session,
            tenant_id=tenant_id,
            player_id=tx.player_id,
            tx_id=str(tx.id),
            event_type="withdraw_paid",
            delta_available=0.0,
            delta_held=-float(tx.amount),
            currency=tx.currency or "USD",
            idempotency_key=f"withdraw_payout_paid:{tx.id}:{idem_key}",
            provider=psp_res.provider,
            provider_ref=psp_res.provider_ref,
            provider_event_id=psp_res.provider_event_id,
        )
    else:
        # Fail path: payout_pending -> payout_failed, NO ledger write, held unchanged
        transition_transaction(tx, "payout_failed")

    # Persist changes
    session.add(tx)
    session.add(attempt)
    await session.commit()
    await session.refresh(tx)
    await session.refresh(attempt)

    return {"transaction": tx, "payout_attempt": attempt}



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
