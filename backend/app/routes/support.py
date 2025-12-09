from fastapi import APIRouter, HTTPException, Body, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
import random
from app.models.modules import (
    SupportTicket, ChatSession, ChatMessage, CannedResponse, Macro, KnowledgeBaseArticle,
    TicketStatus, TicketPriority, ChatStatus, AgentPerformance
)
from config import settings
from motor.motor_asyncio import AsyncIOMotorClient

router = APIRouter(prefix="/api/v1/support", tags=["support"])

def get_db():
    client = AsyncIOMotorClient(settings.mongo_url)
    return client[settings.db_name]

# --- DASHBOARD ---
@router.get("/dashboard")
async def get_support_dashboard():
    db = get_db()
    # Mock data for speed
    open_tickets = await db.tickets.count_documents({"status": "open"})
    active_chats = await db.chats.count_documents({"status": "active"})
    agents_online = 5
    
    return {
        "open_tickets": open_tickets,
        "waiting_tickets": 12,
        "active_chats": active_chats,
        "avg_response_time": "2m 30s",
        "csat_score": 4.8,
        "agents_online": agents_online,
        "category_breakdown": {"payment": 40, "tech": 20, "bonus": 30, "other": 10},
        "risk_alerts": 2
    }

# --- TICKETS ---
@router.get("/tickets", response_model=List[SupportTicket])
async def get_tickets(status: Optional[str] = None, priority: Optional[str] = None):
    db = get_db()
    query = {}
    if status and status != "all": query["status"] = status
    if priority and priority != "all": query["priority"] = priority
    tickets = await db.tickets.find(query).sort("created_at", -1).limit(100).to_list(100)
    return [SupportTicket(**t) for t in tickets]

@router.post("/tickets")
async def create_ticket(ticket: SupportTicket):
    db = get_db()
    await db.tickets.insert_one(ticket.model_dump())
    return ticket

@router.put("/tickets/{id}")
async def update_ticket(id: str, update: Dict[str, Any] = Body(...)):
    db = get_db()
    await db.tickets.update_one({"id": id}, {"$set": update})
    return {"message": "Updated"}

@router.post("/tickets/{id}/message")
async def add_ticket_message(id: str, message: Dict[str, Any] = Body(...)):
    db = get_db()
    await db.tickets.update_one({"id": id}, {"$push": {"messages": message}})
    return {"message": "Message added"}

# --- CHAT ---
@router.get("/chats", response_model=List[ChatSession])
async def get_chats(status: Optional[str] = None):
    db = get_db()
    query = {}
    if status and status != "all": query["status"] = status
    chats = await db.chats.find(query).sort("started_at", -1).limit(50).to_list(50)
    return [ChatSession(**c) for c in chats]

@router.post("/chats")
async def start_chat(chat: ChatSession):
    db = get_db()
    await db.chats.insert_one(chat.model_dump())
    return chat

@router.post("/chats/{id}/message")
async def send_chat_message(id: str, msg: ChatMessage):
    db = get_db()
    msg.session_id = id
    await db.chats.update_one({"id": id}, {"$push": {"messages": msg.model_dump()}})
    return msg

# --- KNOWLEDGE BASE ---
@router.get("/kb", response_model=List[KnowledgeBaseArticle])
async def get_kb_articles(category: Optional[str] = None):
    db = get_db()
    query = {}
    if category: query["category"] = category
    articles = await db.kb_articles.find(query).to_list(100)
    return [KnowledgeBaseArticle(**a) for a in articles]

@router.post("/kb")
async def create_kb_article(article: KnowledgeBaseArticle):
    db = get_db()
    await db.kb_articles.insert_one(article.model_dump())
    return article

# --- CANNED RESPONSES & MACROS ---
@router.get("/canned", response_model=List[CannedResponse])
async def get_canned_responses():
    db = get_db()
    return [CannedResponse(**r) for r in await db.canned_responses.find().to_list(100)]

@router.post("/canned")
async def create_canned_response(resp: CannedResponse):
    db = get_db()
    await db.canned_responses.insert_one(resp.model_dump())
    return resp

# --- SEED ---
@router.post("/seed")
async def seed_support():
    db = get_db()
    if await db.tickets.count_documents({}) == 0:
        await db.tickets.insert_many([
            SupportTicket(subject="Deposit Issue", description="My deposit is pending", player_id="p1", player_email="vip@casino.com", category="payment", priority="high").model_dump(),
            SupportTicket(subject="Bonus Inquiry", description="Where is my free spins?", player_id="p2", player_email="new@gmail.com", category="bonus").model_dump()
        ])
    if await db.canned_responses.count_documents({}) == 0:
        await db.canned_responses.insert_many([
            CannedResponse(title="Deposit Pending", content="Please allow up to 30 mins...", category="payment").model_dump(),
            CannedResponse(title="KYC Request", content="Please upload your ID...", category="verification").model_dump()
        ])
    if await db.kb_articles.count_documents({}) == 0:
        await db.kb_articles.insert_one(
            KnowledgeBaseArticle(title="How to Deposit", slug="how-to-deposit", content="Step 1...", category="payments").model_dump()
        )
    return {"message": "Support Seeded"}
