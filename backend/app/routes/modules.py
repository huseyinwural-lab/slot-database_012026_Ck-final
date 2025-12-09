from fastapi import APIRouter, HTTPException, Body, Depends, Query
from typing import List, Optional, Dict
from app.models.modules import (
    KYCDocument, Campaign, CMSPage, Banner, Affiliate, 
    RiskRule, AdminUser, SystemLog, RGLimit,
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
    # Mock aggregation for speed
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
async def get_kyc_queue(
    status: Optional[str] = None,
    level: Optional[str] = None,
    risk: Optional[str] = None
):
    db = get_db()
    query = {}
    if status and status != 'all': query["status"] = status
    # Note: real implementation would join player data for risk/level filters
    # here we assume just fetching docs for now
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
    # Mock 3rd party check
    res = "clear" if player_id != "p3" else "match" # p3 is our mock fraud user
    check = KYCCheck(
        player_id=player_id,
        type=type,
        status=res,
        result_details={"source": "MockWatchlist", "score": 0 if res == "clear" else 95}
    )
    await db.kyc_checks.insert_one(check.model_dump())
    return check

@router.post("/kyc/documents/{doc_id}/review")
async def review_kyc_doc(
    doc_id: str, 
    status: str = Body(...), 
    reason: str = Body(None),
    admin_id: str = Body("current_admin")
):
    db = get_db()
    doc = await db.kyc.find_one({"id": doc_id})
    if not doc: raise HTTPException(404, "Document not found")
    
    update_data = {
        "status": status,
        "reviewed_at": datetime.now(timezone.utc),
        "reviewed_by": admin_id
    }
    if status == 'rejected':
        update_data["rejection_reason"] = reason
        
    await db.kyc.update_one({"id": doc_id}, {"$set": update_data})
    
    # Audit Log
    await db.kyc_audit.insert_one(KYCAuditLog(
        entity_id=doc['player_id'],
        admin_id=admin_id,
        action=f"doc_{status}",
        old_value=doc['status'],
        new_value=status
    ).model_dump())
    
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

# --- EXISTING MODULES ---

@router.get("/crm/campaigns", response_model=List[Campaign])
async def get_campaigns():
    db = get_db()
    return [Campaign(**c) for c in await db.campaigns.find().to_list(100)]

@router.post("/crm/campaigns")
async def create_campaign(camp: Campaign):
    db = get_db()
    await db.campaigns.insert_one(camp.model_dump())
    return camp

@router.get("/cms/pages", response_model=List[CMSPage])
async def get_pages():
    db = get_db()
    return [CMSPage(**p) for p in await db.pages.find().to_list(100)]

@router.get("/cms/banners", response_model=List[Banner])
async def get_banners():
    db = get_db()
    return [Banner(**b) for b in await db.banners.find().to_list(100)]

@router.get("/affiliates", response_model=List[Affiliate])
async def get_affiliates():
    db = get_db()
    return [Affiliate(**a) for a in await db.affiliates.find().to_list(100)]

@router.get("/risk/rules", response_model=List[RiskRule])
async def get_risk_rules():
    db = get_db()
    return [RiskRule(**r) for r in await db.risk_rules.find().to_list(100)]

@router.get("/admin/users", response_model=List[AdminUser])
async def get_admins():
    db = get_db()
    return [AdminUser(**a) for a in await db.admins.find().to_list(100)]

@router.get("/logs/system", response_model=List[SystemLog])
async def get_system_logs(service: Optional[str] = None):
    db = get_db()
    query = {"service": service} if service else {}
    return [SystemLog(**l) for l in await db.system_logs.find(query).sort("timestamp", -1).limit(100).to_list(100)]

@router.get("/rg/limits", response_model=List[RGLimit])
async def get_rg_limits():
    db = get_db()
    return [RGLimit(**l) for l in await db.rg_limits.find().to_list(100)]

@router.post("/modules/seed")
async def seed_modules():
    db = get_db()
    # KYC Seed
    if await db.kyc.count_documents({}) == 0:
        await db.kyc.insert_many([
            KYCDocument(player_id="p1", player_username="highroller99", type="passport", status="pending", file_url="https://via.placeholder.com/300").model_dump(),
            KYCDocument(player_id="p2", player_username="newbie_luck", type="utility_bill", status="in_review", file_url="https://via.placeholder.com/300").model_dump(),
            KYCDocument(player_id="p3", player_username="bonus_hunter", type="id_card", status="rejected", rejection_reason="Blurry image", file_url="https://via.placeholder.com/300").model_dump(),
        ])
    if await db.kyc_levels.count_documents({}) == 0:
        await db.kyc_levels.insert_many([
            KYCLevel(name="Level 1", description="Basic Identity", requirements=["id_card"]).model_dump(),
            KYCLevel(name="Level 2", description="Address Verification", requirements=["id_card", "address_proof"]).model_dump(),
        ])
    if await db.kyc_rules.count_documents({}) == 0:
        await db.kyc_rules.insert_one(KYCRule(name="High Deposit", condition="deposit > 2000", target_level="Level 2", action="restrict").model_dump())

    # Other Modules Seed
    if await db.campaigns.count_documents({}) == 0:
        await db.campaigns.insert_one(Campaign(name="Weekend Reload", subject="Get 50% Bonus", content="Hi {name}, ...", segment="active_players", channel="email").model_dump())
    if await db.banners.count_documents({}) == 0:
        await db.banners.insert_one(Banner(title="Main Promo", image_url="/banner1.jpg", target_url="/promos", position="home_slider").model_dump())
    if await db.affiliates.count_documents({}) == 0:
        await db.affiliates.insert_one(Affiliate(name="BestCasinoSites", email="partner@bestcasinos.com", total_earnings=1250.50).model_dump())
    if await db.risk_rules.count_documents({}) == 0:
        await db.risk_rules.insert_one(RiskRule(name="High Deposit", condition="amount > 5000", action="flag", severity="medium").model_dump())
    if await db.admins.count_documents({}) == 0:
        await db.admins.insert_one(AdminUser(username="superadmin", email="admin@casino.com", role="super_admin").model_dump())
    if await db.system_logs.count_documents({}) == 0:
        await db.system_logs.insert_one(SystemLog(level="info", service="payment", message="Payment Gateway Connected").model_dump())

    return {"message": "Modules seeded"}
