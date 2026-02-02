from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
import uuid
import logging

from app.core.database import get_session
from app.models.sql_models import Transaction, AdminUser
from app.utils.auth import get_current_admin
from app.services.wallet_ledger import apply_wallet_delta_with_ledger
from app.services.audit import audit

router = APIRouter(prefix="/api/v1/finance", tags=["finance_chargebacks"])
logger = logging.getLogger(__name__)

@router.post("/chargeback")
async def create_chargeback(
    request: Request,
    deposit_tx_id: str = Body(..., embed=True),
    reason: str = Body(..., embed=True),
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    Handle a PSP Chargeback (Forced Refund).
    - Can drive balance into negative.
    - Locks the original deposit TX.
    """
    
    # 1. Fetch Original Deposit
    stmt = select(Transaction).where(Transaction.id == deposit_tx_id, Transaction.type == "deposit")
    tx = (await session.execute(stmt)).scalars().first()
    
    if not tx:
        raise HTTPException(status_code=404, detail="Deposit transaction not found")
        
    if tx.status == "chargeback":
        raise HTTPException(status_code=400, detail="Transaction already charged back")

    # 2. Apply Ledger Delta (Available: -Amount)
    # We allow negative balance here.
    amount = float(tx.amount)
    player_id = tx.player_id
    tenant_id = tx.tenant_id
    currency = tx.currency
    
    cb_tx_id = str(uuid.uuid4())
    
    success = await apply_wallet_delta_with_ledger(
        session,
        tenant_id=tenant_id,
        player_id=player_id,
        tx_id=cb_tx_id,
        event_type="chargeback",
        delta_available=-amount, # Debit
        delta_held=0.0,
        currency=currency,
        idempotency_key=f"chargeback:{deposit_tx_id}",
        allow_negative=True # CRITICAL
    )
    
    if not success:
        raise HTTPException(status_code=409, detail="Chargeback already processed (Idempotency)")

    # 3. Create Chargeback Record (Transaction)
    # We record it as a negative deposit or a special type 'chargeback'
    cb_tx = Transaction(
        id=cb_tx_id,
        tenant_id=tenant_id,
        player_id=player_id,
        type="chargeback",
        amount=amount,
        currency=currency,
        status="completed",
        state="completed",
        provider=tx.provider,
        provider_tx_id=tx.provider_tx_id, # Link to same PSP ref
        metadata_json={
            "original_deposit_id": deposit_tx_id,
            "reason": reason,
            "admin_id": current_admin.id
        }
    )
    session.add(cb_tx)
    
    # 4. Update Original TX State
    tx.status = "chargeback"
    tx.state = "chargeback"
    session.add(tx)
    
    # 5. Audit
    request_id = request.headers.get("X-Request-Id", "unknown")
    ip = request.client.host if request.client else None
    
    await audit.log_event(
        session=session,
        request_id=request_id,
        actor_user_id=current_admin.id,
        tenant_id=tenant_id,
        action="FIN_CHARGEBACK_PROCESSED",
        resource_type="transaction",
        resource_id=deposit_tx_id,
        result="success",
        details={
            "amount": amount,
            "reason": reason,
            "chargeback_tx_id": cb_tx_id
        },
        ip_address=ip
    )
    
    await session.commit()
    
    return {
        "status": "success",
        "chargeback_tx_id": cb_tx_id,
        "amount_debited": amount
    }
