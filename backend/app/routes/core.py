from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime, timezone
import uuid
from app.models.core import Player, Transaction, DashboardStats, PlayerStatus, TransactionStatus, TransactionType, KYCStatus
from config import settings
from motor.motor_asyncio import AsyncIOMotorClient

router = APIRouter(prefix="/api/v1", tags=["core"])

# DB Helper (Quick access)
def get_db():
    client = AsyncIOMotorClient(settings.mongo_url)
    return client[settings.db_name]

# --- DASHBOARD ---
@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    db = get_db()
    # Mock data for MVP if DB is empty
    # In real implementation, these would be aggregation queries
    
    # Check if we have any data, if not seed some mock data for demo
    count = await db.players.count_documents({})
    if count == 0:
        await seed_mock_data(db)

    # Aggregations
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Total Deposits Today
    pipeline_dep = [
        {"$match": {"type": "deposit", "status": "completed", "created_at": {"$gte": today_start}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    res_dep = await db.transactions.aggregate(pipeline_dep).to_list(1)
    total_dep = res_dep[0]['total'] if res_dep else 0.0

    # Total Withdrawals Today
    pipeline_wit = [
        {"$match": {"type": "withdrawal", "status": "completed", "created_at": {"$gte": today_start}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    res_wit = await db.transactions.aggregate(pipeline_wit).to_list(1)
    total_wit = res_wit[0]['total'] if res_wit else 0.0

    # Counts
    active_now = 42 # Mocked for "Real-time"
    pending_wit_count = await db.transactions.count_documents({"type": "withdrawal", "status": "pending"})
    pending_kyc_count = await db.players.count_documents({"kyc_status": "pending"})
    
    recent_players = await db.players.find().sort("registered_at", -1).limit(5).to_list(5)

    return DashboardStats(
        total_deposit_today=total_dep,
        total_withdrawal_today=total_wit,
        net_revenue_today=total_dep - total_wit,
        active_players_now=active_now,
        pending_withdrawals_count=pending_wit_count,
        pending_kyc_count=pending_kyc_count,
        recent_registrations=[Player(**p) for p in recent_players]
    )

# --- PLAYERS ---
@router.get("/players", response_model=List[Player])
async def get_players(
    status: Optional[PlayerStatus] = None,
    search: Optional[str] = None
):
    db = get_db()
    query = {}
    if status:
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

@router.post("/players/{player_id}/status")
async def update_player_status(player_id: str, status: PlayerStatus):
    db = get_db()
    res = await db.players.update_one({"id": player_id}, {"$set": {"status": status}})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Player not found")
    return {"message": f"Player status updated to {status}"}

# --- FINANCE ---
@router.get("/finance/transactions", response_model=List[Transaction])
async def get_transactions(
    type: Optional[TransactionType] = None,
    status: Optional[TransactionStatus] = None
):
    db = get_db()
    query = {}
    if type:
        query["type"] = type
    if status:
        query["status"] = status
        
    txs = await db.transactions.find(query).sort("created_at", -1).limit(100).to_list(100)
    return [Transaction(**t) for t in txs]

@router.post("/finance/transactions/{tx_id}/approve")
async def approve_transaction(tx_id: str):
    db = get_db()
    # Start session ideally for atomicity
    tx = await db.transactions.find_one({"id": tx_id})
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if tx['status'] != TransactionStatus.PENDING:
        raise HTTPException(status_code=400, detail="Transaction not pending")

    # Update Tx
    await db.transactions.update_one(
        {"id": tx_id}, 
        {"$set": {"status": TransactionStatus.APPROVED, "processed_at": datetime.now(timezone.utc)}}
    )
    
    # Update Balance (Simple logic)
    if tx['type'] == TransactionType.DEPOSIT:
        await db.players.update_one(
            {"id": tx['player_id']},
            {"$inc": {"balance_real": tx['amount']}}
        )
    # Withdrawal logic would assume balance was deducted at request time or needs deduction now
    # For MVP assume deduction happened at request time (locked funds), so we just mark done.
    
    return {"message": "Transaction approved"}


# --- MOCK DATA SEEDER ---
async def seed_mock_data(db):
    # Players
    players = [
        Player(id="p1", username="highroller99", email="vip@casino.com", balance_real=50000, vip_level=5, status=PlayerStatus.ACTIVE, country="Turkey").model_dump(),
        Player(id="p2", username="newbie_luck", email="new@gmail.com", balance_real=100, vip_level=1, status=PlayerStatus.ACTIVE, country="Germany").model_dump(),
        Player(id="p3", username="bonus_hunter", email="fraud@alert.com", balance_real=5, vip_level=1, status=PlayerStatus.SUSPENDED, risk_score="high", country="Russia").model_dump(),
    ]
    await db.players.insert_many(players)
    
    # Transactions
    txs = [
        Transaction(id="tx1", player_id="p1", type=TransactionType.DEPOSIT, amount=10000, status=TransactionStatus.COMPLETED, method="crypto").model_dump(),
        Transaction(id="tx2", player_id="p1", type=TransactionType.WITHDRAWAL, amount=5000, status=TransactionStatus.PENDING, method="bank_transfer").model_dump(),
        Transaction(id="tx3", player_id="p2", type=TransactionType.DEPOSIT, amount=100, status=TransactionStatus.COMPLETED, method="credit_card").model_dump(),
    ]
    await db.transactions.insert_many(txs)
