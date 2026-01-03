from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import Optional, Dict
import uuid
import logging

from app.core.database import get_session
from app.models.sql_models import Transaction, Player, AuditEvent
from app.utils.auth_player import get_current_player
from app.services.wallet_ledger import apply_wallet_delta_with_ledger
from app.services.adyen_psp import AdyenPSP
from app.services.metrics import metrics
from config import settings
from pydantic import BaseModel, Field

# Initialize router
router = APIRouter(prefix="/api/v1/payments/adyen", tags=["payments", "adyen"])
logger = logging.getLogger(__name__)

# Initialize Service
def get_adyen_service():
    return AdyenPSP(
        api_key=settings.adyen_api_key or "mock_key",
        merchant_account=settings.adyen_merchant_account or "mock_merchant"
    )

class AdyenDepositRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Amount to deposit")
    currency: str = Field("USD", description="Currency code")
    metadata: Optional[Dict[str, str]] = Field(default_factory=dict)

@router.post("/checkout/session")
async def create_checkout_session(
    request: Request,
    body: AdyenDepositRequest,
    current_player: Player = Depends(get_current_player),
    session: AsyncSession = Depends(get_session),
    adyen: AdyenPSP = Depends(get_adyen_service)
):
    """
    Create an Adyen Payment Link for deposit.
    """
    # 1. Create Transaction (Pending)
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
        provider="adyen",
        method="adyen_payment_link",
        balance_after=0.0,
        metadata_json=body.metadata or {}
    )
    session.add(tx)
    await session.commit()
    await session.refresh(tx)

    # 2. Construct Return URL
    origin = request.headers.get("origin")
    if not origin:
        origin = settings.player_app_url or (
            settings.get_cors_origins()[0] if settings.get_cors_origins() else "http://localhost:3001"
        )
    
    return_url = f"{origin}/wallet?provider=adyen&tx_id={tx_id}"

    # 3. Create Payment Link
    try:
        link_response = await adyen.create_payment_link(
            amount=body.amount,
            currency=body.currency,
            reference=tx_id, 
            return_url=return_url,
            shopper_email=current_player.email
        )
    except Exception as e:
        tx.status = "failed"
        tx.state = "failed"
        await session.commit()
        raise HTTPException(status_code=500, detail=str(e))

    # 4. Update Transaction
    tx.provider_event_id = link_response.get("id")
    tx.state = "pending_provider"
    session.add(tx)
    await session.commit()

    # Ensure UI contract has tx_id for deterministic redirect handling
    return {"url": link_response.get("url"), "tx_id": tx_id}


