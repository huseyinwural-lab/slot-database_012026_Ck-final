from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import Dict, Any

from app.core.database import get_session
from app.models.sql_models import Player, Transaction
from app.repositories.ledger_repo import LedgerTransaction
from app.models.poker_models import RakeProfile, PokerHandAudit
from app.services.poker.rake_engine import rake_engine
# Assuming provider auth is handled via API Key middleware globally or specific dependency
# For MVP we skip provider auth check logic here but assume it exists.

router = APIRouter(prefix="/api/v1/integrations/poker", tags=["poker"])

@router.post("/transaction")
async def poker_transaction(
    payload: Dict[str, Any] = Body(...),
    session: AsyncSession = Depends(get_session)
):
    """
    Handle Wallet Debit (Buy-in/Bet) or Credit (Win/Cashout).
    Payload: {
        "tenant_id": str,
        "player_id": str,
        "type": "DEBIT"|"CREDIT",
        "amount": float,
        "currency": str,
        "round_id": str (hand_id),
        "transaction_id": str (provider_tx_id)
    }
    """
    tenant_id = payload.get("tenant_id", "default_casino")
    player_id = payload["player_id"]
    tx_type = payload["type"]
    amount = float(payload["amount"])
    round_id = payload.get("round_id")
    prov_tx_id = payload["transaction_id"]
    
    # Idempotency Check
    stmt = select(Transaction).where(Transaction.idempotency_key == prov_tx_id)
    existing = (await session.execute(stmt)).scalars().first()
    if existing:
        return {"status": "OK", "balance": existing.balance_after, "ref": existing.id}
    
    player = await session.get(Player, player_id)
    if not player:
        raise HTTPException(404, "Player not found")
        
    new_bal = player.balance_real_available
    
    if tx_type == "DEBIT":
        if player.balance_real_available < amount:
            raise HTTPException(402, "Insufficient funds")
        player.balance_real_available -= amount
        player.balance_real -= amount
        new_bal = player.balance_real_available
        
        # Transaction
        tx = Transaction(
            tenant_id=tenant_id, player_id=player_id, type="poker_bet", amount=amount,
            currency=payload.get("currency", "USD"), status="completed", state="completed",
            method="wallet", provider="poker_provider", provider_event_id=round_id,
            idempotency_key=prov_tx_id, balance_after=new_bal
        )
        session.add(tx)
        
        # Ledger
        lt = LedgerTransaction(
            tenant_id=tenant_id, player_id=player_id, type="poker_bet", amount=amount,
            currency=payload.get("currency", "USD"), status="success", direction="debit",
            provider="poker_provider", provider_ref=round_id
        )
        session.add(lt)
        
    elif tx_type == "CREDIT":
        player.balance_real_available += amount
        player.balance_real += amount
        new_bal = player.balance_real_available
        
        tx = Transaction(
            tenant_id=tenant_id, player_id=player_id, type="poker_win", amount=amount,
            currency=payload.get("currency", "USD"), status="completed", state="completed",
            method="wallet", provider="poker_provider", provider_event_id=round_id,
            idempotency_key=prov_tx_id, balance_after=new_bal
        )
        session.add(tx)
        
        lt = LedgerTransaction(
            tenant_id=tenant_id, player_id=player_id, type="poker_win", amount=amount,
            currency=payload.get("currency", "USD"), status="success", direction="credit",
            provider="poker_provider", provider_ref=round_id
        )
        session.add(lt)
        
    session.add(player)
    await session.commit()
    
    return {"status": "OK", "balance": new_bal, "ref": tx.id}

@router.post("/hand-history")
async def poker_hand_audit(
    payload: Dict[str, Any] = Body(...),
    session: AsyncSession = Depends(get_session)
):
    """
    Audit / Rake Calculation.
    Payload: {
        "tenant_id": str,
        "hand_id": str,
        "table_id": str,
        "game_type": "CASH",
        "pot_total": float,
        "winners": [{"player_id": str, "amount": float}],
        "player_count": int
    }
    """
    tenant_id = payload.get("tenant_id", "default_casino")
    
    # 1. Load Rake Profile
    # Simplified: Get first active profile or default
    stmt = select(RakeProfile).where(RakeProfile.tenant_id == tenant_id, RakeProfile.is_active == True).limit(1)
    profile = (await session.execute(stmt)).scalars().first()
    
    if not profile:
        # Create default if missing (Auto-seed for MVP)
        profile = RakeProfile(tenant_id=tenant_id, name="Default Rake", percentage=5.0, cap=3.0)
        session.add(profile)
        await session.flush()
    
    # 2. Verify Rake
    calculated_rake = rake_engine.calculate_rake(
        pot=payload["pot_total"], 
        profile=profile, 
        player_count=payload.get("player_count", 2)
    )
    
    # 3. Store Audit
    audit_record = PokerHandAudit(
        tenant_id=tenant_id,
        provider_hand_id=payload["hand_id"],
        table_id=payload["table_id"],
        game_type=payload.get("game_type", "CASH"),
        pot_total=payload["pot_total"],
        rake_collected=calculated_rake,
        rake_profile_id=profile.id,
        winners=payload.get("winners", {})
    )
    session.add(audit_record)
    
    # 4. Ledger Entry for Rake Revenue (System Gain)
    # We book the Rake as "Revenue"
    lt = Transaction(
        tenant_id=tenant_id,
        player_id="system", # System account
        type="poker_rake",
        amount=calculated_rake,
        currency="USD",
        status="revenue",
        direction="credit", # Credit to system
        provider="poker_provider",
        provider_ref=payload["hand_id"]
    )
    session.add(lt)
    
    await session.commit()
    
    return {"status": "OK", "rake_calculated": calculated_rake, "audit_id": audit_record.id}
