from fastapi import APIRouter, HTTPException, Body, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
import random
from app.models.modules import (
    Affiliate, AffiliateOffer, TrackingLink, Conversion, Payout, Creative,
    AffiliateStatus, CommissionModel, CommissionPlan
)
from config import settings
from motor.motor_asyncio import AsyncIOMotorClient

router = APIRouter(prefix="/api/v1/affiliates", tags=["affiliates"])

def get_db():
    client = AsyncIOMotorClient(settings.mongo_url)
    return client[settings.db_name]

# --- AFFILIATES ---
@router.get("/", response_model=List[Affiliate])
async def get_affiliates(status: Optional[str] = None):
    db = get_db()
    query = {}
    if status and status != "all":
        query["status"] = status
    affiliates = await db.affiliates.find(query).to_list(100)
    return [Affiliate(**a) for a in affiliates]

@router.post("/")
async def create_affiliate(aff: Affiliate):
    db = get_db()
    # Ensure id and basic fields
    await db.affiliates.insert_one(aff.model_dump())
    return aff

@router.put("/{aff_id}/status")
async def update_affiliate_status(aff_id: str, status: str = Body(..., embed=True)):
    db = get_db()
    await db.affiliates.update_one({"id": aff_id}, {"$set": {"status": status}})
    return {"message": "Status updated"}

# --- OFFERS ---
@router.get("/offers", response_model=List[AffiliateOffer])
async def get_offers():
    db = get_db()
    offers = await db.affiliate_offers.find().to_list(100)
    return [AffiliateOffer(**o) for o in offers]

@router.post("/offers")
async def create_offer(offer: AffiliateOffer):
    db = get_db()
    await db.affiliate_offers.insert_one(offer.model_dump())
    return offer

# --- TRACKING LINKS ---
@router.get("/links", response_model=List[TrackingLink])
async def get_links(affiliate_id: Optional[str] = None):
    db = get_db()
    query = {}
    if affiliate_id: query["affiliate_id"] = affiliate_id
    links = await db.affiliate_links.find(query).to_list(100)
    return [TrackingLink(**l) for l in links]

@router.post("/links")
async def create_link(link: TrackingLink):
    db = get_db()
    link.url = f"https://track.casino.com/c?aid={link.affiliate_id}&oid={link.offer_id}"
    await db.affiliate_links.insert_one(link.model_dump())
    return link

# --- CONVERSIONS & STATS ---
@router.get("/conversions", response_model=List[Conversion])
async def get_conversions(affiliate_id: Optional[str] = None):
    db = get_db()
    query = {}
    if affiliate_id: query["affiliate_id"] = affiliate_id
    convs = await db.affiliate_conversions.find(query).sort("created_at", -1).limit(100).to_list(100)
    return [Conversion(**c) for c in convs]

# --- PAYOUTS ---
@router.get("/payouts", response_model=List[Payout])
async def get_payouts():
    db = get_db()
    payouts = await db.affiliate_payouts.find().sort("created_at", -1).to_list(100)
    return [Payout(**p) for p in payouts]

@router.post("/payouts")
async def create_payout(payout: Payout):
    db = get_db()
    await db.affiliate_payouts.insert_one(payout.model_dump())
    return payout

# --- CREATIVES ---
@router.get("/creatives", response_model=List[Creative])
async def get_creatives():
    db = get_db()
    return [Creative(**c) for c in await db.affiliate_creatives.find().to_list(100)]

@router.post("/creatives")
async def create_creative(creative: Creative):
    db = get_db()
    await db.affiliate_creatives.insert_one(creative.model_dump())
    return creative

# --- SEED DATA ---
@router.post("/seed")
async def seed_affiliates():
    db = get_db()
    if await db.affiliates.count_documents({}) == 0:
        await db.affiliates.insert_many([
            Affiliate(username="bestbonus", email="contact@bestbonus.com", company_name="Best Bonus Media", status=AffiliateStatus.ACTIVE, balance=1500.0, total_earnings=50000.0).model_dump(),
            Affiliate(username="casinoguru", email="ads@guru.com", company_name="Guru Network", status=AffiliateStatus.PENDING, group="VIP").model_dump()
        ])
    if await db.affiliate_offers.count_documents({}) == 0:
        await db.affiliate_offers.insert_one(
            AffiliateOffer(name="TR Welcome CPA", model=CommissionModel.CPA, default_commission=CommissionPlan(cpa_amount=50)).model_dump()
        )
    return {"message": "Affiliates Seeded"}
