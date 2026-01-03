from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.utils.auth_player import get_current_player
from app.models.sql_models import PayoutAttempt
from app.services.adyen_psp import AdyenPSP
from app.core.database import get_session
from sqlmodel import select
from config import settings
from datetime import datetime
from typing import Dict, Any
import uuid
import logging
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/payouts", tags=["payouts"])

# NOTE: This endpoint is called by the player app. We require player auth.

# Dependency
def get_adyen_service():
    return AdyenPSP(
        api_key=settings.adyen_api_key or "mock_key",
        merchant_account=settings.adyen_merchant_account or "mock_merchant"
    )

class BankAccount(BaseModel):
    account_holder_name: str
    account_number: str
    bank_code: str
    branch_code: str
    country_code: str
    currency_code: str = "EUR"

class PayoutRequest(BaseModel):
    player_id: str
    amount: int
    currency: str = "EUR"
    bank_account: BankAccount
    player_email: EmailStr
    description: Optional[str] = None

@router.post("/initiate")
async def initiate_payout(
    request: PayoutRequest,
    session = Depends(get_session),
    current_player=Depends(get_current_player),
):
    # Ensure player cannot request withdrawals for other players
    if request.player_id != current_player.id:
        raise HTTPException(status_code=403, detail={"error_code": "UNAUTHORIZED"})

    # Enforce per-tenant daily withdraw limits
    from app.services.tenant_policy_enforcement import ensure_within_tenant_daily_limits

    await ensure_within_tenant_daily_limits(
        session,
        tenant_id=current_player.tenant_id,
        player_id=current_player.id,
        action="withdraw",
        amount=float(amount_major),
        currency=request.currency,
    )

    amount_major = request.amount / 100.0

    bank_acc_adyen = {
        "accountHolderName": request.bank_account.account_holder_name,
        "accountNumber": request.bank_account.account_number,
        "bankCode": request.bank_account.bank_code,
        "branchCode": request.bank_account.branch_code,
        "countryCode": request.bank_account.country_code,
        "currencyCode": request.bank_account.currency_code,
    }

    # Create Transaction
    from app.models.sql_models import Transaction, Player
    
    # 1. Fetch Player & Check Balance
    player = await session.get(Player, request.player_id)
    if not player:
        raise HTTPException(404, "Player not found")
        
    if player.balance_real_available < amount_major:
        raise HTTPException(400, "Insufficient funds")

    tx_id = str(uuid.uuid4())
    tx = Transaction(
        id=tx_id,
        tenant_id="default_casino", 
        player_id=request.player_id,
        type="withdrawal",
        amount=amount_major,
        currency=request.currency,
        status="pending",
        state="requested", # Player requested
        provider="adyen",
        metadata_json={"bank_account": bank_acc_adyen}
    )
    session.add(tx)
    
    # 2. Apply Ledger Delta (Available -> Held)
    from app.services.wallet_ledger import apply_wallet_delta_with_ledger
    await apply_wallet_delta_with_ledger(
        session,
        tenant_id="default_casino",
        player_id=request.player_id,
        tx_id=tx_id,
        event_type="withdraw_requested",
        delta_available=-float(amount_major),
        delta_held=+float(amount_major),
        currency=request.currency,
        idempotency_key=f"withdraw-{tx_id}"
    )
    
    await session.commit()
    
    return {
        "payout_id": tx_id,
        "status": "submitted",
        "psp_reference": "pending_admin_approval",
        "amount": request.amount,
        "currency": request.currency
    }

@router.get("/status/{payout_id}")
async def get_payout_status(payout_id: str, session = Depends(get_session)):
    from app.models.sql_models import Transaction
    tx = await session.get(Transaction, payout_id)
    if not tx:
        raise HTTPException(404, "Payout not found")
        
    return {
        "_id": tx.id,
        "player_id": tx.player_id,
        "amount": int(tx.amount * 100),
        "currency": tx.currency,
        "status": tx.state, # e.g. requested, approved, payout_submitted, paid
        "psp_reference": tx.provider_event_id,
        "created_at": tx.created_at,
        "webhook_events": [] # simplified
    }

@router.get("/player/{player_id}/history")
async def get_player_payout_history(player_id: str, session = Depends(get_session)):
    from app.models.sql_models import Transaction
    stmt = select(Transaction).where(
        Transaction.player_id == player_id,
        Transaction.type == "withdrawal"
    ).order_by(Transaction.created_at.desc())
    
    result = await session.execute(stmt)
    txs = result.scalars().all()
    
    return {
        "payouts": [
            {
                "_id": tx.id,
                "amount": int(tx.amount * 100),
                "status": tx.state,
                "created_at": tx.created_at
            } for tx in txs
        ],
        "total": len(txs)
    }
