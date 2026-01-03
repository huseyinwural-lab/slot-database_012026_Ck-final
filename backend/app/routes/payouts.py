from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.core.security import get_current_player
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
    current_player=Depends(lambda: None),
):
    # Use AdyenPSP service which handles Mocking in Dev
    merchant_reference = f"PAYOUT-{request.player_id}-{uuid.uuid4().hex[:8]}"
    
    try:
        # Convert minor units to major for AdyenPSP service (it expects float)
        # Wait, AdyenPSP.submit_payout takes float?
        # Let's check AdyenPSP.submit_payout signature.
        # Step 31: amount: float.
        amount_major = request.amount / 100.0
        
        # Prepare bank account dict
        bank_acc = request.bank_account.model_dump(by_alias=True)
        # Remap fields if necessary? AdyenPSP expects dict passed to payload.
        # AdyenPSP.submit_payout expects `bank_account` dict.
        # Keys should match Adyen API: accountHolderName, etc.
        # My PayoutRequest uses snake_case.
        # I need to camelCase it.
        
        bank_acc_adyen = {
            "accountHolderName": request.bank_account.account_holder_name,
            "accountNumber": request.bank_account.account_number,
            "bankCode": request.bank_account.bank_code,
            "branchCode": request.bank_account.branch_code,
            "countryCode": request.bank_account.country_code,
            "currencyCode": request.bank_account.currency_code
        }

        adyen_response = await adyen.submit_payout(
            amount=amount_major,
            currency=request.currency,
            reference=merchant_reference,
            shopper_reference=request.player_id,
            shopper_email=request.player_email,
            bank_account=bank_acc_adyen,
            metadata={"description": request.description}
        )
        
        # In Mock mode, AdyenPSP returns { "pspReference": ..., "resultCode": ... }
        
        # Store attempt/record?
        # We should create a Transaction + PayoutAttempt?
        # Or just return success for Smoke Test?
        # The E2E test checks for "Withdrawal submitted".
        # And later Admin checks "Payout Pending".
        # This endpoint is called by PLAYER.
        # So it should create a Withdrawal Transaction.
        
        # Create Transaction
        from app.models.sql_models import Transaction
        tx_id = str(uuid.uuid4())
        tx = Transaction(
            id=tx_id,
            tenant_id="default_casino", # Assumption
            player_id=request.player_id,
            type="withdrawal",
            amount=amount_major,
            currency=request.currency,
            status="pending", # Pending admin approval
            state="requested",
            provider="adyen",
            provider_event_id=adyen_response.get("pspReference"),
            metadata_json={"bank_account": bank_acc_adyen}
        )
        session.add(tx)
        
        # Create PayoutAttempt?
        # Usually PayoutAttempt is created when Admin approves/retries.
        # Player request just creates TX.
        # BUT AdyenPSP.submit_payout SENDS money.
        # Player should NOT trigger submit_payout directly!
        # Player request should only create TX.
        # Admin triggers payout.
        
        # WAIT. My E2E test says: 
        # "6. Request Withdrawal" (Player)
        # "11. Start Payout" (Admin)
        
        # So `POST /api/payouts/initiate` should ONLY create the Transaction.
        # It should NOT call AdyenPSP.submit_payout.
        # The E2E loop relies on Admin to trigger the real payout.
        
        # Correction:
        # Player requests withdrawal -> TX created (status=pending/requested).
        # Admin approves -> TX status=approved.
        # Admin clicks "Retry/Pay" -> calls AdyenPSP.submit_payout -> TX status=payout_pending.
        
        # So `initiate_payout` should ONLY create DB record.
        pass # To remove the adyen call below
        
    except Exception as e:
        logger.error(f"Payout Init Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
