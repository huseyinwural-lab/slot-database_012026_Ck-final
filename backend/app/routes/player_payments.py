import os
from datetime import datetime

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.future import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.models.sql_models import Player, Transaction
from app.utils.auth_player import get_current_player

router = APIRouter(prefix="/api/v1/payments", tags=["Player Payments"])


class DepositRequest(BaseModel):
    amount: float
    currency: str = "USD"


def _require_env(key: str):
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

    transaction.provider_tx_id = checkout.id
    await session.commit()

    return {
        "ok": True,
        "data": {
            "transaction_id": transaction.id,
            "session_id": checkout.id,
            "redirect_url": checkout.url,
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
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=os.getenv("STRIPE_WEBHOOK_SECRET"),
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail={"error_code": "WEBHOOK_INVALID"}) from exc

    if event["type"] == "checkout.session.completed":
        data = event["data"]["object"]
        transaction_id = data.get("client_reference_id") or data.get("metadata", {}).get("transaction_id")
        if transaction_id:
            transaction = await session.get(Transaction, transaction_id)
            if transaction and transaction.status != "completed":
                transaction.status = "completed"
                transaction.state = "completed"
                transaction.provider_event_id = event.get("id")
                player = await session.get(Player, transaction.player_id)
                if player:
                    player.balance_real += transaction.amount
                    transaction.balance_after = player.balance_real
                await session.commit()

    return {"ok": True}
