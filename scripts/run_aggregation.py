import asyncio
import os
import logging
from datetime import datetime, timedelta, date
from sqlalchemy.future import select
from sqlalchemy import func
from app.core.database import async_session
from app.models.game_models import GameRound, DailyGameAggregation, Game

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aggregator")

async def run_daily_aggregation(target_date: date):
    logger.info(f"Starting aggregation for {target_date}")
    
    start_dt = datetime.combine(target_date, datetime.min.time())
    end_dt = datetime.combine(target_date, datetime.max.time())
    
    async with async_session() as session:
        # 1. Aggregate from GameRound
        # Group by Tenant, Provider (via Game), Currency
        stmt = (
            select(
                GameRound.tenant_id,
                Game.provider_id.label("provider"),
                GameRound.currency,
                func.count(GameRound.id).label("rounds_count"),
                func.sum(GameRound.total_bet).label("total_bet"),
                func.sum(GameRound.total_win).label("total_win"),
                func.count(func.distinct(GameRound.player_id)).label("active_players")
            )
            .join(Game, GameRound.game_id == Game.id)
            .where(
                GameRound.created_at >= start_dt,
                GameRound.created_at <= end_dt
            )
            .group_by(
                GameRound.tenant_id,
                Game.provider_id,
                GameRound.currency
            )
        )
        
        result = await session.execute(stmt)
        rows = result.all()
        
        logger.info(f"Found {len(rows)} aggregation groups")
        
        # 2. Upsert into DailyGameAggregation
        for row in rows:
            tenant_id, provider, currency, rounds, bet, win, players = row
            
            # Check existing using python field name 'date_val' which maps to 'date'
            existing_stmt = select(DailyGameAggregation).where(
                DailyGameAggregation.tenant_id == tenant_id,
                DailyGameAggregation.date_val == target_date,
                DailyGameAggregation.provider == provider,
                DailyGameAggregation.currency == currency
            )
            existing = (await session.execute(existing_stmt)).scalars().first()
            
            if existing:
                existing.rounds_count = rounds
                existing.total_bet = float(bet or 0)
                existing.total_win = float(win or 0)
                existing.active_players = players
                existing.updated_at = datetime.utcnow()
                session.add(existing)
            else:
                new_agg = DailyGameAggregation(
                    tenant_id=tenant_id,
                    date_val=target_date,
                    provider=provider or "unknown",
                    currency=currency or "USD",
                    rounds_count=rounds,
                    total_bet=float(bet or 0),
                    total_win=float(win or 0),
                    active_players=players,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                session.add(new_agg)
        
        await session.commit()
        logger.info("Aggregation complete")

if __name__ == "__main__":
    yesterday = date.today() 
    import sys
    if len(sys.argv) > 1:
        yesterday = datetime.strptime(sys.argv[1], "%Y-%m-%d").date()
        
    asyncio.run(run_daily_aggregation(yesterday))
