from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
import uuid
import logging

from app.core.database import get_session
from app.models.sql_models import Transaction, AdminUser
from app.routes.auth_snippet import get_current_admin
from app.services.wallet_ledger import apply_wallet_delta_with_ledger
from app.services.audit import audit
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/finance/deposits", tags=["finance"])
logger = logging.getLogger(__name__)

class RefundRequest(BaseModel):
    reason: str = Field(..., min_length=5, description="Reason for refund")

@router.post("/{tx_id}/refund")
async def refund_deposit(
    tx_id: str,
    body: RefundRequest,
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    Refund/Reverse a completed deposit.
    Admin only.
    """
    # 1. Fetch TX
    # Use with_for_update to prevent race conditions
    stmt = select(Transaction).where(Transaction.id == tx_id).with_for_update()
    tx = (await session.execute(stmt)).scalars().first()
    
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Audit: Requested
    await audit.log_event(
        session=session,
        request_id=f"req_refund_{tx.id}",
        actor_user_id=str(current_admin.id),
        tenant_id=tx.tenant_id,
        action="FIN_DEPOSIT_REFUND_REQUESTED",
        resource_type="transaction",
        resource_id=tx.id,
        result="pending",
        details={"reason": body.reason}
    )

    # 2. Validation
    if tx.type != "deposit":
        await audit.log_event(
            session=session,
            request_id=f"req_refund_{tx.id}",
            actor_user_id=str(current_admin.id),
            tenant_id=tx.tenant_id,
            action="FIN_DEPOSIT_REFUND_REJECTED",
            resource_type="transaction",
            resource_id=tx.id,
            result="rejected",
            details={"reason": "invalid_type", "type": tx.type}
        )
        await session.commit()
        raise HTTPException(status_code=400, detail="Only deposits can be refunded")
    
    if tx.status == "reversed" or tx.state == "reversed":
        return {"status": "reversed", "tx_id": tx.id, "message": "Already reversed"}

    if tx.status != "completed":
        await audit.log_event(
            session=session,
            request_id=f"req_refund_{tx.id}",
            actor_user_id=str(current_admin.id),
            tenant_id=tx.tenant_id,
            action="FIN_DEPOSIT_REFUND_REJECTED",
            resource_type="transaction",
            resource_id=tx.id,
            result="rejected",
            details={"reason": "invalid_state", "status": tx.status}
        )
        await session.commit()
        raise HTTPException(status_code=400, detail="Transaction is not in completed state")

    # 3. Apply Reversal Ledger
    # Negative delta available
    # New event type: deposit_refunded
    
    try:
        await apply_wallet_delta_with_ledger(
            session,
            tenant_id=tx.tenant_id,
            player_id=tx.player_id,
            tx_id=tx.id,
            event_type="deposit_refunded",
            delta_available= -tx.amount,
            delta_held=0.0,
            currency=tx.currency,
            idempotency_key=f"refund:{tx.id}",
            provider=tx.provider,
            provider_ref=tx.provider_event_id, # Use provider_event_id as ref
            provider_event_id=f"refund_req_{uuid.uuid4()}" # Unique event for the refund action
        )
    except Exception as e:
        logger.error(f"Refund Ledger Error: {e}")
        raise HTTPException(status_code=500, detail="Ledger update failed")

    # 4. Update State
    tx.status = "reversed"
    tx.state = "reversed"
    tx.review_reason = body.reason
    tx.reviewed_by = current_admin.email
    session.add(tx)
    
    # 5. Audit
    # We should log to AuditEvent
    await audit.log_event(
        session=session,
        request_id=f"req_refund_{tx.id}",
        actor_user_id=str(current_admin.id),
        tenant_id=tx.tenant_id,
        action="FIN_DEPOSIT_REFUND_COMPLETED",
        resource_type="transaction",
        resource_id=tx.id,
        result="success",
        details={
            "amount": tx.amount,
            "currency": tx.currency,
            "provider": tx.provider,
            "reason": body.reason
        }
    )
    
    await session.commit()

    return {"status": "reversed", "tx_id": tx.id}
