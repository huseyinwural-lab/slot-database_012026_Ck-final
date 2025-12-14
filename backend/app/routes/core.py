from fastapi import APIRouter, HTTPException, Depends, Query, Body, Request
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
import uuid
from sqlmodel import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.core import (
    DashboardStats, KPIMetric
)
from app.models.sql_models import (
    Player, Transaction, Game, AdminUser
)
from app.schemas.player import PlayerPublic
from app.utils.auth import get_current_admin
from app.utils.pagination import get_pagination_params
from app.models.common import PaginationMeta, PaginatedResponse, PaginationParams
from app.core.database import get_session

# Router
router = APIRouter(prefix="/api/v1", tags=["core"])

# --- DASHBOARD ---
@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    session: AsyncSession = Depends(get_session)
):
    # Total Bets (Sum of 'bet' transactions)
    bets_query = select(func.sum(Transaction.amount)).where(Transaction.type == "bet")
    bets_result = await session.execute(bets_query)
    bets_today = bets_result.scalar() or 0.0

    # Total Wins
    wins_query = select(func.sum(Transaction.amount)).where(Transaction.type == "win")
    wins_result = await session.execute(wins_query)
    wins_today = wins_result.scalar() or 0.0

    ggr_today = bets_today - wins_today
    bonuses_today = 0.0 
    ngr_today = ggr_today - bonuses_today - (ggr_today * 0.15)
    
    # Counts
    pending_wit = (await session.execute(select(func.count()).select_from(Transaction).where(Transaction.type == "withdrawal", Transaction.status == "pending"))).scalar() or 0
    pending_kyc = (await session.execute(select(func.count()).select_from(Player).where(Player.kyc_status == "pending"))).scalar() or 0
    
    # Recent Players (placeholder - future use)
    _recent_players = (await session.execute(select(Player).order_by(Player.registered_at.desc()).limit(5))).scalars().all()

    return DashboardStats(
        ggr=KPIMetric(value=ggr_today, change_percent=0.0, trend="up"),
        ngr=KPIMetric(value=ngr_today, change_percent=0.0, trend="up"),
        total_bets=KPIMetric(value=bets_today, change_percent=0.0, trend="up"),
        total_wins=KPIMetric(value=wins_today, change_percent=0.0, trend="up"),
        provider_health=[{"name": "Pragmatic", "status": "UP"}],
        payment_health=[{"name": "Papara", "status": "UP"}],
        risk_alerts={"high_risk_withdrawals": 0, "vpn_detected": 0},
        online_users=0, 
        active_sessions=0, 
        peak_sessions_24h=0,
        bonuses_given_today_count=0, 
        bonuses_given_today_amount=0.0,
        top_games=[],
        recent_registrations=[], 
        pending_withdrawals_count=pending_wit, 
        pending_kyc_count=pending_kyc
    )

# --- PLAYERS ---
@router.get("/players", response_model=PaginatedResponse[PlayerPublic])
async def get_players(
    request: Request,
    status: Optional[str] = None,
    search: Optional[str] = None,
    pagination: PaginationParams = Depends(get_pagination_params),
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    query = select(Player)
    
    # Tenant Filter
    if not current_admin.is_platform_owner:
        query = query.where(Player.tenant_id == current_admin.tenant_id)
    
    if status and status != "all":
        query = query.where(Player.status == status)
        
    if search:
        query = query.where(
            (Player.username.ilike(f"%{search}%")) | 
            (Player.email.ilike(f"%{search}%"))
        )

    query = query.order_by(Player.registered_at.desc())

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_query)).scalar() or 0

    # Paginate
    query = query.offset((pagination.page - 1) * pagination.page_size).limit(pagination.page_size)
    result = await session.execute(query)
    players = result.scalars().all()

    return {
        "items": players,
        "meta": PaginationMeta(total=total, page=pagination.page, page_size=pagination.page_size),
    }

@router.get("/players/{player_id}", response_model=Player)
async def get_player_detail(player_id: str, session: AsyncSession = Depends(get_session)):
    player = await session.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player

@router.put("/players/{player_id}")
async def update_player(player_id: str, update_data: Dict = Body(...), session: AsyncSession = Depends(get_session)):
    player = await session.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
        
    for k, v in update_data.items():
        if hasattr(player, k):
            setattr(player, k, v)
            
    session.add(player)
    await session.commit()
    return {"message": "Player updated"}

# --- FINANCE ---
@router.get("/finance/transactions", response_model=PaginatedResponse[Transaction])
async def get_transactions(
    request: Request,
    type: Optional[str] = None,
    status: Optional[str] = None,
    pagination: PaginationParams = Depends(get_pagination_params),
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    query = select(Transaction)
    
    if not current_admin.is_platform_owner:
        query = query.where(Transaction.tenant_id == current_admin.tenant_id)
        
    if type and type != "all":
        query = query.where(Transaction.type == type)
    if status and status != "all":
        query = query.where(Transaction.status == status)
        
    query = query.order_by(Transaction.created_at.desc())
    
    count_query = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_query)).scalar() or 0
    
    query = query.offset((pagination.page - 1) * pagination.page_size).limit(pagination.page_size)
    result = await session.execute(query)
    txs = result.scalars().all()
    
    return {
        "items": txs,
        "meta": PaginationMeta(total=total, page=pagination.page, page_size=pagination.page_size),
    }

# --- GAMES ---
# NOTE: This endpoint uses PaginatedResponse format. Frontend must match this.
@router.get("/games", response_model=dict) # Changing to dict to be safe with structure
async def get_games(
    request: Request,
    category: Optional[str] = None,
    pagination: PaginationParams = Depends(get_pagination_params),
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    query = select(Game)
    
    if not current_admin.is_platform_owner:
        query = query.where(Game.tenant_id == current_admin.tenant_id)
        
    if category and category != "all":
        query = query.where(Game.category == category)
        
    query = query.order_by(Game.created_at.desc())
    
    count_query = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_query)).scalar() or 0
    
    query = query.offset((pagination.page - 1) * pagination.page_size).limit(pagination.page_size)
    result = await session.execute(query)
    games = result.scalars().all()
    
    # Frontend likely expects ARRAY for games list based on VipGames.jsx: const all = res.data;
    # But GameManagement.jsx might expect pagination.
    # Let's check common usage. 
    # VipGames.jsx does: const res = await api.get('/v1/games'); const all = res.data;
    # This implies it expects an ARRAY directly, NOT { items: [...] }.
    # BUT GameManagement.jsx likely uses table with pagination.
    
    # Conflict: VipGames expects Array, GameManagement expects Paginated.
    # SOLUTION: Return array if pagination not requested or handle both.
    # OR better: Standardize Frontend to always read .items if present.
    # Since I cannot easily change all Frontend files in one shot without risk, 
    # I will modify this endpoint to return ARRAY if page_size is large (mocking "all") 
    # OR check if we can return a structure that satisfies both (impossible).
    
    # Let's return the standard { items: [], meta: {} } 
    # AND I will patch VipGames.jsx to read .items if it exists.
    
    return {
        "items": games,
        "meta": PaginationMeta(total=total, page=pagination.page, page_size=pagination.page_size),
        # Fallback for simple array access (might not work if they map directly)
        # We will fix Frontend VipGames.jsx
    }
