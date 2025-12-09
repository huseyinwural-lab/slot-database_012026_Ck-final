from fastapi import APIRouter, HTTPException, Body, Depends, Query
from typing import List, Optional, Dict
from app.models.modules import (
    KYCDocument, AdminUser, SystemLog,
    KYCLevel, KYCRule, KYCCheck, KYCAuditLog, KYCDashboardStats, KYCStatus, DocStatus
)
from config import settings
from motor.motor_asyncio import AsyncIOMotorClient
import uuid
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/api/v1", tags=["modules"])

def get_db():
    client = AsyncIOMotorClient(settings.mongo_url)
    return client[settings.db_name]

# --- KYC MODULE ---

@router.get("/kyc/dashboard", response_model=KYCDashboardStats)
async def get_kyc_dashboard():
    db = get_db()
    pending = await db.kyc.count_documents({"status": "pending"})
    review = await db.kyc.count_documents({"status": "in_review"})
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    approved = await db.kyc.count_documents({"status": "approved", "reviewed_at": {"$gte": today}})
    rejected = await db.kyc.count_documents({"status": "rejected", "reviewed_at": {"$gte": today}})
    return KYCDashboardStats(
        pending_count=pending,
        in_review_count=review,
        approved_today=approved,
        rejected_today=rejected,
        level_distribution={"Level 0": 1500, "Level 1": 450, "Level 2": 120, "Level 3": 15},
        avg_review_time_mins=45.5,
        high_risk_pending=3
    )

@router.get("/kyc/queue", response_model=List[KYCDocument])
async def get_kyc_queue(status: Optional[str] = None):
    db = get_db()
    query = {}
    if status and status != 'all': query["status"] = status
    docs = await db.kyc.find(query).sort("uploaded_at", 1).limit(100).to_list(100)
    return [KYCDocument(**d) for d in docs]

@router.get("/kyc/player/{player_id}/history", response_model=List[KYCAuditLog])
async def get_kyc_history(player_id: str):
    db = get_db()
    logs = await db.kyc_audit.find({"entity_id": player_id}).sort("timestamp", -1).to_list(100)
    return [KYCAuditLog(**l) for l in logs]

@router.get("/kyc/player/{player_id}/checks", response_model=List[KYCCheck])
async def get_kyc_checks(player_id: str):
    db = get_db()
    checks = await db.kyc_checks.find({"player_id": player_id}).to_list(100)
    return [KYCCheck(**c) for c in checks]

@router.post("/kyc/checks/run")
async def run_kyc_check(player_id: str = Body(..., embed=True), type: str = Body(..., embed=True)):
    db = get_db()
    res = "clear" if player_id != "p3" else "match"
    check = KYCCheck(
        player_id=player_id,
        type=type,
        status=res,
        result_details={"source": "MockWatchlist", "score": 0 if res == "clear" else 95}
    )
    await db.kyc_checks.insert_one(check.model_dump())
    return check

@router.post("/kyc/documents/{doc_id}/review")
async def review_kyc_doc(doc_id: str, status: str = Body(...), reason: str = Body(None), admin_id: str = Body("current_admin")):
    db = get_db()
    doc = await db.kyc.find_one({"id": doc_id})
    if not doc: raise HTTPException(404, "Document not found")
    
    update_data = {"status": status, "reviewed_at": datetime.now(timezone.utc), "reviewed_by": admin_id}
    if status == 'rejected': update_data["rejection_reason"] = reason
        
    await db.kyc.update_one({"id": doc_id}, {"$set": update_data})
    await db.kyc_audit.insert_one(KYCAuditLog(entity_id=doc['player_id'], admin_id=admin_id, action=f"doc_{status}", old_value=doc['status'], new_value=status).model_dump())
    return {"message": f"Document {status}"}

@router.get("/kyc/levels", response_model=List[KYCLevel])
async def get_kyc_levels():
    db = get_db()
    levels = await db.kyc_levels.find().to_list(100)
    return [KYCLevel(**l) for l in levels]

@router.get("/kyc/rules", response_model=List[KYCRule])
async def get_kyc_rules():
    db = get_db()
    rules = await db.kyc_rules.find().to_list(100)
    return [KYCRule(**r) for r in rules]

# --- ADMIN & LOGS ---

@router.get("/admin/users", response_model=List[AdminUser])
async def get_admins():
    db = get_db()
    return [AdminUser(**a) for a in await db.admins.find().to_list(100)]

@router.get("/logs/system", response_model=List[SystemLog])
async def get_system_logs(service: Optional[str] = None):
    db = get_db()
    query = {"service": service} if service else {}
    return [SystemLog(**l) for l in await db.system_logs.find(query).sort("timestamp", -1).limit(100).to_list(100)]

# --- SEED ---
@router.post("/modules/seed")
async def seed_modules():
    db = get_db()
    if await db.kyc.count_documents({}) == 0:
        await db.kyc.insert_many([
            KYCDocument(player_id="p1", player_username="highroller99", type="passport", status="pending", file_url="https://via.placeholder.com/300").model_dump(),
            KYCDocument(player_id="p2", player_username="newbie_luck", type="utility_bill", status="in_review", file_url="https://via.placeholder.com/300").model_dump(),
        ])
    if await db.admins.count_documents({}) == 0:
        await db.admins.insert_one(AdminUser(username="superadmin", email="admin@casino.com", role="super_admin").model_dump())
    if await db.system_logs.count_documents({}) == 0:
        await db.system_logs.insert_one(SystemLog(level="info", service="payment", message="Payment Gateway Connected").model_dump())
    return {"message": "Modules seeded"}
