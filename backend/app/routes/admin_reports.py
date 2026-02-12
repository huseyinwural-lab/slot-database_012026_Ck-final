from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, Dict, List
from datetime import datetime, timedelta, date
from sqlmodel import select, func, col
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.game_models import GameRound, DailyGameAggregation, Game
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
    GGR Report (Hybrid: Aggregation + Live).
    """
    
    # 1. Split range into Historical (<= yesterday) and Live (today)
    today = datetime.utcnow().date()
    req_start = start_date.date()
    req_end = end_date.date()
    
    historical_start = req_start
    historical_end = min(req_end, today - timedelta(days=1))
    
    live_start = None
    if req_end >= today:
        live_start = max(req_start, today)
    
    # 2. Query Aggregations (Historical)
    agg_rounds = 0
    agg_bet = 0.0
    agg_win = 0.0
    
    if historical_start <= historical_end:
        agg_query = select(
            func.sum(DailyGameAggregation.rounds_count),
            func.sum(DailyGameAggregation.total_bet),
            func.sum(DailyGameAggregation.total_win)
        ).where(
            DailyGameAggregation.tenant_id == current_admin.tenant_id,
            DailyGameAggregation.date_val >= historical_start,
            DailyGameAggregation.date_val <= historical_end
        )
        
        if currency:
            agg_query = agg_query.where(DailyGameAggregation.currency == currency)
        if provider:
            agg_query = agg_query.where(DailyGameAggregation.provider == provider)
            
        agg_res = await session.execute(agg_query)
        agg_row = agg_res.first()
        if agg_row:
            agg_rounds = int(agg_row[0] or 0)
            agg_bet = float(agg_row[1] or 0.0)
            agg_win = float(agg_row[2] or 0.0)

    # 3. Query Live Data (Today)
    live_rounds = 0
    live_bet = 0.0
    live_win = 0.0
    
    if live_start:
        live_dt_start = datetime.combine(live_start, datetime.min.time())
        live_query = select(
            func.count(GameRound.id),
            func.sum(GameRound.total_bet),
            func.sum(GameRound.total_win)
        ).where(
            GameRound.tenant_id == current_admin.tenant_id,
            GameRound.created_at >= live_dt_start
        )
        
        if currency:
            live_query = live_query.where(GameRound.currency == currency)
        
        if provider:
            live_query = live_query.join(Game, GameRound.game_id == Game.id)
            live_query = live_query.where(Game.provider_id == provider)
            
        live_res = await session.execute(live_query)
        live_row = live_res.first()
        if live_row:
            live_rounds = int(live_row[0] or 0)
            live_bet = float(live_row[1] or 0.0)
            live_win = float(live_row[2] or 0.0)

    # 4. Merge
    total_bet = agg_bet + live_bet
    total_win = agg_win + live_win
    ggr = total_bet - total_win
    
    return {
        "rounds_count": agg_rounds + live_rounds,
        "total_bet": total_bet,
        "total_win": total_win,
        "ggr": ggr,
        "currency": currency or "ALL",
        "period": {
            "start": start_date,
            "end": end_date
        },
        "source": {
            "historical_days": (historical_end - historical_start).days + 1 if historical_start <= historical_end else 0,
            "live_included": bool(live_start)
        }
    }

@router.get("/financials")
async def get_financial_report(
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
    start_date: datetime = Query(...),
    end_date: datetime = Query(...)
):
    """
    Financial Report (Ledger Based).
    Summarizes Gross, Discount, and Net amounts from the ledger.
    """
    from app.repositories.ledger_repo import LedgerTransaction
    
    query = select(
        func.sum(LedgerTransaction.gross_amount),
        func.sum(LedgerTransaction.discount_amount),
        func.sum(LedgerTransaction.net_amount) # Or amount if net_amount is not populated
    ).where(
        LedgerTransaction.tenant_id == current_admin.tenant_id,
        LedgerTransaction.created_at >= start_date,
        LedgerTransaction.created_at <= end_date,
        LedgerTransaction.gross_amount != None # Only count pricing-related txs
    )
    
    res = await session.execute(query)
    row = res.first()
    
    gross = float(row[0] or 0.0)
    discount = float(row[1] or 0.0)
    net = float(row[2] or 0.0)
    
    # If net_amount wasn't explicitly stored in early tests, fallback:
    # In V2 service we store it.
    
    return {
        "period": {"start": start_date, "end": end_date},
        "gross_revenue": gross,
        "total_discounts": discount,
        "net_revenue": net,
        "effective_discount_rate": (discount / gross) if gross > 0 else 0.0
    }
