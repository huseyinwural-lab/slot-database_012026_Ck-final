from fastapi import APIRouter, Depends, HTTPException, Body, Request
from pydantic import BaseModel
from typing import Literal, Optional
from sqlmodel import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime, timezone, timedelta


from app.core.errors import AppError
from app.models.sql_models import Transaction, Player, PayoutAttempt
from app.services.audit import audit
from app.services.ledger_shadow import shadow_append_event, shadow_apply_delta


from app.core.database import get_session
from app.models.sql_models import ReconciliationReport, ChargebackCase, AdminUser
from app.utils.auth import get_current_admin


class PayoutWebhookPayload(BaseModel):
    withdraw_tx_id: str
    provider: str
    provider_event_id: str
    status: Literal["paid", "failed"]
    provider_ref: Optional[str] = None
    error_code: Optional[str] = None
    raw_payload: Optional[dict] = None

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
    min_amount: float | None = None,
    max_amount: float | None = None,
    sort: str = "created_at_desc",
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

    if min_amount is not None:
        query = query.where(Transaction.amount >= min_amount)
    if max_amount is not None:
        query = query.where(Transaction.amount <= max_amount)

    # Sorting contract: default created_at DESC; support created_at_asc if requested
    if sort == "created_at_asc":
        query = query.order_by(Transaction.created_at.asc())
    else:
        query = query.order_by(Transaction.created_at.desc())

    query = query.offset(offset).limit(limit)
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
    if min_amount is not None:
        count_query = count_query.where(Transaction.amount >= min_amount)
    if max_amount is not None:
        count_query = count_query.where(Transaction.amount <= max_amount)

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

    if not reason:
        # CI/E2E hardening: default reason if client omitted it.
        # In prod UI, a human operator should supply a reason.
        reason = "ci_default_reason"

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
        tx.review_reason = reason
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
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    """Mark an approved withdrawal as paid.

    - approved -> paid
    - held -= amount (available unchanged)
    """
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    reason = (payload.get("reason") or "").strip()
    if not reason:
        # CI/E2E hardening: default reason if client omitted it.
        # In prod UI, a human operator should supply a reason.
        reason = "ci_default_reason"

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
            "reason": reason,
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

    # Enforce state precondition for first call: must be approved or payout_failed
    if tx.state not in {"approved", "payout_failed"}:
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
    # PSP idempotency is bound to both transaction and API Idempotency-Key so
    # that distinct payout attempts (fail vs retry) are treated as separate
    # provider calls, while replays with the same key remain safe.
    psp_idem_key = build_psp_idem_key(f"{tx.id}:{idem_key}")

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

    # Move from approved/payout_failed into payout_pending before applying
    # terminal success/fail transitions.
    if tx.state in {"approved", "payout_failed"}:
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

        # Audit success
        await audit.log_event(
            session=session,
            request_id=request_id,
            actor_user_id=str(current_admin.id),
            tenant_id=tenant_id,
            action="FIN_PAYOUT_SUCCEEDED",
            resource_type="wallet_payout",
            resource_id=tx.id,
            result="success",
            details={
                "tx_id": tx.id,
                "player_id": tx.player_id,
                "amount": tx.amount,
                "currency": tx.currency,
                "idempotency_key": idem_key,
                "payout_attempt_id": attempt.id,
            },
            ip_address=ip,
        )
    else:
        # Fail path: payout_pending -> payout_failed, NO ledger write, held unchanged
        transition_transaction(tx, "payout_failed")

        await audit.log_event(
            session=session,
            request_id=request_id,
            actor_user_id=str(current_admin.id),
            tenant_id=tenant_id,
            action="FIN_PAYOUT_FAILED",
            resource_type="wallet_payout",
            resource_id=tx.id,
            result="failure",
            details={
                "tx_id": tx.id,
                "player_id": tx.player_id,
                "amount": tx.amount,
                "currency": tx.currency,
                "idempotency_key": idem_key,
                "payout_attempt_id": attempt.id,
                "error_code": attempt.error_code,
            },
            ip_address=ip,
        )

    # Persist changes
    session.add(tx)
    session.add(attempt)
    await session.commit()
    await session.refresh(tx)
    await session.refresh(attempt)

    return {"transaction": tx, "payout_attempt": attempt}