@router.post("/webhook")
async def adyen_webhook(
    request: Request,
    session: AsyncSession = Depends(get_session),
    adyen: AdyenPSP = Depends(get_adyen_service)
):
    """Handle Adyen Webhooks (Notification)."""

    body = await request.json()

    # Signature Verification (Adyen HMAC in additionalData.hmacSignature)
    if not adyen.verify_webhook_signature(body, ""):
        metrics.record_webhook_signature_failure("adyen")
        raise HTTPException(status_code=401, detail="WEBHOOK_SIGNATURE_INVALID")
    
    # Basic validation structure for Adyen
    notification_items = body.get("notificationItems", [])
    
    for item in notification_items:
        req_item = item.get("NotificationRequestItem", {})
        event_code = req_item.get("eventCode")
        
        # Metric recording
        metrics.record_webhook_event("adyen", event_code or "unknown")
        
        # We process 'AUTHORISATION' event
        if event_code == "AUTHORISATION":
            tx_id = req_item.get("merchantReference")
            success = req_item.get("success") == "true"
            psp_reference = req_item.get("pspReference")
            
            # Find Transaction
            stmt = select(Transaction).where(Transaction.id == tx_id)
            tx = (await session.execute(stmt)).scalars().first()
            
            if not tx:
                logger.warning(f"Adyen Webhook: Transaction {tx_id} not found")
                continue
                
            # Replay Check
            if tx.status == "completed":
                logger.info(f"Adyen Webhook: Replay detected for {tx_id}")
                # No-op 200
                metrics.record_webhook_replay()
                continue

            if success:
                # Apply Balance
                await apply_wallet_delta_with_ledger(
                   session,
                   tenant_id=tx.tenant_id,
                   player_id=tx.player_id,
                   tx_id=tx.id,
                   event_type="deposit_succeeded",
                   delta_available=tx.amount,
                   delta_held=0.0,
                   currency=tx.currency,
                   idempotency_key=f"adyen:{psp_reference}:capture",
                   provider="adyen",
                   provider_ref=psp_reference,
                   provider_event_id=psp_reference
                )
                tx.status = "completed"
                tx.state = "completed"
                session.add(tx)
                await session.commit()
            else:
                tx.status = "failed"
                tx.state = "failed"
                session.add(tx)
                await session.commit()

        # PAYOUT-REAL-001: Handle Payout Webhooks
        elif event_code == "PAYOUT_THIRDPARTY":
            tx_id = req_item.get("merchantReference") # We sent "payout_{attempt_id}"
            success = req_item.get("success") == "true"
            psp_reference = req_item.get("pspReference")
            
            # Extract Attempt ID from reference
            # format: payout_{attempt_id}
            if not tx_id or not tx_id.startswith("payout_"):
                logger.warning(f"Adyen Webhook: Invalid payout reference {tx_id}")
                continue
                
            attempt_id = tx_id.replace("payout_", "")
            
            # Find Attempt
            from app.models.sql_models import PayoutAttempt
            attempt = await session.get(PayoutAttempt, attempt_id)
            if not attempt:
                logger.warning(f"Adyen Webhook: PayoutAttempt {attempt_id} not found")
                continue
                
            # Find Transaction
            tx = await session.get(Transaction, attempt.withdraw_tx_id)
            if not tx:
                logger.warning("Adyen Webhook: Withdrawal TX not found")
                continue
                
            if tx.status == "completed":
                logger.info(f"Adyen Webhook: Payout already completed {tx.id}")
                continue
                metrics.record_webhook_replay()

            if success:
                # Ledger: Apply 'withdrawal_succeeded' (Unlock held funds and reduce balance permanently)
                # Wait, for withdrawal:
                # 1. Created: Delta Available -X, Delta Held +X
                # 2. Paid: Delta Held -X (burn)
                # Let's check 'apply_wallet_delta_with_ledger' logic for 'withdrawal_succeeded'
                # It should reduce 'held' balance.
                
                await apply_wallet_delta_with_ledger(
                   session,
                   tenant_id=tx.tenant_id,
                   player_id=tx.player_id,
                   tx_id=tx.id,
                   event_type="withdrawal_succeeded", # burns the held amount
                   delta_available=0.0,
                   delta_held=-tx.amount, # Reduce held
                   currency=tx.currency,
                   idempotency_key=f"adyen:{psp_reference}:payout",
                   provider="adyen",
                   provider_ref=psp_reference,
                   provider_event_id=psp_reference
                )
                tx.status = "completed"
                tx.state = "paid"
                metrics.record_payout_result(True)
                attempt.status = "success"
                
            else:
                # Payout Failed
                # We should Refund the Held amount? Or just mark failed and let admin retry?
                # Usually if payout fails, funds verify logic might keep them held until manual review.
                # Or we auto-refund to available.
                # For safety in this Sprint, we mark as 'payout_failed' and keep funds held.
                # Admin can 'Reject' to refund, or 'Retry'.
                tx.status = "payout_failed"
                tx.state = "payout_failed"
                metrics.record_payout_result(False)
                attempt.status = "failed"
                attempt.error_code = req_item.get("reason", "Payout Failed")
            
            session.add(tx)
            session.add(attempt)
            await session.commit()

    return {"status": "[accepted]"}

