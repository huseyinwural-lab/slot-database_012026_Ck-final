from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import Optional, Dict
import uuid
import logging
from datetime import datetime

from app.core.database import get_session
from app.models.sql_models import Transaction, Player
from app.utils.auth_player import get_current_player
from app.services.wallet_ledger import apply_wallet_delta_with_ledger
from app.services.adyen_psp import AdyenPSP
from config import settings
from pydantic import BaseModel, Field

# Initialize router
router = APIRouter(prefix="/api/v1/payments/adyen", tags=["payments", "adyen"])
logger = logging.getLogger(__name__)

# Initialize Service
# In a real app, we might inject this dependency
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
        # Fallback for local testing if origin missing
        origin = settings.cors_origins[0] if isinstance(settings.cors_origins, list) else "http://localhost:3000"
    
    # Adyen redirects here. Frontend handles the result.
    # We append the tx_id to verify later if needed, though Adyen sends reference.
    return_url = f"{origin}/wallet?provider=adyen&tx_id={tx_id}"

    # 3. Create Payment Link
    try:
        link_response = await adyen.create_payment_link(
            amount=body.amount,
            currency=body.currency,
            reference=tx_id, # Use tx_id as reference
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

    return {"url": link_response.get("url")}


@router.post("/webhook")
async def adyen_webhook(
    request: Request,
    session: AsyncSession = Depends(get_session)
):
    """
    Handle Adyen Webhooks (Notification).
    """
    body = await request.json()
    
    # Basic validation structure for Adyen
    notification_items = body.get("notificationItems", [])
    
    for item in notification_items:
        req_item = item.get("NotificationRequestItem", {})
        
        # We process 'AUTHORISATION' event
        if req_item.get("eventCode") == "AUTHORISATION":
             tx_id = req_item.get("merchantReference")
             success = req_item.get("success") == "true"
             psp_reference = req_item.get("pspReference")
             
             # Find Transaction
             stmt = select(Transaction).where(Transaction.id == tx_id)
             tx = (await session.execute(stmt)).scalars().first()
             
             if not tx:
                 logger.warning(f"Adyen Webhook: Transaction {tx_id} not found")
                 continue
                 
             if tx.status == "completed":
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

    return {"status": "[accepted]"}

@router.post("/test-trigger-webhook")
async def test_trigger_webhook(
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_session)
):
    """
    Simulate Adyen Webhook for E2E testing.
    Payload: { "tx_id": "...", "success": true }
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
