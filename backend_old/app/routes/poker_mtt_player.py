from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from datetime import datetime, timezone

from app.core.database import get_session
from app.models.poker_mtt_models import PokerTournament, TournamentRegistration
from app.models.sql_models import Player
from app.utils.auth_player import get_current_player
from app.repositories.ledger_repo import append_event, apply_balance_delta, get_balance

router = APIRouter(prefix="/api/v1/poker/mtt", tags=["poker_mtt_player"])

@router.post("/{tournament_id}/reentry")
async def reentry_tournament(
    tournament_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
    player: Player = Depends(get_current_player)
):
    """
    Re-enter a tournament if eliminated and rules allow.
    """
    tenant_id = player.tenant_id
    
    # 1. Load Tournament
    tourney = await session.get(PokerTournament, tournament_id)
    if not tourney or tourney.tenant_id != tenant_id:
        raise HTTPException(404, "Tournament not found")
        
    # 2. Check State & Time
    if tourney.status not in ["REG_OPEN", "RUNNING"]:
        raise HTTPException(400, "Tournament not active")
        
    if tourney.late_reg_until and datetime.now(timezone.utc) > tourney.late_reg_until:
        raise HTTPException(400, "Late registration closed")
        
    # 3. Check Eligibility (Must be BUSTED from previous entry)
    # Count previous entries
    stmt = select(TournamentRegistration).where(
        TournamentRegistration.tournament_id == tournament_id,
        TournamentRegistration.player_id == player.id
    ).order_by(TournamentRegistration.registered_at.desc())
    
    entries = (await session.execute(stmt)).scalars().all()
    count = len(entries)
    
    if count == 0:
        raise HTTPException(400, "Use standard registration first")
        
    last_entry = entries[0]
    if last_entry.status != "busted":
        raise HTTPException(400, "Player is still active in tournament")
        
    # Check Limit
    if tourney.reentry_max > 0 and (count - 1) >= tourney.reentry_max: # count-1 because 1st is entry
        raise HTTPException(400, "Re-entry limit reached")
        
    # 4. Financials
    cost = tourney.reentry_price if tourney.reentry_price is not None else tourney.buy_in
    fee = 0.0 # Usually fee is waived or reduced on reentry? Let's assume 0 for Reentry MVP or full fee? 
    # Standard practice varies. Let's charge standard Fee for MVP unless 'reentry_fee' model exists.
    # Actually, let's charge ONLY 'cost' (which covers prize pool part) + standard fee?
    # If reentry_price is None, use buy_in. Fee is separate.
    # Simpler: Total Cost = cost + tourney.fee
    total_deduct = cost + tourney.fee
    
    # Wallet Check
    bal = await get_balance(session, tenant_id=tenant_id, player_id=player.id, currency=tourney.currency)
    if bal.balance_real_available < total_deduct:
        raise HTTPException(402, "Insufficient funds")
        
    # 5. Execute Re-entry
    import uuid
    tx_id_buyin = str(uuid.uuid4())
    
    # Ledger
    await append_event(
        session,
        tenant_id=tenant_id,
        player_id=player.id,
        tx_id=tx_id_buyin,
        type="mtt_reentry",
        direction="debit",
        amount=total_deduct,
        currency=tourney.currency,
        status="completed",
        provider="internal_poker",
        provider_ref=tournament_id
    )
    await apply_balance_delta(
        session=session,
        tenant_id=tenant_id,
        player_id=player.id,
        currency=tourney.currency,
        delta_available=-total_deduct
    )
    
    # Registration Record
    reg = TournamentRegistration(
        tenant_id=tenant_id,
        tournament_id=tournament_id,
        player_id=player.id,
        status="active",
        buyin_amount=cost,
        fee_amount=tourney.fee,
        tx_ref_buyin=tx_id_buyin,
        tx_ref_fee=tx_id_buyin
    )
    session.add(reg)
    
    # Update Tourney Stats
    tourney.prize_pool_total += cost
    tourney.entrants_count += 1
    session.add(tourney)
    
    await session.commit()
    
    return {"status": "re-entered", "registration_id": reg.id}
