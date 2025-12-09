from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime, timedelta, timezone
import random
import uuid
import asyncio
from app.models.core import Player, Transaction, TransactionType, TransactionStatus, PlayerStatus
from config import settings
from motor.motor_asyncio import AsyncIOMotorClient

router = APIRouter(prefix="/api/v1/simulator", tags=["simulator"])

def get_db():
    client = AsyncIOMotorClient(settings.mongo_url)
    return client[settings.db_name]

# Models
class SimConfig(BaseModel):
    count: int = 10
    delay_ms: int = 100

class PlayerSimRequest(SimConfig):
    country_code: str = "TR"
    risk_profile: Literal["low", "medium", "high"] = "low"

class GameSimRequest(SimConfig):
    game_provider: str = "Pragmatic Play"
    win_rate: float = 0.3 # 30% win chance

class FinanceSimRequest(BaseModel):
    type: Literal["deposit", "withdrawal"]
    amount_range: List[int] = [100, 5000]
    success_rate: float = 0.9

class TimeTravelRequest(BaseModel):
    days_offset: int

class SimulationLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    details: dict = {}

# Background Tasks
async def run_player_sim(config: PlayerSimRequest):
    db = get_db()
    logs = []
    for i in range(config.count):
        pid = f"sim-{uuid.uuid4().hex[:8]}"
        p = Player(
            id=pid,
            username=f"SimUser_{i}_{random.randint(100,999)}",
            email=f"sim_{i}@test.com",
            country=config.country_code,
            risk_score=config.risk_profile,
            balance_real=random.randint(100, 10000),
            status=PlayerStatus.ACTIVE
        )
        await db.players.insert_one(p.model_dump())
        logs.append(SimulationLog(type="player_sim", message=f"Created player {p.username}", details={"id": pid}))
        await asyncio.sleep(config.delay_ms / 1000)
    
    await db.sim_logs.insert_many([l.model_dump() for l in logs])

async def run_game_sim(config: GameSimRequest):
    db = get_db()
    players = await db.players.find({}).limit(50).to_list(50)
    if not players: return

    logs = []
    for i in range(config.count):
        player = random.choice(players)
        bet = random.randint(1, 100)
        
        # --- LUCK BOOST LOGIC ---
        player_luck_factor = player.get("luck_boost_factor", 1.0)
        player_boost_spins = player.get("luck_boost_remaining_spins", 0)
        
        adjusted_win_rate = config.win_rate
        boost_active = False

        if player_boost_spins > 0 and player_luck_factor > 1.0:
            adjusted_win_rate = min(config.win_rate * player_luck_factor, 0.95) # Cap at 95%
            boost_active = True
            # Decrement spins (in a real scenario we'd batch update, here simpler)
            await db.players.update_one({"id": player['id']}, {"$inc": {"luck_boost_remaining_spins": -1}})

        is_win = random.random() < adjusted_win_rate
        win_amount = bet * random.uniform(1.5, 50.0) if is_win else 0
        
        # Log Transaction (Bet)
        await db.transactions.insert_one(Transaction(
            id=f"sim-bet-{uuid.uuid4().hex[:8]}",
            player_id=player['id'],
            type=TransactionType.ADJUSTMENT, 
            amount=-bet,
            status=TransactionStatus.COMPLETED,
            method=config.game_provider
        ).model_dump())

        if is_win:
             await db.transactions.insert_one(Transaction(
                id=f"sim-win-{uuid.uuid4().hex[:8]}",
                player_id=player['id'],
                type=TransactionType.ADJUSTMENT,
                amount=win_amount,
                status=TransactionStatus.COMPLETED,
                method=config.game_provider
            ).model_dump())

        logs.append(SimulationLog(
            type="game_sim", 
            message=f"Spin for {player['username']} {'(BOOSTED)' if boost_active else ''}: {'WIN' if is_win else 'LOSS'}", 
            details={"bet": bet, "win": win_amount, "luck_factor": player_luck_factor if boost_active else 1.0}
        ))
        await asyncio.sleep(config.delay_ms / 1000)
    
    await db.sim_logs.insert_many([l.model_dump() for l in logs])

# Endpoints
@router.post("/players/start")
async def start_player_sim(config: PlayerSimRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_player_sim, config)
    return {"message": f"Started simulation for {config.count} players"}

@router.post("/games/start")
async def start_game_sim(config: GameSimRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_game_sim, config)
    return {"message": f"Started game simulation with {config.count} rounds"}

@router.post("/finance/test")
async def test_finance_callback(req: FinanceSimRequest):
    db = get_db()
    # Immediate execution for testing
    amount = random.randint(req.amount_range[0], req.amount_range[1])
    is_success = random.random() < req.success_rate
    
    tx = Transaction(
        id=f"sim-pay-{uuid.uuid4().hex[:8]}",
        player_id="sim-tester", 
        type=TransactionType.DEPOSIT if req.type == "deposit" else TransactionType.WITHDRAWAL,
        amount=amount,
        status=TransactionStatus.COMPLETED if is_success else TransactionStatus.FAILED,
        method="SimulatedProvider",
        admin_note="Generated by Finance Simulator"
    )
    return {
        "transaction": tx,
        "provider_response": {
            "code": "200" if is_success else "500",
            "message": "Success" if is_success else "Provider Timeout"
        }
    }

@router.post("/time-travel")
async def time_travel(req: TimeTravelRequest):
    db = get_db()
    new_time = datetime.now(timezone.utc) + timedelta(days=req.days_offset)
    await db.sim_logs.insert_one(SimulationLog(
        type="time_travel",
        message=f"System time shifted by {req.days_offset} days",
        details={"virtual_time": new_time.isoformat()}
    ).model_dump())
    return {"message": "Time travel successful", "virtual_time": new_time}

@router.get("/logs")
async def get_sim_logs(limit: int = 50):
    db = get_db()
    logs = await db.sim_logs.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit).to_list(limit)
    return logs
