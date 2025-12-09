from fastapi import APIRouter, HTTPException, Body
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
import random
from app.models.modules import (
    ChannelConfig, PlayerCommPrefs, Segment, MessageTemplate, Campaign, Journey, MessageLog, InAppMessage,
    ChannelType, CampaignStatus, MessageStatus
)
from config import settings
from motor.motor_asyncio import AsyncIOMotorClient

router = APIRouter(prefix="/api/v1/crm", tags=["crm"])

def get_db():
    client = AsyncIOMotorClient(settings.mongo_url)
    return client[settings.db_name]

# --- CHANNELS ---
@router.get("/channels", response_model=List[ChannelConfig])
async def get_channels():
    db = get_db()
    return [ChannelConfig(**c) for c in await db.crm_channels.find().to_list(100)]

@router.post("/channels")
async def create_channel(channel: ChannelConfig):
    db = get_db()
    await db.crm_channels.insert_one(channel.model_dump())
    return channel

# --- SEGMENTS ---
@router.get("/segments", response_model=List[Segment])
async def get_segments():
    db = get_db()
    return [Segment(**s) for s in await db.crm_segments.find().to_list(100)]

@router.post("/segments")
async def create_segment(segment: Segment):
    db = get_db()
    # Mock calculation
    segment.estimated_size = random.randint(10, 5000)
    await db.crm_segments.insert_one(segment.model_dump())
    return segment

# --- TEMPLATES ---
@router.get("/templates", response_model=List[MessageTemplate])
async def get_templates():
    db = get_db()
    return [MessageTemplate(**t) for t in await db.crm_templates.find().to_list(100)]

@router.post("/templates")
async def create_template(template: MessageTemplate):
    db = get_db()
    await db.crm_templates.insert_one(template.model_dump())
    return template

# --- CAMPAIGNS ---
@router.get("/campaigns", response_model=List[Campaign])
async def get_campaigns():
    db = get_db()
    return [Campaign(**c) for c in await db.crm_campaigns.find().sort("created_at", -1).to_list(100)]

@router.post("/campaigns")
async def create_campaign(campaign: Campaign):
    db = get_db()
    await db.crm_campaigns.insert_one(campaign.model_dump())
    return campaign

@router.post("/campaigns/{id}/send")
async def send_campaign(id: str):
    db = get_db()
    camp = await db.crm_campaigns.find_one({"id": id})
    if not camp: raise HTTPException(404, "Campaign not found")
    
    # Mock sending process
    sent_count = random.randint(100, 1000)
    await db.crm_campaigns.update_one(
        {"id": id}, 
        {"$set": {"status": "completed", "stats.sent": sent_count}}
    )
    return {"message": f"Campaign sent to {sent_count} users"}

# --- JOURNEYS ---
@router.get("/journeys", response_model=List[Journey])
async def get_journeys():
    db = get_db()
    return [Journey(**j) for j in await db.crm_journeys.find().to_list(100)]

@router.post("/journeys")
async def create_journey(journey: Journey):
    db = get_db()
    await db.crm_journeys.insert_one(journey.model_dump())
    return journey

# --- SEED CRM DATA ---
@router.post("/seed")
async def seed_crm():
    db = get_db()
    if await db.crm_channels.count_documents({}) == 0:
        await db.crm_channels.insert_many([
            ChannelConfig(name="SendGrid Main", type=ChannelType.EMAIL, provider="sendgrid").model_dump(),
            ChannelConfig(name="Twilio SMS", type=ChannelType.SMS, provider="twilio").model_dump(),
        ])
    if await db.crm_segments.count_documents({}) == 0:
        await db.crm_segments.insert_many([
            Segment(name="VIP Users", description="Level 3+ Players", rule_definition={"vip": 3}).model_dump(),
            Segment(name="New Registrations", description="Joined last 24h", type="dynamic").model_dump(),
        ])
    if await db.crm_templates.count_documents({}) == 0:
        await db.crm_templates.insert_many([
            MessageTemplate(name="Welcome Email", channel=ChannelType.EMAIL, subject="Welcome!", body_html="<h1>Hi {username}</h1>").model_dump(),
            MessageTemplate(name="Weekly Reload SMS", channel=ChannelType.SMS, body_text="Reload bonus available!").model_dump(),
        ])
    return {"message": "CRM Seeded"}