@router.post("/test-trigger-webhook")
async def test_trigger_webhook(
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_session)
):
    """
    Simulate Adyen Webhook for E2E testing.
    """
    if settings.env in {"prod", "production"}:
        raise HTTPException(status_code=403, detail="Not available in production")

    tx_id = payload.get("tx_id")
    success = payload.get("success", True)
    
    stmt = select(Transaction).where(Transaction.id == tx_id)
    tx = (await session.execute(stmt)).scalars().first()
    
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if tx.status == "completed":
        return {"status": "already_completed"}

    # Handle Payout Simulation
    if payload.get("type") == "payout":
        psp_reference = payload.get("psp_reference") or f"sim_payout_{uuid.uuid4()}"
        
        # Look up the Attempt by withdraw_tx_id = tx_id
        from app.models.sql_models import PayoutAttempt
        stmt = select(PayoutAttempt).where(
            PayoutAttempt.withdraw_tx_id == tx_id
        ).order_by(PayoutAttempt.created_at.desc())
        attempt = (await session.execute(stmt)).scalars().first()
        
        if not attempt:
            # If attempt missing (maybe manual curl test?), create one or fail?
            # For E2E robustness, if we can't find attempt, we might fail.
            # But let's log warning and try to proceed if possible? 
            # No, ledger needs idempotency which usually links to attempt.
            raise HTTPException(status_code=404, detail="Payout Attempt not found for this TX")

        if success:
            if tx and tx.status != "completed":
                await apply_wallet_delta_with_ledger(
                   session,
                   tenant_id=tx.tenant_id,
                   player_id=tx.player_id,
                   tx_id=tx.id,
                   event_type="withdrawal_succeeded",
                   delta_available=0.0,
                   delta_held=-tx.amount, 
                   currency=tx.currency,
                   idempotency_key=f"adyen:{psp_reference}:payout",
                   provider="adyen",
                   provider_ref=psp_reference,
                   provider_event_id=psp_reference
                )
                tx.status = "completed"
                tx.state = "paid"
                attempt.status = "success"
                session.add(tx)
                session.add(attempt)
                await session.commit()
                return {"status": "simulated_payout_success"}
        else:
            if tx:
                tx.status = "payout_failed"
                tx.state = "payout_failed"
                attempt.status = "failed"
                session.add(tx)
                session.add(attempt)
                await session.commit()
                return {"status": "simulated_payout_failed"}
        return {"status": "payout_processed"}

    # Handle Deposit Simulation (Default)
    if success:
        # Generate a fake psp reference
        psp_reference = f"sim_{uuid.uuid4()}"
        
        await apply_wallet_delta_with_ledger(
            session,
            tenant_id=tx.tenant_id,
            player_id=tx.player_id,
            tx_id=tx.id,
            event_type="deposit_succeeded",
            delta_available=tx.amount,
            delta_held=0.0,
            currency=tx.currency,
            idempotency_key=f"adyen:{psp_reference}:capture",
            provider="adyen",
            provider_ref=psp_reference,
            provider_event_id=psp_reference
        )
        tx.status = "completed"
        tx.state = "completed"
        session.add(tx)
        await session.commit()
        return {"status": "simulated_success", "tx_id": tx.id}
    else:
        tx.status = "failed"
        tx.state = "failed"
        session.add(tx)
        await session.commit()
        return {"status": "simulated_failure"}

    if payload.get("type") == "payout":
        # Simulate Payout Webhook
        # We need to manually trigger the logic that happens in the real webhook
        # Or easier: just call the internal logic?
        # But real webhook logic is inside `adyen_webhook`. 
        # Ideally we should just invoke the real webhook with a valid signature if possible,
        # but generating HMAC matches the one in config might be tricky if we don't have the lib.
        # Let's just implement the logic here for simulation.
        
        psp_reference = payload.get("psp_reference") or f"sim_payout_{uuid.uuid4()}"
        success = payload.get("success", True)
        
        # We need to find the TX and Attempt.
        # But wait, the E2E test might not know the internal "attempt_id".
        # The E2E test knows the "tx_id".
        # In `finance_actions.py`, we created an attempt and set provider_ref = attempt.id (via "payout_{id}")
        # So we need to look up the Attempt by `withdraw_tx_id = tx_id`.
        
        from app.models.sql_models import PayoutAttempt
        stmt = select(PayoutAttempt).where(
            PayoutAttempt.withdraw_tx_id == tx_id
        ).order_by(PayoutAttempt.created_at.desc())
        attempt = (await session.execute(stmt)).scalars().first()
        
        if not attempt:
            raise HTTPException(status_code=404, detail="Payout Attempt not found")
             
        # Mock Adyen sends merchantReference = "payout_{attempt_id}"
        # So we use that to mimic the real webhook payload
        
        # Apply Logic
        if success:
            # Find TX
            tx = await session.get(Transaction, tx_id)
            if tx and tx.status != "completed":
                await apply_wallet_delta_with_ledger(
                   session,
                   tenant_id=tx.tenant_id,
                   player_id=tx.player_id,
                   tx_id=tx.id,
                   event_type="withdrawal_succeeded",
                   delta_available=0.0,
                   delta_held=-tx.amount, 
                   currency=tx.currency,
                   idempotency_key=f"adyen:{psp_reference}:payout",
                   provider="adyen",
                   provider_ref=psp_reference,
                   provider_event_id=psp_reference
                )
                tx.status = "completed"
                tx.state = "paid"
                attempt.status = "success"
                session.add(tx)
                session.add(attempt)
                await session.commit()
                return {"status": "simulated_payout_success"}
        else:
            tx = await session.get(Transaction, tx_id)
            if tx:
                tx.status = "payout_failed"
                tx.state = "payout_failed"
                attempt.status = "failed"
                session.add(tx)
                session.add(attempt)
                await session.commit()
                return {"status": "simulated_payout_failed"}
