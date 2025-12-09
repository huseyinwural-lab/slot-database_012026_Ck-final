from fastapi import APIRouter, HTTPException, Body, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
from app.models.modules import ReportSchedule, ExportJob
from config import settings
from motor.motor_asyncio import AsyncIOMotorClient

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])

def get_db():
    client = AsyncIOMotorClient(settings.mongo_url)
    return client[settings.db_name]

# --- OVERVIEW KPI ---
@router.get("/overview")
async def get_overview():
    # Mock KPI data
    return {
        "ggr": 16200.5,
        "ngr": 8770.4,
        "total_deposits": 154200.0,
        "total_withdrawals": 138000.0,
        "active_players": 124,
        "new_registrations": 45,
        "bonus_cost": 5000.0,
        "fraud_loss": 0.0
    }

# --- FINANCIAL REPORTS ---
@router.get("/financial")
async def get_financial_report(type: str = "daily"):
    # Mock Financial Data
    return [
        {"date": "2025-12-09", "ggr": 5000, "ngr": 4200, "deposits": 10000, "withdrawals": 5000},
        {"date": "2025-12-08", "ggr": 4500, "ngr": 3800, "deposits": 9000, "withdrawals": 4500}
    ]

# --- PLAYER REPORTS ---
@router.get("/players/ltv")
async def get_player_ltv():
    return [
        {"player_id": "p1", "deposits": 50000, "withdrawals": 5000, "net_revenue": 45000, "vip": 5},
        {"player_id": "p2", "deposits": 100, "withdrawals": 0, "net_revenue": 100, "vip": 1}
    ]

# --- GAME PERFORMANCE ---
@router.get("/games")
async def get_game_performance():
    return [
        {"game": "Sweet Bonanza", "provider": "Pragmatic", "bets": 150000, "wins": 140000, "ggr": 10000},
        {"game": "Lightning Roulette", "provider": "Evolution", "bets": 80000, "wins": 75000, "ggr": 5000}
    ]

# --- SCHEDULES ---
@router.get("/schedules", response_model=List[ReportSchedule])
async def get_schedules():
    db = get_db()
    return [ReportSchedule(**s) for s in await db.report_schedules.find().to_list(100)]

@router.post("/schedules")
async def create_schedule(sch: ReportSchedule):
    db = get_db()
    await db.report_schedules.insert_one(sch.model_dump())
    return sch

# --- EXPORTS ---
@router.get("/exports", response_model=List[ExportJob])
async def get_exports():
    db = get_db()
    return [ExportJob(**e) for e in await db.export_jobs.find().sort("created_at", -1).to_list(100)]

@router.post("/exports")
async def create_export(job: ExportJob):
    db = get_db()
    job.status = "ready" # Mock immediate success
    job.download_url = "https://example.com/report.pdf"
    await db.export_jobs.insert_one(job.model_dump())
    return job

# --- AUDIT ---
@router.get("/audit")
async def get_report_audit():
    return [
        {"admin": "current_admin", "action": "Downloaded Financial Report", "time": datetime.now(timezone.utc)}
    ]
