from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import hashlib
import logging

from app.core.database import get_session
from app.models.game_models import GameSession
from app.services.slot_math import SlotMath
from app.core.errors import AppError
from app.schemas.game_schemas import ProviderEvent
from app.services.game_engine import GameEngine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/mock-provider", tags=["mock_provider"])

@router.post("/spin")
async def mock_spin(
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_session)
):
    """
    Smart Spin Endpoint.
    Uses SlotMath engine instead of random.
    """
    session_id = payload.get("session_id")
    bet_amount = float(payload.get("amount", 0.0))
    currency = payload.get("currency", "USD")
    
    # 1. Load Session
    game_session = await session.get(GameSession, session_id)
    if not game_session:
        raise HTTPException(404, "Session not found")
        
    # 2. Load Math Context
    try:
        robot, reelset, paytable = await SlotMath.load_context(session, game_session)
    except AppError as e:
        raise HTTPException(e.status_code, e.message)
        
    # 3. Deterministic RNG
    round_id = f"rnd-{uuid.uuid4().hex[:12]}"
    seed_str = f"{game_session.tenant_id}|{game_session.game_id}|{game_session.player_id}|{session_id}|{round_id}"
    seed = hashlib.sha256(seed_str.encode()).hexdigest()
    
    # 4. Generate Outcome
    grid, stops = SlotMath.generate_grid(reelset.content, seed)
    result = SlotMath.calculate_payout(grid, paytable.content, bet_amount)
    
    total_win = result["total_win"]
    
    # 5. Process Ledger (Bet + Win)
    # Helper to send signed callback internal
    # We call GameEngine directly here to save HTTP overhead within same process, 
    # BUT to verify B-FIN requirements we should simulate the 'External' call or use the Engine.
    # We use GameEngine directly for efficiency but maintain the "Contract".
    
    # BET Event
    bet_event = ProviderEvent(
        provider_id="mock-smart",
        event_type="BET",
        session_id=session_id,
        provider_round_id=round_id,
        provider_event_id=f"evt-bet-{uuid.uuid4().hex}",
        amount=bet_amount,
        currency=currency,
        signature="internal" # Trusted
    )
    
    # WIN Event
    win_event = ProviderEvent(
        provider_id="mock-smart",
        event_type="WIN",
        session_id=session_id,
        provider_round_id=round_id,
        provider_event_id=f"evt-win-{uuid.uuid4().hex}",
        amount=total_win,
        currency=currency,
        signature="internal"
    )
    
    try:
        # Atomic Transaction ideally
        # 1. Bet
        await GameEngine.process_event(session, bet_event)
        # 2. Win (if any)
        final_bal_resp = None
        if total_win > 0:
            final_bal_resp = await GameEngine.process_event(session, win_event)
        else:
            # Need to get balance if no win event
            # Hack: send 0 win? Or just query player.
            # GameEngine handles 0 win gracefully usually as a "Loss" event or just skip.
            # Let's query player balance.
            from app.models.sql_models import Player
            p = await session.get(Player, game_session.player_id)
            final_bal = p.balance_real_available
    except AppError as e:
        raise HTTPException(e.status_code, e.message)
        
    # Get Final Balance
    from app.models.sql_models import Player
    await session.refresh(game_session)
    player = await session.get(Player, game_session.player_id)
    
    # Audit Provenance
    audit_data = {
        "robot_id": robot.id,
        "robot_config_hash": robot.config_hash,
        "reelset_hash": reelset.content_hash,
        "paytable_hash": paytable.content_hash,
        "seed_hash": seed,
        "stops": stops
    }
    
    return {
        "status": "success",
        "round_id": round_id,
        "grid": grid,
        "lines": result["details"],
        "win": total_win,
        "balance": player.balance_real_available,
        "audit": audit_data
    }
