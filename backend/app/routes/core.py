from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import List, Optional, Dict
from datetime import datetime, timezone
import uuid
import random
from app.models.core import (
    Player, Transaction, DashboardStats, PlayerStatus, TransactionStatus, 
    TransactionType, KYCStatus, Game, Bonus, Ticket, TicketMessage
)
from config import settings
from motor.motor_asyncio import AsyncIOMotorClient

router = APIRouter(prefix="/api/v1", tags=["core"])

def get_db():
    client = AsyncIOMotorClient(settings.mongo_url)
    return client[settings.db_name]

# --- DASHBOARD & MOCK ---
@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    db = get_db()
    count = await db.players.count_documents({})
    if count == 0:
        await seed_mock_data(db)

    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    pipeline_dep = [
        {"$match": {"type": "deposit", "status": "completed", "created_at": {"$gte": today_start}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    res_dep = await db.transactions.aggregate(pipeline_dep).to_list(1)
    total_dep = res_dep[0]['total'] if res_dep else 0.0

    pipeline_wit = [
        {"$match": {"type": "withdrawal", "status": "completed", "created_at": {"$gte": today_start}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    res_wit = await db.transactions.aggregate(pipeline_wit).to_list(1)
    total_wit = res_wit[0]['total'] if res_wit else 0.0

    pending_wit_count = await db.transactions.count_documents({"type": "withdrawal", "status": "pending"})
    pending_kyc_count = await db.players.count_documents({"kyc_status": "pending"})
    recent_players = await db.players.find().sort("registered_at", -1).limit(5).to_list(5)

    return DashboardStats(
        total_deposit_today=total_dep,
        total_withdrawal_today=total_wit,
        net_revenue_today=total_dep - total_wit,
        active_players_now=random.randint(40, 60),
        pending_withdrawals_count=pending_wit_count,
        pending_kyc_count=pending_kyc_count,
        recent_registrations=[Player(**p) for p in recent_players]
    )

# --- PLAYERS ---
@router.get("/players", response_model=List[Player])
async def get_players(status: Optional[str] = None, search: Optional[str] = None):
    db = get_db()
    query = {}
    if status and status != "all":
        query["status"] = status
    if search:
        query["$or"] = [
            {"username": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    players = await db.players.find(query).limit(100).to_list(100)
    return [Player(**p) for p in players]

@router.get("/players/{player_id}", response_model=Player)
async def get_player_detail(player_id: str):
    db = get_db()
    player = await db.players.find_one({"id": player_id})
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return Player(**player)

@router.put("/players/{player_id}")
async def update_player(player_id: str, update_data: Dict = Body(...)):
    db = get_db()
    # Simple update
    await db.players.update_one({"id": player_id}, {"$set": update_data})
    return {"message": "Player updated"}

@router.get("/players/{player_id}/games")
async def get_player_game_history(player_id: str):
    # Mock game history
    return [
        {"game": "Sweet Bonanza", "provider": "Pragmatic", "bet": 10, "win": 0, "time": datetime.now(timezone.utc)},
        {"game": "Gates of Olympus", "provider": "Pragmatic", "bet": 5, "win": 50, "time": datetime.now(timezone.utc)},
        {"game": "Blackjack VIP", "provider": "Evolution", "bet": 100, "win": 200, "time": datetime.now(timezone.utc)},
    ]

# --- FINANCE ---
@router.get("/finance/transactions", response_model=List[Transaction])
async def get_transactions(type: Optional[str] = None):
    db = get_db()
    query = {}
    if type and type != "all":
        query["type"] = type
    txs = await db.transactions.find(query).sort("created_at", -1).limit(100).to_list(100)
    return [Transaction(**t) for t in txs]

@router.post("/finance/transactions/{tx_id}/approve")
async def approve_transaction(tx_id: str):
    db = get_db()
    tx = await db.transactions.find_one({"id": tx_id})
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    await db.transactions.update_one(
        {"id": tx_id}, 
        {"$set": {"status": "completed", "processed_at": datetime.now(timezone.utc)}}
    )
    
    if tx['type'] == 'deposit':
        await db.players.update_one({"id": tx['player_id']}, {"$inc": {"balance_real": tx['amount']}})
    
    return {"message": "Approved"}

# --- GAMES ---
@router.get("/games", response_model=List[Game])
async def get_games():
    db = get_db()
    games = await db.games.find().limit(100).to_list(100)
    return [Game(**g) for g in games]

@router.post("/games")
async def add_game(game: Game):
    db = get_db()
    await db.games.insert_one(game.model_dump())
    return game

@router.post("/games/{game_id}/toggle")
async def toggle_game_status(game_id: str):
    db = get_db()
    game = await db.games.find_one({"id": game_id})
    if game:
        new_status = "inactive" if game.get("status") == "active" else "active"
        await db.games.update_one({"id": game_id}, {"$set": {"status": new_status}})
        return {"status": new_status}
    raise HTTPException(404, "Game not found")

# --- BONUSES ---
@router.get("/bonuses", response_model=List[Bonus])
async def get_bonuses():
    db = get_db()
    bonuses = await db.bonuses.find().to_list(100)
    return [Bonus(**b) for b in bonuses]

@router.post("/bonuses")
async def create_bonus(bonus: Bonus):
    db = get_db()
    await db.bonuses.insert_one(bonus.model_dump())
    return bonus

# --- SUPPORT TICKETS ---
@router.get("/tickets", response_model=List[Ticket])
async def get_tickets():
    db = get_db()
    tickets = await db.tickets.find().sort("created_at", -1).to_list(100)
    return [Ticket(**t) for t in tickets]

@router.post("/tickets/{ticket_id}/reply")
async def reply_ticket(ticket_id: str, message: TicketMessage):
    db = get_db()
    await db.tickets.update_one(
        {"id": ticket_id}, 
        {
            "$push": {"messages": message.model_dump()},
            "$set": {"status": "answered"}
        }
    )
    return {"message": "Replied"}

# --- SEED DATA ---
async def seed_mock_data(db):
    # Players
    await db.players.insert_many([
        Player(id="p1", username="highroller99", email="vip@casino.com", balance_real=50000, vip_level=5, status=PlayerStatus.ACTIVE, country="Turkey").model_dump(),
        Player(id="p2", username="newbie_luck", email="new@gmail.com", balance_real=100, vip_level=1, status=PlayerStatus.ACTIVE, country="Germany").model_dump(),
        Player(id="p3", username="bonus_hunter", email="fraud@alert.com", balance_real=5, vip_level=1, status=PlayerStatus.SUSPENDED, risk_score="high", country="Russia").model_dump(),
    ])
    # Transactions
    await db.transactions.insert_many([
        Transaction(id="tx1", player_id="p1", type=TransactionType.DEPOSIT, amount=10000, status=TransactionStatus.COMPLETED, method="crypto").model_dump(),
        Transaction(id="tx2", player_id="p1", type=TransactionType.WITHDRAWAL, amount=5000, status=TransactionStatus.PENDING, method="bank_transfer").model_dump(),
    ])
    # Games
    await db.games.insert_many([
        Game(name="Sweet Bonanza", provider="Pragmatic Play", category="Slot", rtp=96.5).model_dump(),
        Game(name="Lightning Roulette", provider="Evolution", category="Live", rtp=97.3).model_dump(),
        Game(name="Aviator", provider="Spribe", category="Crash", rtp=97.0).model_dump(),
    ])
    # Bonuses
    await db.bonuses.insert_many([
        Bonus(name="Welcome Pack", type="deposit", amount=100, wager_req=30).model_dump(),
        Bonus(name="Weekend Cashback", type="cashback", amount=10, wager_req=1).model_dump(),
    ])
    # Tickets
    await db.tickets.insert_many([
        Ticket(id="t1", player_id="p2", player_username="newbie_luck", subject="Deposit issue", messages=[
            TicketMessage(sender="player", text="My deposit is not showing up.").model_dump()
        ]).model_dump()
    ])
