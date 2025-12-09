from fastapi import APIRouter, HTTPException, Body, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
import random
from app.models.modules import (
    RiskRule, RiskCase, DeviceProfile, RiskAlert, RiskDashboardStats,
    RiskCategory, RiskSeverity, RiskActionType, RiskCaseStatus
)
from config import settings
from motor.motor_asyncio import AsyncIOMotorClient

router = APIRouter(prefix="/api/v1/risk", tags=["risk"])

def get_db():
    client = AsyncIOMotorClient(settings.mongo_url)
    return client[settings.db_name]

# --- DASHBOARD ---
@router.get("/dashboard", response_model=RiskDashboardStats)
async def get_risk_dashboard():
    db = get_db()
    # Mock aggregation
    return RiskDashboardStats(
        daily_alerts=await db.risk_alerts.count_documents({}),
        open_cases=await db.risk_cases.count_documents({"status": "open"}),
        high_risk_players=await db.players.count_documents({"risk_score": "high"}),
        suspicious_withdrawals=3,
        bonus_abuse_alerts=12,
        risk_trend=[{"date": "2025-12-08", "count": 10}, {"date": "2025-12-09", "count": 15}],
        category_breakdown={"payment": 40, "bonus": 30, "device": 20, "geo": 10}
    )

# --- RULES ENGINE ---
@router.get("/rules", response_model=List[RiskRule])
async def get_risk_rules(category: Optional[str] = None):
    db = get_db()
    query = {}
    if category and category != "all": query["category"] = category
    rules = await db.risk_rules.find(query).to_list(100)
    return [RiskRule(**r) for r in rules]

@router.post("/rules")
async def create_risk_rule(rule: RiskRule):
    db = get_db()
    await db.risk_rules.insert_one(rule.model_dump())
    return rule

@router.post("/rules/{id}/toggle")
async def toggle_rule(id: str):
    db = get_db()
    rule = await db.risk_rules.find_one({"id": id})
    if rule:
        new_status = "paused" if rule["status"] == "active" else "active"
        await db.risk_rules.update_one({"id": id}, {"$set": {"status": new_status}})
        return {"status": new_status}
    raise HTTPException(404, "Rule not found")

# --- CASES ---
@router.get("/cases", response_model=List[RiskCase])
async def get_cases(status: Optional[str] = None):
    db = get_db()
    query = {}
    if status and status != "all": query["status"] = status
    cases = await db.risk_cases.find(query).sort("created_at", -1).limit(100).to_list(100)
    return [RiskCase(**c) for c in cases]

@router.post("/cases")
async def create_case(case: RiskCase):
    db = get_db()
    await db.risk_cases.insert_one(case.model_dump())
    return case

@router.put("/cases/{id}/status")
async def update_case_status(id: str, status: str = Body(..., embed=True), note: str = Body(None, embed=True)):
    db = get_db()
    await db.risk_cases.update_one(
        {"id": id}, 
        {
            "$set": {"status": status, "updated_at": datetime.now(timezone.utc)},
            "$push": {"notes": {"admin": "current_admin", "text": note, "time": datetime.now(timezone.utc)}}
        }
    )
    return {"message": "Status updated"}

# --- DEVICE INTELLIGENCE ---
@router.get("/devices", response_model=List[DeviceProfile])
async def get_devices(player_id: Optional[str] = None):
    db = get_db()
    query = {}
    if player_id: query["player_ids"] = player_id
    devices = await db.risk_devices.find(query).limit(100).to_list(100)
    return [DeviceProfile(**d) for d in devices]

# --- ALERTS ---
@router.get("/alerts", response_model=List[RiskAlert])
async def get_alerts():
    db = get_db()
    alerts = await db.risk_alerts.find().sort("timestamp", -1).limit(100).to_list(100)
    return [RiskAlert(**a) for a in alerts]

# --- SEED ---
@router.post("/seed")
async def seed_risk():
    db = get_db()
    if await db.risk_rules.count_documents({}) == 0:
        await db.risk_rules.insert_many([
            RiskRule(name="Multi-Account Device", category=RiskCategory.DEVICE, severity=RiskSeverity.HIGH, score_impact=50).model_dump(),
            RiskRule(name="Bonus Abuse Pattern", category=RiskCategory.BONUS_ABUSE, severity=RiskSeverity.MEDIUM, score_impact=30).model_dump(),
            RiskRule(name="High Velocity Withdrawal", category=RiskCategory.PAYMENT, severity=RiskSeverity.CRITICAL, score_impact=100).model_dump(),
        ])
    if await db.risk_cases.count_documents({}) == 0:
        await db.risk_cases.insert_one(
            RiskCase(player_id="p3", risk_score=85, severity=RiskSeverity.HIGH, triggered_rules=["Bonus Abuse"]).model_dump()
        )
    if await db.risk_alerts.count_documents({}) == 0:
        await db.risk_alerts.insert_one(
            RiskAlert(type="payment_fraud", message="Suspicious bin match", severity=RiskSeverity.HIGH).model_dump()
        )
    return {"message": "Risk Seeded"}