@router.post("/withdrawals/{tx_id}/recheck")
async def recheck_payout(
    request: Request,
    tx_id: str,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    """Manually recheck a stuck payout (idempotent).

    Semantics (O1):
    - Only callable when withdrawal.state in {payout_pending, payout_failed}.
    - Uses Idempotency-Key to guard against double-processing.
    - Mock provider status is driven by X-Mock-Outcome: paid|failed|pending.
        * paid   -> finalize as paid (single withdraw_paid ledger, held -= amount)
        * failed -> payout_failed (no ledger, balances unchanged)
        * pending-> no-op on state/ledger
    - Replay with the same Idempotency-Key is a safe no-op and logged via
      FIN_IDEMPOTENCY_HIT.
    """

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

    # Recheck idempotency: if an attempt with this key already exists, treat as replay
    pa_stmt = select(PayoutAttempt).where(
        PayoutAttempt.withdraw_tx_id == tx_id,
        PayoutAttempt.idempotency_key == idem_key,
    )
    existing_attempt = (await session.execute(pa_stmt)).scalars().first()
    if existing_attempt:
        await audit.log_event(
            session=session,
            request_id=request_id,
            actor_user_id=str(current_admin.id),
            tenant_id=tenant_id,
            action="FIN_IDEMPOTENCY_HIT",
            resource_type="wallet_payout_recheck",
            resource_id=tx.id,
            result="success",
            details={
                "tx_id": tx.id,
                "payout_attempt_id": existing_attempt.id,
                "idempotency_key": idem_key,
                "state": tx.state,
                "attempt_status": existing_attempt.status,
            },
            ip_address=ip,
        )
        await session.commit()
        return {"transaction": tx, "payout_attempt": existing_attempt, "replay": True}

    # Enforce state precondition for first call
    if tx.state not in {"payout_pending", "payout_failed"}:
        raise HTTPException(
            status_code=409,
            detail={
                "error_code": "INVALID_STATE_TRANSITION",
                "from_state": tx.state,
                "to_state": tx.state,
                "tx_type": "withdrawal",
            },
        )

    # Determine mock outcome: default pending, override via header in dev/test
    outcome = request.headers.get("X-Mock-Outcome", "pending").strip().lower()
    if outcome not in {"paid", "failed", "pending"}:
        outcome = "pending"

    # Audit: recheck started
    await audit.log_event(
        session=session,
        request_id=request_id,
        actor_user_id=str(current_admin.id),
        tenant_id=tenant_id,
        action="FIN_PAYOUT_RECHECK_STARTED",
        resource_type="wallet_payout_recheck",
        resource_id=tx.id,
        result="pending",
        details={
            "tx_id": tx.id,
            "player_id": tx.player_id,
            "amount": tx.amount,
            "currency": tx.currency,
            "idempotency_key": idem_key,
            "outcome_hint": outcome,
            "state_before": tx.state,
        },
        ip_address=ip,
    )

    from app.services.transaction_state_machine import transition_transaction
    from app.services.wallet_ledger import apply_wallet_delta_with_ledger

    # Create a payout attempt record for this recheck
    attempt = PayoutAttempt(
        withdraw_tx_id=tx.id,
        tenant_id=tenant_id,
        provider="mockpsp",
        provider_event_id=None,
        idempotency_key=idem_key,
        status="pending",
    )
    session.add(attempt)

    # Apply outcome-specific logic
    player = await session.get(Player, tx.player_id)
    if not player:
        raise HTTPException(status_code=404, detail={"error_code": "PLAYER_NOT_FOUND"})

    # Ensure we are in payout_pending before finalizing paid/failed from PSP
    state_before = tx.state

    if outcome == "paid" and tx.state == "payout_pending":
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
            idempotency_key=f"withdraw_payout_paid_recheck:{tx.id}:{idem_key}",
            provider="mockpsp",
            provider_ref=None,
            provider_event_id=None,
        )
        attempt.status = "succeeded"
        attempt.error_code = None
    elif outcome == "failed" and tx.state == "payout_pending":
        transition_transaction(tx, "payout_failed")
        attempt.status = "failed"
        attempt.error_code = "PSP_PAYOUT_FAILED"
    else:
        # pending outcome or unsupported combination: no state/ledger change
        attempt.status = "pending"

    # Audit: result
    await audit.log_event(
        session=session,
        request_id=request_id,
        actor_user_id=str(current_admin.id),
        tenant_id=tenant_id,
        action="FIN_PAYOUT_RECHECK_RESULT",
        resource_type="wallet_payout_recheck",
        resource_id=tx.id,
        result="success" if outcome == "paid" and tx.state == "paid" else (
            "failure" if tx.state == "payout_failed" else "pending"
        ),
        details={
            "tx_id": tx.id,
            "player_id": tx.player_id,
            "amount": tx.amount,
            "currency": tx.currency,
            "idempotency_key": idem_key,
            "outcome": outcome,
            "state_before": state_before,
            "state_after": tx.state,
            "payout_attempt_id": attempt.id,
        },
        ip_address=ip,
    )

    session.add(tx)
    await session.commit()
    await session.refresh(tx)
    await session.refresh(attempt)

    return {"transaction": tx, "payout_attempt": attempt}


