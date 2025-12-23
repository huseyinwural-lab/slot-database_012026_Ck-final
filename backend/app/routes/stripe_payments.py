from fastapi import APIRouter, Depends, HTTPException, Body, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import Optional, Dict
import uuid
import logging

from app.core.database import get_session
from app.models.sql_models import Transaction, Player
from app.utils.auth_player import get_current_player
from app.services.audit import audit
from app.services.wallet_ledger import apply_wallet_delta_with_ledger
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionRequest, CheckoutSessionResponse
from config import settings
import os
from pydantic import BaseModel, Field

# Initialize router
router = APIRouter(prefix="/api/v1/payments/stripe", tags=["payments", "stripe"])
logger = logging.getLogger(__name__)

# Using global init for efficiency, but need to ensure env is loaded.
STRIPE_API_KEY = settings.stripe_api_key
webhook_url = "/api/v1/payments/stripe/webhook" # Relative path, will be constructed with host

# We need to instantiate this per request or lazily if we want to capture host_url correctly
# or just once if we pass the URLs dynamically.
# The library example: stripe_checkout = StripeCheckout(api_key=api_key, webhook_url=webhook_url)

class StripeDepositRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Amount to deposit")
    currency: str = Field("USD", description="Currency code")
    metadata: Optional[Dict[str, str]] = Field(default_factory=dict)

@router.post("/checkout/session", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    request: Request,
    body: StripeDepositRequest,
    current_player: Player = Depends(get_current_player),
    session: AsyncSession = Depends(get_session)
):
    """
    Create a Stripe Checkout Session for a deposit.
    """
    if not STRIPE_API_KEY:
        raise HTTPException(status_code=500, detail="Stripe configuration missing")

    # 1. Validation
    # Enforce limits (reusing logic from player_wallet if possible, but simplified here)
    if body.amount < 10.0: # Minimum deposit
        raise HTTPException(status_code=400, detail="Minimum deposit is $10.00")
    
    # 2. Create Transaction (Pending)
    tx_id = str(uuid.uuid4())
    tx = Transaction(
        id=tx_id,
        tenant_id=current_player.tenant_id,
        player_id=current_player.id,
        type="deposit",
        amount=body.amount,
        currency=body.currency,
        status="pending",
        state="created", # Initial state
        provider="stripe",
        method="stripe_checkout",
        balance_after=0.0, # Will be updated on completion
        metadata_json=body.metadata or {}
    )
    session.add(tx)
    await session.commit()
    await session.refresh(tx)

    # 3. Initialize Stripe Helper
    # Construct full URLs
    host_url = str(request.base_url).rstrip("/")
    # Check if REACT_APP_BACKEND_URL or similar matches request.base_url 
    # For frontend redirect, we need the FRONTEND URL, not backend.
    # Usually we get origin from headers or config.
    # The Playbook says: "Frontend will get the host header via window.location.origin and call the backend... passing the host header"
    # But here we are simplifying. Let's assume the frontend calls this and we return a URL.
    # We need to know where to redirect back.
    # Ideally, frontend sends `success_url` pattern.
    # For now, let's look at `request.headers.get("origin")`.
    origin = request.headers.get("origin")
    if not origin:
        # Fallback to a known frontend URL or throw error
        # In this environment, frontend is on port 3000.
        # But we don't know the external IP easily if not provided.
        # Let's trust the origin header if present, else fail.
        raise HTTPException(status_code=400, detail="Origin header required for redirect construction")

    success_url = f"{origin}/wallet?session_id={{CHECKOUT_SESSION_ID}}&status=success"
    cancel_url = f"{origin}/wallet?status=cancel"

    full_webhook_url = f"{host_url}{webhook_url}"
    
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=full_webhook_url)

    # 4. Create Session
    checkout_request = CheckoutSessionRequest(
        amount=body.amount,
        currency=body.currency,
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "tx_id": tx_id,
            "player_id": current_player.id,
            "tenant_id": current_player.tenant_id,
            "type": "deposit"
        }
    )

    try:
        checkout_session = await stripe_checkout.create_checkout_session(checkout_request)
    except Exception as e:
        logger.error(f"Stripe Session Creation Failed: {e}")
        tx.status = "failed"
        tx.state = "failed"
        await session.commit()
        raise HTTPException(status_code=500, detail=str(e))

    # 5. Update Transaction with Provider IDs
    tx.provider_event_id = checkout_session.session_id
    tx.state = "pending_provider"
    session.add(tx)
    await session.commit()

    return checkout_session

