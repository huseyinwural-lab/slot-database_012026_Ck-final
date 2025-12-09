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

# --- GAME REPORTS ---
@router.get("/games")
async def get_game_performance():
    return [
        {"game": "Sweet Bonanza", "provider": "Pragmatic", "bets": 150000, "wins": 140000, "ggr": 10000},
        {"game": "Lightning Roulette", "provider": "Evolution", "bets": 80000, "wins": 75000, "ggr": 5000}
    ]

# --- PROVIDER REPORTS ---
@router.get("/providers")
async def get_provider_reports():
    return [
        {"provider": "Pragmatic Play", "ggr": 55000, "rtp": 96.5, "bet_count": 50000},
        {"provider": "Evolution", "ggr": 45000, "rtp": 97.2, "bet_count": 30000},
        {"provider": "NetEnt", "ggr": 15000, "rtp": 95.8, "bet_count": 12000}
    ]

# --- BONUS REPORTS ---
@router.get("/bonuses")
async def get_bonus_reports():
    return [
        {"type": "Welcome Bonus", "cost": 15000, "claimed": 500, "roi": 120},
        {"type": "Cashback", "cost": 5000, "claimed": 200, "roi": 85},
        {"type": "Free Spins", "cost": 2000, "claimed": 1000, "roi": 150}
    ]

# --- AFFILIATE REPORTS ---
@router.get("/affiliates")
async def get_affiliate_reports():
    return [
        {"affiliate": "BestBonus", "ftd": 150, "cpa_cost": 7500, "revenue_share": 2500},
        {"affiliate": "CasinoGuru", "ftd": 50, "cpa_cost": 2500, "revenue_share": 1000}
    ]

# --- RISK REPORTS ---
@router.get("/risk")
async def get_risk_reports():
    return [
        {"metric": "Fraud Incidents", "count": 12, "prevented_loss": 50000},
        {"metric": "Device Clusters", "count": 5, "prevented_loss": 12000},
        {"metric": "Bonus Abuse", "count": 25, "prevented_loss": 8000}
    ]

# --- RG REPORTS ---
@router.get("/rg")
async def get_rg_reports():
    return [
        {"metric": "Self Exclusions", "count": 12, "trend": "+2"},
        {"metric": "Loss Limits Hit", "count": 45, "trend": "+5"},
        {"metric": "Cool Offs", "count": 8, "trend": "-1"}
    ]

# --- KYC REPORTS ---
@router.get("/kyc")
async def get_kyc_reports():
    return [
        {"status": "Approved", "count": 150, "avg_time": "25m"},
        {"status": "Rejected", "count": 15, "avg_time": "15m"},
        {"status": "Pending", "count": 5, "avg_time": "-"}
    ]

# --- CRM REPORTS ---
@router.get("/crm")
async def get_crm_reports():
    return [
        {"campaign": "Weekend Reload", "channel": "Email", "sent": 5000, "open_rate": 25.5, "conversion": 5.2},
        {"campaign": "Welcome SMS", "channel": "SMS", "sent": 1000, "open_rate": 98.0, "conversion": 12.5}
    ]

# --- CMS REPORTS ---
@router.get("/cms")
async def get_cms_reports():
    return [
        {"page": "Homepage", "views": 15000, "bounce_rate": 35},
        {"page": "Promotions", "views": 5000, "bounce_rate": 45},
        {"banner": "Welcome Offer", "impressions": 12000, "ctr": 2.5}
    ]

# --- OPERATIONAL REPORTS ---
@router.get("/operational")
async def get_operational_reports():
    return [
        {"metric": "Support Ticket Volume", "value": 145},
        {"metric": "Avg Support Response", "value": "2m"},
        {"metric": "Approval Queue Pending", "value": 8},
        {"metric": "Avg Withdrawal Time", "value": "15m"}
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
    job.status = "ready"
    job.download_url = "https://example.com/report.pdf"
    await db.export_jobs.insert_one(job.model_dump())
    return job

# --- AUDIT ---
@router.get("/audit")
async def get_report_audit():
    return [{"admin": "current_admin", "action": "Downloaded Financial Report", "time": datetime.now(timezone.utc)}]
