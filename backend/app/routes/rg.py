from fastapi import APIRouter, HTTPException, Body, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
import random
from app.models.modules import (
    PlayerRGProfile, RGRule, RGAlert, RGCase, RGDashboardStats,
    RGAlertSeverity, RGCaseStatus, ExclusionType, RGLimitConfig
)
from config import settings
from motor.motor_asyncio import AsyncIOMotorClient

router = APIRouter(prefix="/api/v1/rg", tags=["rg"])

def get_db():
    client = AsyncIOMotorClient(settings.mongo_url)
    return client[settings.db_name]

# --- DASHBOARD ---
@router.get("/dashboard", response_model=RGDashboardStats)
async def get_rg_dashboard():
    db = get_db()
    # Mock data
    return RGDashboardStats(
        active_self_exclusions=12,
        active_cool_offs=5,
        players_with_limits=145,
        high_loss_alerts_7d=3,
        open_cases=8,
        risk_distribution={"low": 1200, "medium": 50, "high": 10, "critical": 2}
    )

# --- ALERTS ---
@router.get("/alerts", response_model=List[RGAlert])
async def get_rg_alerts(status: Optional[str] = None):
    db = get_db()
    query = {}
    if status and status != "all": query["status"] = status
    alerts = await db.rg_alerts.find(query).sort("created_at", -1).limit(100).to_list(100)
    return [RGAlert(**a) for a in alerts]

@router.post("/alerts/resolve/{id}")
async def resolve_alert(id: str):
    db = get_db()
    await db.rg_alerts.update_one({"id": id}, {"$set": {"status": "resolved", "resolved_at": datetime.now(timezone.utc)}})
    return {"message": "Alert resolved"}

# --- CASES ---
@router.get("/cases", response_model=List[RGCase])
async def get_rg_cases(status: Optional[str] = None):
    db = get_db()
    query = {}
    if status and status != "all": query["status"] = status
    cases = await db.rg_cases.find(query).limit(100).to_list(100)
    return [RGCase(**c) for c in cases]

@router.post("/cases")
async def create_rg_case(case: RGCase):
    db = get_db()
    await db.rg_cases.insert_one(case.model_dump())
    return case

# --- PLAYER PROFILE ---
@router.get("/profile/{player_id}", response_model=PlayerRGProfile)
async def get_player_rg_profile(player_id: str):
    db = get_db()
    profile = await db.rg_profiles.find_one({"player_id": player_id})
    if not profile:
        # Create default
        profile = PlayerRGProfile(player_id=player_id).model_dump()
        await db.rg_profiles.insert_one(profile)
    return PlayerRGProfile(**profile)

@router.post("/profile/{player_id}/limits")
async def update_rg_limits(player_id: str, limits: RGLimitConfig):
    db = get_db()
    await db.rg_profiles.update_one(
        {"player_id": player_id}, 
        {"$set": {"active_limits": limits.model_dump()}},
        upsert=True
    )
    return {"message": "Limits updated"}

@router.post("/profile/{player_id}/exclude")
async def set_exclusion(player_id: str, type: str = Body(..., embed=True), duration_days: int = Body(..., embed=True)):
    db = get_db()
    end_date = datetime.now(timezone.utc) + timedelta(days=duration_days) if duration_days > 0 else None
    
    await db.rg_profiles.update_one(
        {"player_id": player_id},
        {
            "$set": {
                "exclusion_active": True,
                "exclusion_type": type,
                "exclusion_start": datetime.now(timezone.utc),
                "exclusion_end": end_date
            }
        },
        upsert=True
    )
    # Also update main player status
    status = "self_excluded" if type == "self_exclusion" else "suspended"
    await db.players.update_one({"id": player_id}, {"$set": {"status": status}})
    
    return {"message": f"Player excluded ({type})"}

# --- RULES ---
@router.get("/rules", response_model=List[RGRule])
async def get_rg_rules():
    db = get_db()
    rules = await db.rg_rules.find().to_list(100)
    return [RGRule(**r) for r in rules]

@router.post("/rules")
async def create_rg_rule(rule: RGRule):
    db = get_db()
    await db.rg_rules.insert_one(rule.model_dump())
    return rule

# --- SEED ---
@router.post("/seed")
async def seed_rg():
    db = get_db()
    if await db.rg_alerts.count_documents({}) == 0:
        await db.rg_alerts.insert_one(
            RGAlert(player_id="p1", type="high_loss", message="Lost > $5000 in 1 hour", severity=RGAlertSeverity.HIGH).model_dump()
        )
    if await db.rg_rules.count_documents({}) == 0:
        await db.rg_rules.insert_many([
            RGRule(name="High Loss Alert", severity=RGAlertSeverity.HIGH, conditions={"net_loss_24h": {">": 5000}}).model_dump(),
            RGRule(name="Session Limit", severity=RGAlertSeverity.MEDIUM, conditions={"session_time": {">": 240}}).model_dump()
        ])
    return {"message": "RG Seeded"}
