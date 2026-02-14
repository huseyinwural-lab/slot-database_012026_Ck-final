from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from typing import Dict, Any

from app.core.database import get_session
from app.models.sql_models import Transaction, AdminUser, Player
from app.utils.auth import get_current_admin
from app.services.audit import audit
from app.services.transaction_state_machine import transition_transaction, STATE_APPROVED, STATE_PAID, STATE_REJECTED
from app.services.wallet_ledger import apply_wallet_delta_with_ledger

router = APIRouter(prefix="/api/v1/admin/withdrawals", tags=["admin_withdrawals"])

@router.get("/", response_model=Dict[str, Any])
async def list_withdrawals(
    status: str = "requested",
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    # Only show requested/under_review by default or as filtered
    query = select(Transaction).where(
        Transaction.tenant_id == current_admin.tenant_id,
        Transaction.type == "withdrawal"
    )
    
    if status:
        # Support comma separated
        statuses = status.split(",")
        query = query.where(Transaction.state.in_(statuses))
    
    query = query.order_by(Transaction.created_at.desc())
    
    result = await session.execute(query)
    items = result.scalars().all()
    
    return {"items": items, "total": len(items)}

@router.post("/{tx_id}/approve")
async def approve_withdrawal(
    tx_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tx = await session.get(Transaction, tx_id)
    if not tx or tx.tenant_id != current_admin.tenant_id:
        raise HTTPException(404, "Transaction not found")
        
    if tx.state not in ["requested", "under_review"]:
        raise HTTPException(400, f"Invalid state for approval: {tx.state}")

    # Move to APPROVED (Payout ready)
    old_state = tx.state
    transition_transaction(tx, STATE_APPROVED)
    
    # Audit
    await audit.log_event(
        session=session,
        request_id=request.headers.get("X-Request-Id"),
        actor_user_id=current_admin.id,
        tenant_id=tx.tenant_id,
        action="FIN_WITHDRAW_APPROVED",
        resource_type="wallet_withdraw",
        resource_id=tx.id,
        result="success",
        details={"old_state": old_state, "new_state": tx.state, "amount": tx.amount},
    )
    
    # Auto-payout simulation (For P0, we assume manual payout or auto-trigger here)
    # Moving to PAID to release funds from hold (burn them)
    # In real flow: Approved -> Payout Service -> Paid
    # For now, let's complete it immediately for E2E
    
    # Transition to PAID
    transition_transaction(tx, STATE_PAID)
    tx.status = "completed"
    
    # Ledger: Burn held funds (Locked -> Out)
    # Delta: Available 0 (already deducted), Held -Amount
    await apply_wallet_delta_with_ledger(
        session,
        tenant_id=tx.tenant_id,
        player_id=tx.player_id,
        tx_id=tx.id,
        event_type="withdraw_paid",
        delta_available=0.0,
        delta_held=-float(tx.amount),
        currency=tx.currency,
        idempotency_key=f"payout:{tx.id}",
    )
    
    await session.commit()
    return {"ok": True, "transaction": tx}

@router.post("/{tx_id}/reject")
async def reject_withdrawal(
    tx_id: str,
    request: Request,
    payload: Dict[str, str], # {"reason": "..."}
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    reason = payload.get("reason")
    if not reason:
        raise HTTPException(400, "Rejection reason is required")

    tx = await session.get(Transaction, tx_id)
    if not tx or tx.tenant_id != current_admin.tenant_id:
        raise HTTPException(404, "Transaction not found")

    if tx.state in ["paid", "rejected", "cancelled"]:
        raise HTTPException(400, "Cannot reject final state")

    old_state = tx.state
    tx.review_reason = reason
    transition_transaction(tx, STATE_REJECTED)
    tx.status = "failed" # Final status

    # Ledger: Return held funds to available (Refund)
    # Delta: Available +Amount, Held -Amount
    await apply_wallet_delta_with_ledger(
        session,
        tenant_id=tx.tenant_id,
        player_id=tx.player_id,
        tx_id=tx.id,
        event_type="withdraw_rejected",
        delta_available=+float(tx.amount),
        delta_held=-float(tx.amount),
        currency=tx.currency,
        idempotency_key=f"reject:{tx.id}",
    )

    # Audit
    await audit.log_event(
        session=session,
        request_id=request.headers.get("X-Request-Id"),
        actor_user_id=current_admin.id,
        tenant_id=tx.tenant_id,
        action="FIN_WITHDRAW_REJECTED",
        resource_type="wallet_withdraw",
        resource_id=tx.id,
        result="success",
        details={"old_state": old_state, "new_state": tx.state, "reason": reason},
    )

    await session.commit()
    return {"ok": True, "transaction": tx}
