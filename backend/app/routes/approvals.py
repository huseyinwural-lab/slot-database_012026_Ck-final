from fastapi import APIRouter, HTTPException, Body, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
import random
from app.models.core import (
    ApprovalRequest, ApprovalRule, Delegation, ApprovalStatus, ApprovalCategory
)
from app.models.domain.admin import AdminUser
from app.utils.auth import get_current_admin
from app.utils.permissions import require_owner
from config import settings
from motor.motor_asyncio import AsyncIOMotorClient

router = APIRouter(prefix="/api/v1/approvals", tags=["approvals"])

def get_db():
    client = AsyncIOMotorClient(settings.mongo_url)
    return client[settings.db_name]

# --- REQUESTS ---
@router.get("/requests", response_model=List[ApprovalRequest])
async def get_approval_requests(
    status: Optional[str] = None, 
    category: Optional[str] = None,
    current_admin: AdminUser = Depends(get_current_admin)
):
    # Owner-only endpoint
    require_owner(current_admin)
    
    db = get_db()
    query = {}
    if status and status != "all": query["status"] = status
    if category and category != "all": query["category"] = category
    reqs = await db.approvals.find(query).sort("created_at", -1).limit(100).to_list(100)
    return [ApprovalRequest(**r) for r in reqs]

@router.post("/requests")
async def create_approval_request(req: ApprovalRequest):
    db = get_db()
    # Check for auto-approve rules
    rule = await db.approval_rules.find_one({
        "action_type": req.action_type,
        "auto_approve": True
    })
    if rule:
        req.status = ApprovalStatus.APPROVED
        # Trigger the action logic (Mock)
        
    await db.approvals.insert_one(req.model_dump())
    return req

@router.post("/requests/{id}/action")
async def action_approval_request(id: str, action: str = Body(..., embed=True), note: str = Body(None, embed=True)):
    db = get_db()
    req = await db.approvals.find_one({"id": id})
    if not req:
        raise HTTPException(404, "Request not found")
    
    new_status = ApprovalStatus.APPROVED if action == "approve" else ApprovalStatus.REJECTED
    
    # If rejected, maybe allow changes
    if action == "request_changes":
        new_status = ApprovalStatus.PENDING # Or a specific status like "changes_requested"
    
    await db.approvals.update_one(
        {"id": id},
        {
            "$set": {"status": new_status, "updated_at": datetime.now(timezone.utc)},
            "$push": {"notes": {"admin": "current_admin", "text": note, "time": datetime.now(timezone.utc)}}
        }
    )
    
    # Trigger Logic (Mock)
    if new_status == ApprovalStatus.APPROVED:
        # Example: if withdrawal, update tx status
        if req['category'] == "finance" and req['action_type'] == "withdrawal_approve":
            await db.transactions.update_one(
                {"id": req['related_entity_id']},
                {"$set": {"status": "completed"}}
            )
            
    return {"message": f"Request {new_status}"}

# --- RULES ---
@router.get("/rules", response_model=List[ApprovalRule])
async def get_approval_rules():
    db = get_db()
    rules = await db.approval_rules.find().to_list(100)
    return [ApprovalRule(**r) for r in rules]

@router.post("/rules")
async def create_approval_rule(rule: ApprovalRule):
    db = get_db()
    await db.approval_rules.insert_one(rule.model_dump())
    return rule

# --- DELEGATIONS ---
@router.get("/delegations", response_model=List[Delegation])
async def get_delegations():
    db = get_db()
    delegs = await db.delegations.find().to_list(100)
    return [Delegation(**d) for d in delegs]

@router.post("/delegations")
async def create_delegation(delegation: Delegation):
    db = get_db()
    await db.delegations.insert_one(delegation.model_dump())
    return delegation

# --- SEED ---
@router.post("/seed")
async def seed_approvals():
    db = get_db()
    if await db.approval_rules.count_documents({}) == 0:
        await db.approval_rules.insert_many([
            ApprovalRule(action_type="rtp_change", condition="always", required_role="manager").model_dump(),
            ApprovalRule(action_type="withdrawal_approve", condition="amount > 5000", required_role="finance_lead").model_dump()
        ])
    return {"message": "Approvals Seeded"}
