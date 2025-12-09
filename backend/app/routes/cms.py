from fastapi import APIRouter, HTTPException, Body, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
from app.models.modules import (
    CMSPage, CMSBanner, CMSMenu, CMSCollection, CMSPopup, CMSTranslation,
    CMSAuditLog, CMSDashboardStats, CMSStatus, CMSPageType, CMSBannerPosition
)
from config import settings
from motor.motor_asyncio import AsyncIOMotorClient

router = APIRouter(prefix="/api/v1/cms", tags=["cms"])

def get_db():
    client = AsyncIOMotorClient(settings.mongo_url)
    return client[settings.db_name]

# --- DASHBOARD ---
@router.get("/dashboard", response_model=CMSDashboardStats)
async def get_cms_dashboard():
    db = get_db()
    # Mock data
    return CMSDashboardStats(
        published_pages=await db.cms_pages.count_documents({"status": "published"}),
        active_banners=await db.cms_banners.count_documents({"status": "published"}),
        draft_count=5,
        scheduled_count=2,
        recent_changes=[]
    )

# --- PAGES ---
@router.get("/pages", response_model=List[CMSPage])
async def get_pages(status: Optional[str] = None):
    db = get_db()
    query = {}
    if status and status != "all": query["status"] = status
    pages = await db.cms_pages.find(query).to_list(100)
    return [CMSPage(**p) for p in pages]

@router.post("/pages")
async def create_page(page: CMSPage):
    db = get_db()
    await db.cms_pages.insert_one(page.model_dump())
    return page

@router.put("/pages/{id}")
async def update_page(id: str, update: Dict[str, Any] = Body(...)):
    db = get_db()
    await db.cms_pages.update_one({"id": id}, {"$set": update})
    return {"message": "Page updated"}

# --- BANNERS ---
@router.get("/banners", response_model=List[CMSBanner])
async def get_banners():
    db = get_db()
    banners = await db.cms_banners.find().sort("priority", -1).to_list(100)
    return [CMSBanner(**b) for b in banners]

@router.post("/banners")
async def create_banner(banner: CMSBanner):
    db = get_db()
    await db.cms_banners.insert_one(banner.model_dump())
    return banner

# --- MENUS ---
@router.get("/menus", response_model=List[CMSMenu])
async def get_menus():
    db = get_db()
    menus = await db.cms_menus.find().to_list(100)
    return [CMSMenu(**m) for m in menus]

@router.post("/menus")
async def create_menu(menu: CMSMenu):
    db = get_db()
    await db.cms_menus.insert_one(menu.model_dump())
    return menu

# --- SEED ---
@router.post("/seed")
async def seed_cms():
    db = get_db()
    if await db.cms_pages.count_documents({}) == 0:
        await db.cms_pages.insert_many([
            CMSPage(title="Homepage", slug="/", template=CMSPageType.HOMEPAGE, status=CMSStatus.PUBLISHED).model_dump(),
            CMSPage(title="Promotions", slug="/promos", template=CMSPageType.PROMO, status=CMSStatus.PUBLISHED).model_dump()
        ])
    if await db.cms_banners.count_documents({}) == 0:
        await db.cms_banners.insert_one(
            CMSBanner(title="Welcome Bonus", position=CMSBannerPosition.HOME_HERO, image_desktop="banner1.jpg", status=CMSStatus.PUBLISHED).model_dump()
        )
    return {"message": "CMS Seeded"}
