from fastapi import APIRouter, HTTPException, Body
from typing import List, Optional
from app.models.modules import (
    KYCDocument, Campaign, CMSPage, Banner, Affiliate, 
    RiskRule, AdminUser, SystemLog, RGLimit
)
from config import settings
from motor.motor_asyncio import AsyncIOMotorClient
import uuid
from datetime import datetime, timezone

router = APIRouter(prefix="/api/v1", tags=["modules"])

def get_db():
    client = AsyncIOMotorClient(settings.mongo_url)
    return client[settings.db_name]

# --- KYC ---
@router.get("/kyc", response_model=List[KYCDocument])
async def get_kyc_docs(status: Optional[str] = None):
    db = get_db()
    query = {"status": status} if status else {}
    docs = await db.kyc.find(query).limit(100).to_list(100)
    return [KYCDocument(**d) for d in docs]

@router.post("/kyc/{doc_id}/review")
async def review_kyc(doc_id: str, status: str = Body(..., embed=True), note: str = Body(None, embed=True)):
    db = get_db()
    await db.kyc.update_one(
        {"id": doc_id}, 
        {"$set": {"status": status, "admin_note": note, "reviewed_at": datetime.now(timezone.utc)}}
    )
    # If approved, update player kyc_status (mock logic)
    doc = await db.kyc.find_one({"id": doc_id})
    if doc and status == 'approved':
        await db.players.update_one({"id": doc['player_id']}, {"$set": {"kyc_status": "approved"}})
    return {"message": "Reviewed"}

# --- CRM ---
@router.get("/crm/campaigns", response_model=List[Campaign])
async def get_campaigns():
    db = get_db()
    return [Campaign(**c) for c in await db.campaigns.find().to_list(100)]

@router.post("/crm/campaigns")
async def create_campaign(camp: Campaign):
    db = get_db()
    await db.campaigns.insert_one(camp.model_dump())
    return camp

# --- CMS ---
@router.get("/cms/pages", response_model=List[CMSPage])
async def get_pages():
    db = get_db()
    return [CMSPage(**p) for p in await db.pages.find().to_list(100)]

@router.get("/cms/banners", response_model=List[Banner])
async def get_banners():
    db = get_db()
    return [Banner(**b) for b in await db.banners.find().to_list(100)]

# --- AFFILIATES ---
@router.get("/affiliates", response_model=List[Affiliate])
async def get_affiliates():
    db = get_db()
    return [Affiliate(**a) for a in await db.affiliates.find().to_list(100)]

# --- RISK ---
@router.get("/risk/rules", response_model=List[RiskRule])
async def get_risk_rules():
    db = get_db()
    return [RiskRule(**r) for r in await db.risk_rules.find().to_list(100)]

# --- ADMIN USERS ---
@router.get("/admin/users", response_model=List[AdminUser])
async def get_admins():
    db = get_db()
    return [AdminUser(**a) for a in await db.admins.find().to_list(100)]

# --- LOGS ---
@router.get("/logs/system", response_model=List[SystemLog])
async def get_system_logs(service: Optional[str] = None):
    db = get_db()
    query = {"service": service} if service else {}
    return [SystemLog(**l) for l in await db.system_logs.find(query).sort("timestamp", -1).limit(100).to_list(100)]

# --- RESPONSIBLE GAMING ---
@router.get("/rg/limits", response_model=List[RGLimit])
async def get_rg_limits():
    db = get_db()
    return [RGLimit(**l) for l in await db.rg_limits.find().to_list(100)]


# --- SEED DATA (Auto-Run if empty) ---
@router.post("/modules/seed")
async def seed_modules():
    db = get_db()
    # KYC
    if await db.kyc.count_documents({}) == 0:
        await db.kyc.insert_one(KYCDocument(player_id="p1", player_username="highroller99", type="passport", file_url="https://via.placeholder.com/300").model_dump())
    
    # CRM
    if await db.campaigns.count_documents({}) == 0:
        await db.campaigns.insert_one(Campaign(name="Weekend Reload", subject="Get 50% Bonus", content="Hi {name}, ...", segment="active_players", channel="email").model_dump())

    # CMS
    if await db.banners.count_documents({}) == 0:
        await db.banners.insert_one(Banner(title="Main Promo", image_url="/banner1.jpg", target_url="/promos", position="home_slider").model_dump())
    
    # Affiliates
    if await db.affiliates.count_documents({}) == 0:
        await db.affiliates.insert_one(Affiliate(name="BestCasinoSites", email="partner@bestcasinos.com", total_earnings=1250.50).model_dump())

    # Risk
    if await db.risk_rules.count_documents({}) == 0:
        await db.risk_rules.insert_one(RiskRule(name="High Deposit", condition="amount > 5000", action="flag", severity="medium").model_dump())
        
    # Admin
    if await db.admins.count_documents({}) == 0:
        await db.admins.insert_one(AdminUser(username="superadmin", email="admin@casino.com", role="super_admin").model_dump())

    # Logs
    if await db.system_logs.count_documents({}) == 0:
        await db.system_logs.insert_one(SystemLog(level="info", service="payment", message="Payment Gateway Connected").model_dump())

    return {"message": "Modules seeded"}
