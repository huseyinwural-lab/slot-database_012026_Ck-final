import os
import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.future import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.models.sql_models import Player, Transaction
from app.utils.auth_player import get_current_player

router = APIRouter(prefix="/api/v1/payments", tags=["Player Payments"])

MOCK_MODE = os.getenv("MOCK_EXTERNAL_SERVICES", "false").lower() == "true"

class DepositRequest(BaseModel):
    amount: float
    currency: str = "USD"

def _require_env(key: str):
    if MOCK_MODE:
        return
    if not os.getenv(key):
        raise HTTPException(
            status_code=503,
            detail={"error_code": "INTEGRATION_NOT_CONFIGURED", "message": f"Missing {key}"},
        )

@router.post("/deposit")
async def create_deposit(
    payload: DepositRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_player: Player = Depends(get_current_player),
):
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail={"error_code": "INVALID_AMOUNT"})

    if not current_player.email_verified or not current_player.sms_verified:
        raise HTTPException(
            status_code=403,
            detail={"error_code": "AUTH_UNVERIFIED", "message": "Verification required"},
        )

    _require_env("STRIPE_SECRET_KEY")
    frontend_url = os.getenv("PLAYER_FRONTEND_URL")
    if not frontend_url:
        raise HTTPException(
            status_code=503,
            detail={"error_code": "INTEGRATION_NOT_CONFIGURED", "message": "Missing PLAYER_FRONTEND_URL"},
        )

    if not MOCK_MODE:
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

    transaction = Transaction(
        tenant_id=current_player.tenant_id,
        player_id=current_player.id,
        type="deposit",
        amount=payload.amount,
        currency=payload.currency,
        status="pending",
        state="pending_provider",
        provider="stripe",
    )
    session.add(transaction)
    await session.commit()
    await session.refresh(transaction)

    success_url = f"{frontend_url}/wallet?status=success&tx={transaction.id}"
    cancel_url = f"{frontend_url}/wallet?status=cancel&tx={transaction.id}"

    checkout_id = f"sess_mock_{transaction.id}"
    checkout_url = success_url # Auto success for mock

    if not MOCK_MODE:
        checkout = stripe.checkout.Session.create(
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=transaction.id,
            line_items=[
                {
                    "price_data": {
                        "currency": payload.currency.lower(),
                        "product_data": {"name": "Casino Deposit"},
                        "unit_amount": int(payload.amount * 100),
                    },
                    "quantity": 1,
                }
            ],
            metadata={"transaction_id": transaction.id, "player_id": current_player.id},
        )
        checkout_id = checkout.id
        checkout_url = checkout.url

    transaction.provider_tx_id = checkout_id
    if MOCK_MODE:
        # Auto-complete for mock
        transaction.status = "completed"
        transaction.state = "completed"
        transaction.balance_after = current_player.balance_real + payload.amount
        current_player.balance_real += payload.amount
    
    await session.commit()

    return {
        "ok": True,
        "data": {
            "transaction_id": transaction.id,
            "session_id": checkout_id,
            "redirect_url": checkout_url,
        },
    }

@router.get("/{transaction_id}/status")
async def payment_status(
    transaction_id: str,
    session: AsyncSession = Depends(get_session),
    current_player: Player = Depends(get_current_player),
):
    transaction = await session.get(Transaction, transaction_id)
    if not transaction or transaction.player_id != current_player.id:
        raise HTTPException(status_code=404, detail={"error_code": "PAYMENT_NOT_FOUND"})
    return {
        "ok": True,
        "data": {
            "status": transaction.status,
            "state": transaction.state,
            "amount": transaction.amount,
            "currency": transaction.currency,
        },
    }

@router.post("/webhook/stripe")
async def stripe_webhook(request: Request, session: AsyncSession = Depends(get_session)):
    _require_env("STRIPE_WEBHOOK_SECRET")
    _require_env("STRIPE_SECRET_KEY")
    # ... mock logic if needed, but deposit endpoint auto-completes in mock mode ...
    return {"ok": True}
