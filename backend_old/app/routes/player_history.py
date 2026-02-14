from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from sqlmodel import select, func, col
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.game_models import GameRound, Game
from app.models.sql_models import Player
from app.utils.auth_player import get_current_player
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/player/history", tags=["player_history"])

@router.get("/games")
async def get_game_history(
    current_player: Player = Depends(get_current_player),
    session: AsyncSession = Depends(get_session),
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100),
    currency: Optional[str] = None,
    provider: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """
    Get aggregated game history (Round based).
    """
    
    # Query Rounds joined with Game (Left Join to show rounds even if game metadata missing)
    query = select(GameRound, Game).join(Game, GameRound.game_id == Game.id, isouter=True)
    query = query.where(GameRound.player_id == current_player.id)
    
    if currency:
        pass

    if provider:
        # If game missing, provider is None
        query = query.where(Game.provider_id == provider)

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
    rows = result.all()
    
    items = []
    for round_obj, game_obj in rows:
        items.append({
            "round_id": round_obj.provider_round_id,
            "game_id": round_obj.game_id,
            "game_name": game_obj.name if game_obj else "Unknown Game",
            "provider": game_obj.provider_id if game_obj else "unknown",
            "status": round_obj.status,
            "total_bet": round_obj.total_bet,
            "total_win": round_obj.total_win,
            "net": round_obj.total_win - round_obj.total_bet,
            "currency": "USD", 
            "created_at": round_obj.created_at.isoformat() if round_obj.created_at else None
        })
        
    return {
        "items": items,
        "meta": {
            "total": total,
            "page": page,
            "limit": limit
        }
    }
