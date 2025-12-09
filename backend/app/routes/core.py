from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import uuid
import random
from app.models.core import (
    Player, Transaction, DashboardStats, PlayerStatus, TransactionStatus, 
    TransactionType, KYCStatus, Game, Bonus, Ticket, TicketMessage,
    FeatureFlag, ApprovalRequest, GameConfig, BonusRule, KPIMetric, LoginLog,
    FinancialReport, CustomTable, GameUploadLog, Paytable, JackpotConfig,
    BusinessStatus, RuntimeStatus, SpecialType, TransactionTimeline
)
from app.models.modules import KYCDocument
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
    if await db.players.count_documents({}) == 0:
        await seed_mock_data(db)

    # Mock aggregation for MVP speed
    bets_today = 154200.50
    wins_today = 138000.00
    ggr_today = bets_today - wins_today
    bonuses_today = 5000.00
    ngr_today = ggr_today - bonuses_today - (ggr_today * 0.15)
    
    pending_wit = await db.transactions.count_documents({"type": "withdrawal", "status": "pending"})
    pending_kyc = await db.players.count_documents({"kyc_status": "pending"})
    recent_players = await db.players.find().sort("registered_at", -1).limit(5).to_list(5)

    return DashboardStats(
        ggr=KPIMetric(value=ggr_today, change_percent=12.5, trend="up"),
        ngr=KPIMetric(value=ngr_today, change_percent=10.2, trend="up"),
        total_bets=KPIMetric(value=bets_today, change_percent=8.4, trend="up"),
        total_wins=KPIMetric(value=wins_today, change_percent=5.2, trend="up"),
        provider_health=[{"name": "Pragmatic", "status": "UP"}, {"name": "Evolution", "status": "UP"}],
        payment_health=[{"name": "Papara", "status": "UP"}, {"name": "Crypto", "status": "UP"}],
        risk_alerts={"high_risk_withdrawals": 3, "vpn_detected": 45},
        online_users=124, active_sessions=90, peak_sessions_24h=340,
        bonuses_given_today_count=145, bonuses_given_today_amount=bonuses_today,
        top_games=[{"name": "Sweet Bonanza", "provider": "Pragmatic", "revenue": 12500, "rtp_today": 94.2}],
        recent_registrations=[Player(**p) for p in recent_players],
        pending_withdrawals_count=pending_wit, pending_kyc_count=pending_kyc
    )