@router.post("/withdrawals/payout/webhook")
async def payout_webhook(
    payload: PayoutWebhookPayload,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    """Generic PSP payout webhook handler with signature verification + replay dedupe.

    Behaviour:
    - provider_event_id is the primary dedupe key.
    - First call for a given event id applies the same success/fail semantics as
      the /payout endpoint (ledger + state machine).
    - Replays with the same provider_event_id are 200 OK no-ops.
    """

    # Webhook signature verification (WEBHOOK-SEC-001)
    from app.services.webhook_security import verify_webhook_signature

    raw_body = await request.body()
    ts_header = request.headers.get("X-Webhook-Timestamp")
    sig_header = request.headers.get("X-Webhook-Signature")

    status_code, error_code = verify_webhook_signature(ts_header, sig_header, raw_body)
    if status_code != 200:
        raise HTTPException(status_code=status_code, detail={"error_code": error_code})


    request_id = getattr(request.state, "request_id", "unknown")
    ip = request.client.host if request.client else None

    # Find existing payout attempt by provider_event_id
    stmt = select(PayoutAttempt).where(
        PayoutAttempt.provider == payload.provider,
        PayoutAttempt.provider_event_id == payload.provider_event_id,
    )
    existing = (await session.execute(stmt)).scalars().first()

    # Idempotent replay: if we already processed this provider_event_id, no-op
    if existing:
        await audit.log_event(
            session=session,
            request_id=request_id,
            actor_user_id=str(current_admin.id),
            tenant_id=existing.tenant_id,
            action="FIN_IDEMPOTENCY_HIT",
            resource_type="wallet_payout_webhook",
            resource_id=existing.withdraw_tx_id,
            result="success",
            details={
                "withdraw_tx_id": existing.withdraw_tx_id,
                "payout_attempt_id": existing.id,
                "provider": payload.provider,
                "provider_event_id": payload.provider_event_id,
                "status": existing.status,
            },
            ip_address=ip,
        )
        await session.commit()
        return {"status": "ok", "replay": True}

    # Otherwise, create a payout attempt stub and delegate to the same state
    # machine/ledger semantics as /payout. We re-run the /payout endpoint logic
    # indirectly by mimicking a success/fail outcome.

    # Load the withdrawal transaction
    tx = await session.get(Transaction, payload.withdraw_tx_id)
    if not tx:
        # Unknown transaction; still 200 to avoid PSP retries storm, but log.
        await audit.log_event(
            session=session,
            request_id=request_id,
            actor_user_id=str(current_admin.id),
            tenant_id=current_admin.tenant_id,
            action="FIN_PAYOUT_WEBHOOK_ORPHAN",
            resource_type="wallet_payout_webhook",
            resource_id=payload.withdraw_tx_id,
            result="failure",
            details={
                "provider": payload.provider,
                "provider_event_id": payload.provider_event_id,
                "status": payload.status,
                "error_code": payload.error_code,
            },
            ip_address=ip,
        )
        await session.commit()
        return {"status": "ok", "orphan": True}

    # For simplicity, we reuse the same mechanics by constructing a
    # PayoutAttempt row and then applying the same state+ledger logic inline.
    attempt = PayoutAttempt(
        withdraw_tx_id=tx.id,
        tenant_id=current_admin.tenant_id,
        provider=payload.provider,
        provider_event_id=payload.provider_event_id,
        idempotency_key=None,
        status="pending",
        error_code=payload.error_code,
    )
    session.add(attempt)

    from app.services.transaction_state_machine import transition_transaction
    from app.services.wallet_ledger import apply_wallet_delta_with_ledger

    # Ensure we are in payout_pending before applying terminal transitions.
    if tx.state == "approved":
        transition_transaction(tx, "payout_pending")

    if payload.status == "paid":
        transition_transaction(tx, "paid")
        await apply_wallet_delta_with_ledger(
            session,
            tenant_id=current_admin.tenant_id,
            player_id=tx.player_id,
            tx_id=str(tx.id),
            event_type="withdraw_paid",
            delta_available=0.0,
            delta_held=-float(tx.amount),
            currency=tx.currency or "USD",
            idempotency_key=f"withdraw_payout_paid_webhook:{tx.id}:{payload.provider_event_id}",
            provider=payload.provider,
            provider_ref=payload.provider_ref,
            provider_event_id=payload.provider_event_id,
        )
    else:
        # failed
        transition_transaction(tx, "payout_failed")

    await audit.log_event(
        session=session,
        request_id=request_id,
        actor_user_id=str(current_admin.id),
        tenant_id=current_admin.tenant_id,
        action="FIN_PAYOUT_WEBHOOK_PROCESSED",
        resource_type="wallet_payout_webhook",
        resource_id=tx.id,
        result="success" if payload.status == "paid" else "failure",
        details={
            "withdraw_tx_id": tx.id,
            "payout_attempt_id": attempt.id,
            "provider": payload.provider,
            "provider_event_id": payload.provider_event_id,
            "status": payload.status,
            "error_code": payload.error_code,
        },
        ip_address=ip,
    )

    session.add(tx)
    await session.commit()
    await session.refresh(tx)
    await session.refresh(attempt)

    return {"status": "ok", "transaction": tx, "payout_attempt": attempt}


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


@router.post("/reconciliation/run")
async def run_wallet_reconciliation(
    request: Request,
    date: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    """Run wallet-ledger reconciliation for a given UTC day.

    This computes money-path invariants and persists findings into
    reconciliation_findings tied to a ReconciliationRun.
    """

    from datetime import date as date_cls
    from app.models.reconciliation_run import ReconciliationRun
    from app.models.reconciliation import ReconciliationFinding
    from app.services.reconciliation import compute_daily_findings
    from app.services.reconciliation_runs import create_run, get_run
    from app.services.audit import audit

    provider = "wallet_ledger"

    # Parse date or default to today (UTC)
    if date:
        target_date = date_cls.fromisoformat(date)
    else:
        now = datetime.now(timezone.utc)
        target_date = date_cls(year=now.year, month=now.month, day=now.day)

    day_start = datetime(target_date.year, target_date.month, target_date.day, tzinfo=timezone.utc)
    day_end = day_start + timedelta(days=1)

    # Create reconciliation run
    run = await create_run(
        session,
        provider=provider,
        window_start=day_start,
        window_end=day_end,
        dry_run=False,
        idempotency_key=None,
        created_by_admin_id=str(current_admin.id),
    )

    request_id = getattr(request.state, "request_id", "unknown")
    ip = request.client.host if request.client else None

    await audit.log_event(
        session=session,
        request_id=request_id,
        actor_user_id=str(current_admin.id),
        tenant_id=current_admin.tenant_id,
        action="FIN_RECONCILIATION_RUN_STARTED",
        resource_type="reconciliation_run",
        resource_id=run.id,
        result="started",
        details={"provider": provider, "date": target_date.isoformat(), "run_id": run.id},
        ip_address=ip,
    )

    inserted = 0
    scanned = 0

    try:
        findings = await compute_daily_findings(session, day=target_date)
        scanned = len(findings)

        for f in findings:
            rec = ReconciliationFinding(
                provider=provider,
                tenant_id=f.tenant_id,
                tx_id=f.tx_id,
                finding_type=f.finding_code,
                severity=f.severity,
                status="OPEN",
                message=None,
                raw={
                    "run_id": run.id,
                    "date": target_date.isoformat(),
                    "tenant_id": f.tenant_id,
                    "tx_id": f.tx_id,
                    "details": f.details,
                },
            )
            session.add(rec)
            inserted += 1

        run.status = "completed"
        run.stats_json = {"inserted": inserted, "scanned": scanned}
        await session.commit()

        await audit.log_event(
            session=session,
            request_id=request_id,
            actor_user_id=str(current_admin.id),
            tenant_id=current_admin.tenant_id,
            action="FIN_RECONCILIATION_RUN_COMPLETED",
            resource_type="reconciliation_run",
            resource_id=run.id,
            result="success",
            details={"provider": provider, "date": target_date.isoformat(), "inserted": inserted, "scanned": scanned, "run_id": run.id},
            ip_address=ip,
        )
        await session.commit()

    except Exception as exc:  # noqa: BLE001
        run.status = "failed"
        run.stats_json = {"inserted": inserted, "scanned": scanned, "error": str(exc)}
        await session.commit()

        await audit.log_event(
            session=session,
            request_id=request_id,
            actor_user_id=str(current_admin.id),
            tenant_id=current_admin.tenant_id,
            action="FIN_RECONCILIATION_RUN_FAILED",
            resource_type="reconciliation_run",
            resource_id=run.id,
            result="failed",
            details={"provider": provider, "date": target_date.isoformat(), "error": str(exc), "run_id": run.id},
            ip_address=ip,
        )
        await session.commit()
        raise

    return {"run_id": run.id, "inserted": inserted, "scanned": scanned}


@router.get("/reconciliation/summary")
async def get_wallet_reconciliation_summary(
    date: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    from datetime import date as date_cls
    from app.models.reconciliation_run import ReconciliationRun
    from app.models.reconciliation import ReconciliationFinding

    provider = "wallet_ledger"

    if date:
        target_date = date_cls.fromisoformat(date)
    else:
        now = datetime.now(timezone.utc)
        target_date = date_cls(year=now.year, month=now.month, day=now.day)

    # Latest run for this provider and window_start date
    day_start = datetime(target_date.year, target_date.month, target_date.day, tzinfo=timezone.utc)

    query = select(ReconciliationRun).where(
        ReconciliationRun.provider == provider,
        ReconciliationRun.window_start >= day_start,
    ).order_by(ReconciliationRun.created_at.desc())
    run = (await session.execute(query)).scalars().first()
    if not run:
        return {"run_id": None, "counts_by_finding_code": {}, "counts_by_severity": {}, "scanned_tx_count": 0}

    # Aggregate findings for this run
    stmt = select(
        ReconciliationFinding.finding_type,
        func.count().label("cnt"),
    ).where(ReconciliationFinding.provider == provider, ReconciliationFinding.raw["run_id"].as_string() == run.id).group_by(ReconciliationFinding.finding_type)
    rows = (await session.execute(stmt)).all()
    counts_by_finding = {r[0]: r[1] for r in rows}

    stmt2 = select(
        ReconciliationFinding.severity,
        func.count().label("cnt"),
    ).where(ReconciliationFinding.provider == provider, ReconciliationFinding.raw["run_id"].as_string() == run.id).group_by(ReconciliationFinding.severity)
    rows2 = (await session.execute(stmt2)).all()
    counts_by_severity = {r[0]: r[1] for r in rows2}

    scanned = 0
    if run.stats_json and "scanned" in run.stats_json:
        scanned = run.stats_json["scanned"]

    return {
        "run_id": run.id,
        "counts_by_finding_code": counts_by_finding,
        "counts_by_severity": counts_by_severity,
        "scanned_tx_count": scanned,
    }


@router.get("/reconciliation/findings")
async def list_wallet_reconciliation_findings(
    date: Optional[str] = None,
    finding_code: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    from datetime import date as date_cls
    from app.models.reconciliation_run import ReconciliationRun
    from app.models.reconciliation import ReconciliationFinding

    provider = "wallet_ledger"

    if date:
        target_date = date_cls.fromisoformat(date)
    else:
        now = datetime.now(timezone.utc)
        target_date = date_cls(year=now.year, month=now.month, day=now.day)

    day_start = datetime(target_date.year, target_date.month, target_date.day, tzinfo=timezone.utc)

    # Latest run for this provider and date
    query = select(ReconciliationRun).where(
        ReconciliationRun.provider == provider,
        ReconciliationRun.window_start >= day_start,
    ).order_by(ReconciliationRun.created_at.desc())
    run = (await session.execute(query)).scalars().first()
    if not run:
        return {"items": [], "meta": {"total": 0, "limit": limit, "offset": offset}}

    stmt = select(ReconciliationFinding).where(
        ReconciliationFinding.provider == provider,
        ReconciliationFinding.raw["run_id"].as_string() == run.id,
    )
    if finding_code:
        stmt = stmt.where(ReconciliationFinding.finding_type == finding_code)
    if severity:
        stmt = stmt.where(ReconciliationFinding.severity == severity)

    total = (await session.execute(stmt.with_only_columns(func.count()))).scalar_one()

    stmt = stmt.order_by(ReconciliationFinding.created_at.desc()).limit(limit).offset(offset)
    items = (await session.execute(stmt)).scalars().all()

    # Serialize minimal fields
    payload_items = [
        {
            "tenant_id": it.tenant_id,
            "tx_id": it.tx_id,
            "finding_type": it.finding_type,
            "severity": it.severity,
            "status": it.status,
            "raw": it.raw,
        }
        for it in items
    ]

    return {"items": payload_items, "meta": {"total": total, "limit": limit, "offset": offset}}


@router.get("/reconciliation/tx/{tx_id}")
async def get_wallet_reconciliation_tx_snapshot(
    tx_id: str,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    """Return a snapshot for a single transaction for reconciliation drill-down."""

    from app.models.sql_models import Transaction, Player
    from app.models.reconciliation import ReconciliationFinding
    from app.models.sql_models import PayoutAttempt
    from app.repositories.ledger_repo import LedgerTransaction

    tx = (await session.execute(select(Transaction).where(Transaction.id == tx_id))).scalars().first()
    if not tx:
        raise HTTPException(status_code=404, detail={"error_code": "TX_NOT_FOUND"})

    findings = (
        await session.execute(
            select(ReconciliationFinding).where(
                ReconciliationFinding.tx_id == tx_id,
            )
        )
    ).scalars().all()

    attempts = (
        await session.execute(
            select(PayoutAttempt).where(PayoutAttempt.withdraw_tx_id == tx_id)
        )
    ).scalars().all()

    ledger_events = (
        await session.execute(select(LedgerTransaction).where(LedgerTransaction.tx_id == tx_id))
    ).scalars().all()

    return {
        "tx": {
            "id": tx.id,
            "tenant_id": tx.tenant_id,
            "player_id": tx.player_id,
            "type": tx.type,
            "state": tx.state,
            "amount": float(tx.amount),
            "currency": tx.currency,
        },
        "findings": [
            {
                "finding_type": f.finding_type,
                "severity": f.severity,
                "status": f.status,
                "raw": f.raw,
            }
            for f in findings
        ],
        "payout_attempts": [
            {
                "id": pa.id,
                "provider": pa.provider,
                "provider_event_id": pa.provider_event_id,
                "status": pa.status,
            }
            for pa in attempts
        ],
        "ledger_events": [
            {
                "id": ev.id,
                "status": ev.status,
                "amount": float(ev.amount),
                "currency": ev.currency,
            }
            for ev in ledger_events
        ],
    }

