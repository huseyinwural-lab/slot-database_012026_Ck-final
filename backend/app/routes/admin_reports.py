from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from sqlmodel import select, func, col
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.game_models import GameRound
from app.models.sql_models import AdminUser
from app.utils.auth import get_current_admin
from app.core.errors import AppError

router = APIRouter(prefix="/api/v1/admin/reports", tags=["admin_reports"])

@router.get("/ggr")
async def get_ggr_report(
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    currency: Optional[str] = None,
    provider: Optional[str] = None
):
    """
    GGR (Gross Gaming Revenue) Report.
    Formula: GGR = Total Bet - Total Win
    """
    
    query = select(
        func.count(GameRound.id).label("rounds_count"),
        func.sum(GameRound.total_bet).label("total_bet"),
        func.sum(GameRound.total_win).label("total_win"),
        func.count(func.distinct(GameRound.player_id)).label("active_players")
    ).where(
        GameRound.tenant_id == current_admin.tenant_id,
        GameRound.created_at >= start_date,
        GameRound.created_at <= end_date
    )
    
    if currency:
        query = query.where(GameRound.currency == currency)
        
    if provider:
        from app.models.game_models import Game
        query = query.join(Game, GameRound.game_id == Game.id)
        query = query.where(Game.provider_id == provider)
        
    result = await session.execute(query)
    row = result.first()
    
    if not row:
        return {
            "rounds_count": 0,
            "total_bet": 0.0,
            "total_win": 0.0,
            "ggr": 0.0,
            "active_players": 0,
            "currency": currency or "ALL"
        }
        
    rounds_count, total_bet, total_win, active_players = row
    
    total_bet = float(total_bet or 0.0)
    total_win = float(total_win or 0.0)
    ggr = total_bet - total_win
    
    return {
        "rounds_count": rounds_count,
        "total_bet": total_bet,
        "total_win": total_win,
        "ggr": ggr,
        "active_players": active_players,
        "currency": currency or "ALL",
        "period": {
            "start": start_date,
            "end": end_date
        }
    }