# --- PLAYERS ---
@router.get("/players", response_model=List[Player])
async def get_players(
    status: Optional[str] = None, 
    search: Optional[str] = None,
    vip_level: Optional[int] = None,
    risk_score: Optional[str] = None,
    country: Optional[str] = None
):
    db = get_db()
    query = {}
    if status and status != "all":
        query["status"] = status
    if vip_level:
        query["vip_level"] = vip_level
    if risk_score and risk_score != "all":
        query["risk_score"] = risk_score
    if country and country != "all":
        query["country"] = country
        
    if search:
        query["$or"] = [
            {"username": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
            {"id": search} 
        ]
        
    players = await db.players.find(query).sort("registered_at", -1).limit(100).to_list(100)
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
    await db.audit_logs.insert_one({
        "admin_id": "current_admin", "action": "update_player", "target_id": player_id,
        "details": str(update_data), "timestamp": datetime.now(timezone.utc)
    })
    await db.players.update_one({"id": player_id}, {"$set": update_data})
    return {"message": "Player updated"}

@router.post("/players/{player_id}/balance")
async def manual_balance_adjustment(player_id: str, amount: float = Body(...), type: str = Body(...), note: str = Body(...)):
    db = get_db()
    if abs(amount) > 1000:
        approval_req = ApprovalRequest(
            type="manual_adjustment", related_entity_id=player_id, requester_admin="current_admin",
            amount=amount, details={"type": type, "note": note}
        )
        await db.approvals.insert_one(approval_req.model_dump())
        return {"message": "Adjustment > $1000. Moved to Approval Queue."}

    field = "balance_real" if type == "real" else "balance_bonus"
    # Also update deposits/withdrawals/net if needed
    await db.players.update_one({"id": player_id}, {"$inc": {field: amount}})
    tx = Transaction(
        id=f"adj-{uuid.uuid4().hex[:8]}", player_id=player_id, type=TransactionType.ADJUSTMENT,
        amount=amount, status=TransactionStatus.COMPLETED, method="manual", admin_note=note
    )
    await db.transactions.insert_one(tx.model_dump())
    return {"message": "Balance updated"}

@router.get("/players/{player_id}/kyc", response_model=List[KYCDocument])
async def get_player_kyc(player_id: str):
    db = get_db()
    docs = await db.kyc.find({"player_id": player_id}).to_list(100)
    return [KYCDocument(**d) for d in docs]

@router.get("/players/{player_id}/transactions", response_model=List[Transaction])
async def get_player_transactions(player_id: str):
    db = get_db()
    txs = await db.transactions.find({"player_id": player_id}).sort("created_at", -1).limit(100).to_list(100)
    return [Transaction(**t) for t in txs]

@router.get("/players/{player_id}/logs", response_model=List[LoginLog])
async def get_player_logs(player_id: str):
    return [
        LoginLog(player_id=player_id, ip_address="192.168.1.1", location="Istanbul, TR", device_info="Chrome / Win10", status="success"),
        LoginLog(player_id=player_id, ip_address="192.168.1.1", location="Istanbul, TR", device_info="Chrome / Win10", status="success", timestamp=datetime.now(timezone.utc)-timedelta(days=1)),
    ]

# --- FINANCE & APPROVALS ---
@router.get("/finance/transactions", response_model=List[Transaction])
async def get_transactions(
    type: Optional[str] = None,
    status: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    player_search: Optional[str] = None,
    provider: Optional[str] = None,
    country: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    db = get_db()
    query = {}
    if type and type != "all":
        query["type"] = type
    if status and status != "all":
        query["status"] = status
    if provider and provider != "all":
        query["provider"] = provider
    if country and country != "all":
        query["country"] = country
        
    if min_amount or max_amount:
        query["amount"] = {}
        if min_amount: query["amount"]["$gte"] = min_amount
        if max_amount: query["amount"]["$lte"] = max_amount
    if start_date:
        query["created_at"] = {"$gte": start_date}
    if player_search:
        p = await db.players.find_one({"username": player_search})
        if p: query["player_id"] = p['id']
        else: query["id"] = player_search

    txs = await db.transactions.find(query).sort("created_at", -1).limit(100).to_list(100)
    return [Transaction(**t) for t in txs]

@router.post("/finance/transactions/{tx_id}/action")
async def action_transaction(tx_id: str, action: str = Body(..., embed=True), reason: str = Body(None, embed=True)):
    db = get_db()
    tx = await db.transactions.find_one({"id": tx_id})
    if not tx:
        raise HTTPException(404, "Transaction not found")
    
    admin = "current_admin"
    new_timeline_entry = None
    
    if action == "approve":
        if tx['type'] == 'withdrawal' and tx['amount'] > 1000 and tx['status'] == 'pending':
            approval_req = ApprovalRequest(
                type="withdrawal_high_value", related_entity_id=tx_id, requester_admin="system_bot",
                amount=tx['amount'], details={"player_id": tx['player_id'], "method": tx['method']}
            )
            await db.approvals.insert_one(approval_req.model_dump())
            await db.transactions.update_one({"id": tx_id}, {"$set": {"status": "waiting_second_approval"}})
            return {"message": "High value withdrawal moved to Approval Queue"}
        new_status = "completed"
        if tx['type'] == 'deposit':
            await db.players.update_one({"id": tx['player_id']}, {"$inc": {"balance_real": tx['amount'], "total_deposits": tx['amount'], "net_position": tx['amount']}})
        if tx['type'] == 'withdrawal':
             await db.players.update_one({"id": tx['player_id']}, {"$inc": {"total_withdrawals": tx['amount'], "net_position": -tx['amount'], "pending_withdrawals": -tx['amount']}})
        new_timeline_entry = TransactionTimeline(status="completed", description="Transaction Approved", operator=admin)

    elif action == "reject":
        new_status = "rejected"
        if tx['type'] == 'withdrawal':
            # Refund
            await db.players.update_one({"id": tx['player_id']}, {"$inc": {"balance_real": tx['amount'], "pending_withdrawals": -tx['amount']}})
        new_timeline_entry = TransactionTimeline(status="rejected", description=f"Transaction Rejected: {reason}", operator=admin)
            
    elif action == "fraud":
        new_status = "fraud_flagged"
        await db.players.update_one({"id": tx['player_id']}, {"$set": {"status": "suspended", "risk_score": "high"}})
        new_timeline_entry = TransactionTimeline(status="fraud_flagged", description="Flagged for Fraud", operator=admin)
        
    elif action == "retry_callback":
        # Mock retry
        new_timeline_entry = TransactionTimeline(status=tx['status'], description="Callback Retried manually", operator=admin)
        await db.transactions.update_one({"id": tx_id}, {"$push": {"timeline": new_timeline_entry.model_dump()}})
        return {"message": "Callback retried"}
        
    elif action == "pending_review":
        new_status = "pending" # Or specific review status
        new_timeline_entry = TransactionTimeline(status="pending", description="Marked for Manual Review", operator=admin)
        
    else:
        raise HTTPException(400, "Invalid action")

    update_ops = {
        "$set": {"status": new_status, "processed_at": datetime.now(timezone.utc), "admin_note": reason},
    }
    
    if new_timeline_entry:
        update_ops["$push"] = {"timeline": new_timeline_entry.model_dump()}

    await db.transactions.update_one({"id": tx_id}, update_ops)
    return {"message": f"Transaction {new_status}"}

@router.get("/finance/reports", response_model=FinancialReport)
async def get_financial_reports(start_date: Optional[datetime] = None, end_date: Optional[datetime] = None):
    db = get_db()
    pipeline = [{"$match": {"status": "completed"}}, {"$group": {"_id": "$type", "total": {"$sum": "$amount"}}}]
    res = await db.transactions.aggregate(pipeline).to_list(10)
    totals = {r['_id']: r['total'] for r in res}
    total_dep = totals.get('deposit', 0)
    total_wit = totals.get('withdrawal', 0)
    providers = {"Papara": total_dep * 0.4, "Crypto": total_dep * 0.3, "Bank Transfer": total_dep * 0.3}
    daily = [{"date": "2025-12-08", "deposit": 14000, "withdrawal": 2000}, {"date": "2025-12-09", "deposit": 10100, "withdrawal": 5000}]
    return FinancialReport(
        total_deposit=total_dep, total_withdrawal=total_wit, net_cashflow=total_dep - total_wit,
        provider_breakdown=providers, daily_stats=daily
    )

# --- APPROVAL QUEUE ---
@router.get("/approvals", response_model=List[ApprovalRequest])
async def get_approvals():
    db = get_db()
    approvals = await db.approvals.find({"status": "pending"}).to_list(100)
    return [ApprovalRequest(**a) for a in approvals]

@router.post("/approvals/{req_id}/action")
async def action_approval(req_id: str, action: str = Body(..., embed=True)):
    db = get_db()
    req = await db.approvals.find_one({"id": req_id})
    if not req:
        raise HTTPException(404, "Request not found")
    
    new_status = "approved" if action == "approve" else "rejected"
    await db.approvals.update_one({"id": req_id}, {"$set": {"status": new_status}})

    if new_status == "approved" and req['type'] == 'withdrawal_high_value':
        # Approve underlying tx
        tx = await db.transactions.find_one({"id": req['related_entity_id']})
        if tx:
             await db.transactions.update_one(
                {"id": req['related_entity_id']}, 
                {"$set": {"status": "completed", "processed_at": datetime.now(timezone.utc)}}
            )
             await db.players.update_one({"id": tx['player_id']}, {"$inc": {"total_withdrawals": tx['amount'], "net_position": -tx['amount'], "pending_withdrawals": -tx['amount']}})

    return {"message": f"Request {new_status}"}

# --- FEATURE FLAGS ---
@router.get("/features", response_model=List[FeatureFlag])
async def get_feature_flags():
    db = get_db()
    flags = await db.features.find().to_list(100)
    return [FeatureFlag(**f) for f in flags]

@router.post("/features")
async def create_feature_flag(flag: FeatureFlag):
    db = get_db()
    await db.features.insert_one(flag.model_dump())
    return flag

@router.post("/features/{flag_id}/toggle")
async def toggle_feature(flag_id: str):
    db = get_db()
    flag = await db.features.find_one({"id": flag_id})
    if flag:
        new_val = not flag['is_enabled']
        await db.features.update_one({"id": flag_id}, {"$set": {"is_enabled": new_val}})
        return {"is_enabled": new_val}
    raise HTTPException(404, "Flag not found")

# --- GLOBAL SEARCH ---
@router.get("/search")
async def global_search(q: str):
    db = get_db()
    results = []
    
    players = await db.players.find({
        "$or": [{"username": {"$regex": q, "$options": "i"}}, {"email": {"$regex": q, "$options": "i"}}, {"id": q}]
    }).limit(5).to_list(5)
    for p in players:
        results.append({"type": "player", "title": p['username'], "id": p['id'], "details": p['email']})

    txs = await db.transactions.find({"id": q}).limit(5).to_list(5)
    for t in txs:
        results.append({"type": "transaction", "title": f"TX: {t['amount']}", "id": t['id'], "details": t['status']})

    return results

# --- CUSTOM TABLES ---
@router.get("/tables", response_model=List[CustomTable])
async def get_tables():
    db = get_db()
    tables = await db.tables.find().to_list(100)
    return [CustomTable(**t) for t in tables]

@router.post("/tables")
async def create_table(table: CustomTable):
    db = get_db()
    await db.tables.insert_one(table.model_dump())
    return table

@router.post("/tables/{table_id}/status")
async def update_table_status(table_id: str, status: str = Body(..., embed=True)):
    db = get_db()
    await db.tables.update_one({"id": table_id}, {"$set": {"status": status}})
    return {"message": "Status updated"}

# --- GAMES & ADVANCED SETTINGS ---
@router.get("/games", response_model=List[Game])
async def get_games():
    db = get_db()
    games = await db.games.find().limit(100).to_list(100)
    
    # Auto-Suggestion Logic (Mock)
    enhanced_games = []
    for g in games:
        # Check if should be suggested as VIP
        config = g.get('configuration', {})
        # Handle case where configuration is a dict or model dump
        min_bet = config.get('min_bet', 0) if isinstance(config, dict) else 0
        
        if min_bet > 10 and not g.get('is_special_game'):
            g['suggestion_reason'] = "High min bet detected - Candidate for VIP"
        enhanced_games.append(Game(**g))
        
    return enhanced_games

@router.post("/games")
async def add_game(game: Game):
    db = get_db()
    await db.games.insert_one(game.model_dump())
    return game

@router.put("/games/{game_id}")
async def update_game_config(game_id: str, config: GameConfig):
    db = get_db()
    current = await db.games.find_one({"id": game_id})
    if current:
        old_ver = current.get("configuration", {}).get("version", "1.0.0")
        parts = old_ver.split(".")
        new_ver = f"{parts[0]}.{parts[1]}.{int(parts[2])+1}"
        config.version = new_ver
        
    res = await db.games.update_one({"id": game_id}, {"$set": {"configuration": config.model_dump()}})
    if res.matched_count == 0:
        raise HTTPException(404, "Game not found")
    return {"message": "Game configuration updated", "version": config.version}

@router.put("/games/{game_id}/details")
async def update_game_details(game_id: str, details: Dict[str, Any] = Body(...)):
    db = get_db()
    await db.audit_logs.insert_one({
        "admin_id": "current_admin",
        "action": "update_game_details",
        "target_id": game_id,
        "details": str(details),
        "timestamp": datetime.now(timezone.utc)
    })
    
    allowed = ["name", "category", "provider", "image_url", "tags", 
               "business_status", "runtime_status", "is_special_game", "special_type"]
    update_data = {k: v for k, v in details.items() if k in allowed}
    
    if not update_data:
        raise HTTPException(400, "No valid fields to update")

    res = await db.games.update_one({"id": game_id}, {"$set": update_data})
    if res.matched_count == 0:
        raise HTTPException(404, "Game not found")
        
    return {"message": "Game details updated"}

@router.post("/games/{game_id}/toggle")
async def toggle_game_status(game_id: str):
    db = get_db()
    game = await db.games.find_one({"id": game_id})
    if game:
        # Default behavior: Toggle Business Status Active/Suspended
        new_status = BusinessStatus.SUSPENDED if game.get("business_status") == BusinessStatus.ACTIVE else BusinessStatus.ACTIVE
        await db.games.update_one({"id": game_id}, {"$set": {"business_status": new_status}})
        return {"status": new_status}
    raise HTTPException(404, "Game not found")

@router.post("/games/upload")
async def upload_games(
    provider: str = Body(...),
    method: str = Body(...), 
    game_ids: List[str] = Body([])
):
    db = get_db()
    imported_count = 0
    if method == "fetch_api":
        new_games = [
            Game(name=f"{provider} Slot {random.randint(100,999)}", provider=provider, category="Slot", 
                 configuration=GameConfig(rtp=96.5).model_dump()).model_dump()
            for _ in range(3)
        ]
        if new_games:
            await db.games.insert_many(new_games)
            imported_count = len(new_games)
            
    await db.upload_logs.insert_one(GameUploadLog(
        admin_id="current_admin", provider=provider, total_games=imported_count, 
        success_count=imported_count, error_count=0
    ).model_dump())
    
    return {"message": f"Successfully imported {imported_count} games from {provider}"}

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
    await db.players.insert_many([
        Player(
            id="p1", 
            username="highroller99", 
            email="vip@casino.com", 
            balance_real=50000, 
            vip_level=5, 
            status=PlayerStatus.ACTIVE, 
            country="Turkey", 
            first_name="Mehmet", 
            last_name="Yilmaz", 
            tags=["high_roller", "whale"],
            total_deposits=120000,
            total_withdrawals=45000,
            net_position=75000,
            last_login=datetime.now(timezone.utc),
            last_ip="192.168.1.1",
            risk_score="low",
            fraud_score=12,
            kyc_status=KYCStatus.APPROVED,
            kyc_level=3,
            affiliate_source="google_ads"
        ).model_dump(),
        Player(
            id="p2", 
            username="newbie_luck", 
            email="new@gmail.com", 
            balance_real=100, 
            vip_level=1, 
            status=PlayerStatus.ACTIVE, 
            country="Germany", 
            first_name="Hans", 
            last_name="Muller",
            total_deposits=200,
            total_withdrawals=0,
            net_position=200,
            last_login=datetime.now(timezone.utc)-timedelta(days=2),
            risk_score="low",
            fraud_score=5,
            affiliate_source="direct"
        ).model_dump(),
        Player(
            id="p3", 
            username="bonus_hunter", 
            email="fraud@alert.com", 
            balance_real=5, 
            vip_level=1, 
            status=PlayerStatus.SUSPENDED, 
            risk_score="high", 
            fraud_score=88,
            country="Russia", 
            tags=["bonus_abuse", "multi_account"],
            total_deposits=50,
            total_withdrawals=0,
            net_position=50,
            account_flags=["bonus_abuse"],
            kyc_status=KYCStatus.REJECTED
        ).model_dump(),
    ])
    await db.transactions.insert_many([
        Transaction(
            id="tx1", 
            player_id="p1", 
            type=TransactionType.DEPOSIT, 
            amount=10000, 
            status=TransactionStatus.COMPLETED, 
            method="crypto", 
            player_username="highroller99",
            provider="CoinPayments",
            provider_tx_id="CP_123456789",
            ip_address="88.241.12.1",
            device_info="iPhone 14 / Mobile Safari",
            country="TR",
            fee=50.0,
            net_amount=9950.0,
            timeline=[
                TransactionTimeline(status="pending", description="Created").model_dump(),
                TransactionTimeline(status="completed", description="Confirmed by Blockchain").model_dump()
            ]
        ).model_dump(),
        Transaction(
            id="tx2", 
            player_id="p1", 
            type=TransactionType.WITHDRAWAL, 
            amount=5000, 
            status=TransactionStatus.PENDING, 
            method="bank_transfer", 
            player_username="highroller99",
            provider="InternalBank",
            country="TR",
            fee=0.0,
            net_amount=5000.0,
            timeline=[
                TransactionTimeline(status="pending", description="Request Created").model_dump()
            ]
        ).model_dump(),
    ])
    await db.games.insert_many([
        Game(name="Sweet Bonanza", provider="Pragmatic Play", category="Slot", business_status=BusinessStatus.ACTIVE, runtime_status=RuntimeStatus.ONLINE, configuration=GameConfig(rtp=96.5).model_dump()).model_dump(),
        Game(name="VIP Roulette", provider="Evolution", category="Live", is_special_game=True, special_type=SpecialType.VIP, business_status=BusinessStatus.ACTIVE, runtime_status=RuntimeStatus.ONLINE, configuration=GameConfig(min_bet=100).model_dump()).model_dump(),
    ])
    await db.bonuses.insert_many([
        Bonus(name="Welcome Offer", type="deposit_match", auto_apply=True, rules=BonusRule(reward_percentage=100).model_dump()).model_dump(),
        Bonus(name="Weekly Cashback", type="periodic_cashback", rules=BonusRule(cashback_percentage=10).model_dump()).model_dump(),
    ])
    await db.tables.insert_many([
        CustomTable(name="VIP Blackjack TR", game_type="Blackjack", provider="Evolution", table_type="vip", min_bet=100, max_bet=10000, business_status=BusinessStatus.ACTIVE, runtime_status=RuntimeStatus.ONLINE).model_dump()
    ])
