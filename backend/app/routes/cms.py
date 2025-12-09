from fastapi import APIRouter, HTTPException, Body, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
from app.models.modules import (
    CMSPage, CMSBanner, CMSMenu, CMSCollection, CMSPopup, CMSTranslation,
    CMSAuditLog, CMSDashboardStats, CMSStatus, CMSPageType, CMSBannerPosition,
    CMSLayout, CMSMedia, CMSLegalDoc, CMSExperiment, CMSMaintenance
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

# --- HOMEPAGE LAYOUT ---
@router.get("/layout", response_model=List[CMSLayout])
async def get_layouts():
    db = get_db()
    return [CMSLayout(**l) for l in await db.cms_layouts.find().to_list(100)]

@router.post("/layout")
async def save_layout(layout: CMSLayout):
    db = get_db()
    await db.cms_layouts.insert_one(layout.model_dump())
    return layout

# --- COLLECTIONS ---
@router.get("/collections", response_model=List[CMSCollection])
async def get_collections():
    db = get_db()
    return [CMSCollection(**c) for c in await db.cms_collections.find().to_list(100)]

@router.post("/collections")
async def create_collection(coll: CMSCollection):
    db = get_db()
    await db.cms_collections.insert_one(coll.model_dump())
    return coll

# --- POPUPS ---
@router.get("/popups", response_model=List[CMSPopup])
async def get_popups():
    db = get_db()
    return [CMSPopup(**p) for p in await db.cms_popups.find().to_list(100)]

@router.post("/popups")
async def create_popup(popup: CMSPopup):
    db = get_db()
    await db.cms_popups.insert_one(popup.model_dump())
    return popup

# --- TRANSLATIONS ---
@router.get("/translations", response_model=List[CMSTranslation])
async def get_translations():
    db = get_db()
    return [CMSTranslation(**t) for t in await db.cms_translations.find().to_list(100)]

@router.post("/translations")
async def create_translation(trans: CMSTranslation):
    db = get_db()
    await db.cms_translations.insert_one(trans.model_dump())
    return trans

# --- MEDIA LIBRARY ---
@router.get("/media", response_model=List[CMSMedia])
async def get_media():
    db = get_db()
    return [CMSMedia(**m) for m in await db.cms_media.find().to_list(100)]

@router.post("/media")
async def upload_media(media: CMSMedia):
    db = get_db()
    await db.cms_media.insert_one(media.model_dump())
    return media

# --- LEGAL ---
@router.get("/legal", response_model=List[CMSLegalDoc])
async def get_legal_docs():
    db = get_db()
    return [CMSLegalDoc(**d) for d in await db.cms_legal.find().to_list(100)]

@router.post("/legal")
async def create_legal_doc(doc: CMSLegalDoc):
    db = get_db()
    await db.cms_legal.insert_one(doc.model_dump())
    return doc

# --- EXPERIMENTS ---
@router.get("/experiments", response_model=List[CMSExperiment])
async def get_experiments():
    db = get_db()
    return [CMSExperiment(**e) for e in await db.cms_experiments.find().to_list(100)]

@router.post("/experiments")
async def create_experiment(exp: CMSExperiment):
    db = get_db()
    await db.cms_experiments.insert_one(exp.model_dump())
    return exp

# --- AUDIT ---
@router.get("/audit", response_model=List[CMSAuditLog])
async def get_audit_logs():
    db = get_db()
    return [CMSAuditLog(**l) for l in await db.cms_audit.find().sort("timestamp", -1).limit(100).to_list(100)]

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
    if await db.cms_collections.count_documents({}) == 0:
        await db.cms_collections.insert_one(CMSCollection(name="New Games", type="dynamic").model_dump())
    if await db.cms_popups.count_documents({}) == 0:
        await db.cms_popups.insert_one(CMSPopup(title="Welcome", content="Hi!", type="entry").model_dump())
    if await db.cms_media.count_documents({}) == 0:
        await db.cms_media.insert_one(CMSMedia(filename="banner1.jpg", type="image", url="/images/b1.jpg", size=1024).model_dump())
    
    return {"message": "CMS Seeded"}
