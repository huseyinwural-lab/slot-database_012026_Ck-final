from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, Dict
from datetime import datetime, timedelta
from sqlmodel import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.game_models import GameRound, GameEvent
from app.models.sql_models import Player
from app.utils.auth_player import get_current_player

router = APIRouter(prefix="/api/v1/player/history", tags=["player_history"])

@router.get("/games")
async def get_game_history(
    current_player: Player = Depends(get_current_player),
    session: AsyncSession = Depends(get_session),
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100),
    currency: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """
    Get aggregated game history (Round based).
    One round can have multiple events (Bet, Win, Bonus).
    We summarize them here.
    """
    
    # Query Rounds
    query = select(GameRound).where(GameRound.player_id == current_player.id)
    
    if currency:
        # Round doesn't strictly have currency column in P0 schema (it's on Event/Session)
        # We assume player's main currency or filter by join if needed.
        # For P0, ignore currency filter on round directly or join Session.
        pass

    if start_date:
        query = query.where(GameRound.created_at >= start_date)
    if end_date:
        query = query.where(GameRound.created_at <= end_date)
        
    query = query.order_by(GameRound.created_at.desc())
    
    # Count
    count_q = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_q)).scalar() or 0
    
    # Paginate
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    
    result = await session.execute(query)
    rounds = result.scalars().all()
    
    # Transform to Response (Aggregation on the fly? Or stored totals?)
    # GameRound has total_bet / total_win fields (updated by engine).
    items = []
    for r in rounds:
        items.append({
            "round_id": r.provider_round_id,
            "game_id": r.game_id,
            "status": r.status,
            "total_bet": r.total_bet,
            "total_win": r.total_win,
            "net": r.total_win - r.total_bet,
            "currency": "USD", # Fallback P0
            "created_at": r.created_at
        })
        
    return {
        "items": items,
        "meta": {
            "total": total,
            "page": page,
            "limit": limit
        }
    }
