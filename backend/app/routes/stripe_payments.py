from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import Optional, Dict
import uuid
import logging
import stripe
from app.core.database import get_session
from app.models.sql_models import Transaction, Player
from app.utils.auth_player import get_current_player
from app.services.wallet_ledger import apply_wallet_delta_with_ledger
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionRequest, CheckoutSessionResponse
from app.services.metrics import metrics
from config import settings
from pydantic import BaseModel, Field

# Initialize router
router = APIRouter(prefix="/api/v1/payments/stripe", tags=["payments", "stripe"])
logger = logging.getLogger(__name__)

# Initialize global stripe api key if available for direct usage
if settings.stripe_api_key:
    stripe.api_key = settings.stripe_api_key

STRIPE_API_KEY = settings.stripe_api_key
webhook_url = "/api/v1/payments/stripe/webhook" 

class StripeDepositRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Amount to deposit")
    currency: str = Field("USD", description="Currency code")
    metadata: Optional[Dict[str, str]] = Field(default_factory=dict)

class CheckoutSessionResponseWithTxId(CheckoutSessionResponse):
    tx_id: str


@router.post("/checkout/session", response_model=CheckoutSessionResponseWithTxId)
async def create_checkout_session(
    request: Request,
    body: StripeDepositRequest,
    current_player: Player = Depends(get_current_player),
    session: AsyncSession = Depends(get_session)
):
    """
    Create a Stripe Checkout Session for a deposit.
    """

    # Enforce tenant policy limits at payment initiation time (covers Stripe + CI mock).
    from app.services.tenant_policy_enforcement import ensure_within_tenant_daily_limits

    await ensure_within_tenant_daily_limits(
        session,
        tenant_id=current_player.tenant_id,
        player_id=current_player.id,
        action="deposit",
        amount=body.amount,
        currency=body.currency,
    )

    if not STRIPE_API_KEY:
        # CI/dev/test deterministic mock: allow simulated checkout without real Stripe keys.
        if settings.env.lower() in {"ci", "test", "dev"} or settings.stripe_mock:
            session_id = f"cs_test_{uuid.uuid4().hex}"
            tx_id = str(uuid.uuid4())

            # Create a placeholder transaction for later simulated webhook.
            tx = Transaction(
                id=tx_id,
                tenant_id=current_player.tenant_id,
                player_id=current_player.id,
                type="deposit",
                amount=float(body.amount),
                currency=body.currency,
                status="pending_provider",
                provider="stripe",
                provider_ref=session_id,
                provider_event_id=session_id,
            )
            session.add(tx)
            await session.commit()

            origin = request.headers.get("origin") or settings.player_app_url
            return {
                "session_id": session_id,
                "url": f"{origin}/wallet?session_id={session_id}&status=success&tx_id={tx_id}",
                "tx_id": tx_id,
            }

        raise HTTPException(status_code=500, detail="Stripe configuration missing")

    if body.amount < 10.0:
        raise HTTPException(status_code=400, detail="Minimum deposit is $10.00")
    
    tx_id = str(uuid.uuid4())
    tx = Transaction(
        id=tx_id,
        tenant_id=current_player.tenant_id,
        player_id=current_player.id,
        type="deposit",
        amount=body.amount,
        currency=body.currency,
        status="pending",
        state="created", 
        provider="stripe",
        method="stripe_checkout",
        balance_after=0.0, 
        metadata_json=body.metadata or {}
    )
    session.add(tx)
    await session.commit()
    await session.refresh(tx)

    host_url = str(request.base_url).rstrip("/")
    origin = request.headers.get("origin")
    # In CI/E2E runs, the request Origin header may be missing due to proxying.
    # Fallback to configured player URL (or first CORS origin) to keep checkout deterministic.
    if not origin:
        origin = settings.player_app_url or (
            settings.get_cors_origins()[0] if settings.get_cors_origins() else "http://localhost:3001"
        )

    # Wallet contract requires tx_id in return URLs
    success_url = f"{origin}/wallet?session_id={{CHECKOUT_SESSION_ID}}&status=success&tx_id={tx_id}"
    cancel_url = f"{origin}/wallet?status=cancel&tx_id={tx_id}"

    full_webhook_url = f"{host_url}{webhook_url}"
    
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=full_webhook_url)

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
        # CI/dev/test deterministic mock: allow polling without real Stripe keys.
        if settings.env.lower() in {"ci", "test", "dev"} or settings.stripe_mock:
            stmt = select(Transaction).where(
                Transaction.provider_event_id == session_id,
                Transaction.provider == "stripe",
            )
            tx = (await session.execute(stmt)).scalars().first()
            if not tx:
                raise HTTPException(status_code=404, detail="Transaction not found")

            if tx.status == "completed":
                return {"status": "complete", "payment_status": "paid"}

            return {"status": "open", "payment_status": "unpaid"}

        raise HTTPException(status_code=500, detail="Stripe configuration missing")

    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url="") 

    try:
        status_response = await stripe_checkout.get_checkout_status(session_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch status: {e}")

    stmt = select(Transaction).where(
        Transaction.provider_event_id == session_id,
        Transaction.provider == "stripe"
    )
    tx = (await session.execute(stmt)).scalars().first()

    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if tx.status == "completed":
        status_response.payment_status = "paid"
        status_response.status = "complete"
        return status_response

    if status_response.payment_status == "paid":
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
    Handle Stripe Webhooks with Hardened Security
    """
    if not STRIPE_API_KEY:
        raise HTTPException(status_code=500, detail="Stripe configuration missing")

    body_bytes = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    event = None

    # Hardening: Verify Signature
    if settings.webhook_signature_enforced or settings.stripe_webhook_secret:
        webhook_secret = settings.stripe_webhook_secret
        if not webhook_secret and settings.webhook_signature_enforced:
             logger.error("Stripe webhook secret missing but signature enforced")
             raise HTTPException(status_code=500, detail="Configuration Error")
        
        try:
            event = stripe.Webhook.construct_event(
                payload=body_bytes,
                sig_header=sig_header,
                secret=webhook_secret,
                tolerance=300 # 5 minutes
            )
        except ValueError:
            # Invalid payload
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            raise HTTPException(status_code=400, detail=f"Webhook Error: {str(e)}")
    else:
        # Fallback for dev/mock without signature
        try:
             event = stripe.Event.construct_from(
                 await request.json(), stripe.api_key
             )
        except Exception:
             pass

    if not event:
         raise HTTPException(status_code=400, detail="Could not parse event")

    metrics.record_webhook_event("stripe", event.type)

    if event.type == "checkout.session.completed":
        session_obj = event.data.object
        session_id = session_obj.id
        
        # Idempotency check / Replay protection
        stmt = select(Transaction).where(
            Transaction.provider_event_id == session_id,
            Transaction.provider == "stripe"
        )
        tx = (await session.execute(stmt)).scalars().first()
        
        if tx:
            if tx.status == "completed":
                logger.info(f"Stripe Webhook: Replay detected for {session_id}")
                # Log audit event for replay?
                return {"status": "success", "replay": True}

            # Process
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
        else:
            logger.warning(f"Stripe Webhook: Transaction not found for {session_id}")
            # Maybe return 404 to force retry if race condition? Or 200 to ack?
            # Usually 200 because we can't do anything if TX doesn't exist yet (unless created by webhook)
            pass

    return {"status": "success"}