@router.get("/checkout/status/{session_id}")
async def get_checkout_status(
    session_id: str,
    request: Request,
    current_player: Player = Depends(get_current_player),
    session: AsyncSession = Depends(get_session)
):
    """
    Poll status of a session and update DB if changed.
    """
    if not STRIPE_API_KEY:
        raise HTTPException(status_code=500, detail="Stripe configuration missing")

    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url="") # Webhook url not needed for status check

    try:
        status_response = await stripe_checkout.get_checkout_status(session_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch status: {e}")

    # Find Transaction
    stmt = select(Transaction).where(
        Transaction.provider_event_id == session_id,
        Transaction.provider == "stripe"
    )
    tx = (await session.execute(stmt)).scalars().first()

    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Check if already processed
    if tx.status == "completed":
        return status_response

    # Update logic
    if status_response.payment_status == "paid":
        # Apply Balance Update
        # Using apply_wallet_delta_with_ledger to be safe and consistent
        await apply_wallet_delta_with_ledger(
            session,
            tenant_id=tx.tenant_id,
            player_id=tx.player_id,
            tx_id=tx.id,
            event_type="deposit_succeeded",
            delta_available=tx.amount, # Credit
            delta_held=0.0,
            currency=tx.currency,
            idempotency_key=f"stripe:{session_id}:capture",
            provider="stripe",
            provider_ref=session_id,
            provider_event_id=session_id
        )
        
        tx.status = "completed"
        tx.state = "completed"
        session.add(tx)
        await session.commit()
        
    elif status_response.status == "expired":
        tx.status = "failed"
        tx.state = "expired"
        session.add(tx)
        await session.commit()

    return status_response

@router.post("/test-trigger-webhook")
async def test_trigger_webhook(
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_session)
):
    """
    Test-only endpoint to simulate a Stripe Webhook event.
    Only available in non-prod environments.
    """
    if settings.env in {"prod", "production"}:
        raise HTTPException(status_code=403, detail="Not available in production")

    event_type = payload.get("type")
    session_id = payload.get("session_id")

    if event_type == "checkout.session.completed":
        # Idempotency check
        stmt = select(Transaction).where(
            Transaction.provider_event_id == session_id,
            Transaction.provider == "stripe"
        )
        tx = (await session.execute(stmt)).scalars().first()

        if tx and tx.status != "completed":
             await apply_wallet_delta_with_ledger(
                session,
                tenant_id=tx.tenant_id,
                player_id=tx.player_id,
                tx_id=tx.id,
                event_type="deposit_succeeded",
                delta_available=tx.amount,
                delta_held=0.0,
                currency=tx.currency,
                idempotency_key=f"stripe:{session_id}:capture",
                provider="stripe",
                provider_ref=session_id,
                provider_event_id=session_id
            )
             tx.status = "completed"
             tx.state = "completed"
             session.add(tx)
             await session.commit()
             return {"status": "simulated_success", "tx_id": tx.id}
    
    return {"status": "ignored"}

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    session: AsyncSession = Depends(get_session)
):
    """
    Handle Stripe Webhooks
    """
    if not STRIPE_API_KEY:
        raise HTTPException(status_code=500, detail="Stripe configuration missing")

    body_bytes = await request.body()
    sig_header = request.headers.get("stripe-signature")

    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url="")

    try:
        # Note: library might need fixed webhook secret if verifying signature properly
        # The playbook says: handle_webhook(webhook_request_body_bytes, request.headers.get("Stripe-Signature"))
        # But handle_webhook usually needs the secret to be set in the class or passed?
        # emergentintegrations 0.1.0 might handle this.
        webhook_response = await stripe_checkout.handle_webhook(body_bytes, sig_header)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook Error: {e}")

    # Process event
    if webhook_response.event_type == "checkout.session.completed":
        session_id = webhook_response.session_id
        
        # Idempotency check
        stmt = select(Transaction).where(
            Transaction.provider_event_id == session_id,
            Transaction.provider == "stripe"
        )
        tx = (await session.execute(stmt)).scalars().first()

        if tx and tx.status != "completed":
             await apply_wallet_delta_with_ledger(
                session,
                tenant_id=tx.tenant_id,
                player_id=tx.player_id,
                tx_id=tx.id,
                event_type="deposit_succeeded",
                delta_available=tx.amount,
                delta_held=0.0,
                currency=tx.currency,
                idempotency_key=f"stripe:{session_id}:capture",
                provider="stripe",
                provider_ref=session_id,
                provider_event_id=session_id
            )
             tx.status = "completed"
             tx.state = "completed"
             session.add(tx)
             await session.commit()

    return {"status": "success"}
