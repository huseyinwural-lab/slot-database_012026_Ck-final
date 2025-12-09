from fastapi import APIRouter, HTTPException, Body, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
import random
from app.models.modules import (
    AdminUser, AdminRole, AdminTeam, AdminSession, SecurityPolicy, AdminInvite, AdminAPIKey,
    AdminStatus, InviteStatus, SystemEvent, LogSeverity, AdminActivityLog, AdminLoginHistory,
    AdminPermissionMatrix, AdminIPRestriction, AdminDeviceRestriction
)
from config import settings
from motor.motor_asyncio import AsyncIOMotorClient

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

def get_db():
    client = AsyncIOMotorClient(settings.mongo_url)
    return client[settings.db_name]

# --- USERS ---
@router.get("/users", response_model=List[AdminUser])
async def get_admins():
    db = get_db()
    users = await db.admins.find().to_list(100)
    return [AdminUser(**u) for u in users]

@router.post("/users")
async def create_admin(user: AdminUser):
    db = get_db()
    await db.admins.insert_one(user.model_dump())
    return user

@router.put("/users/{id}/status")
async def update_admin_status(id: str, status: str = Body(..., embed=True)):
    db = get_db()
    await db.admins.update_one({"id": id}, {"$set": {"status": status}})
    return {"message": "Status updated"}

# --- ROLES ---
@router.get("/roles", response_model=List[AdminRole])
async def get_roles():
    db = get_db()
    roles = await db.admin_roles.find().to_list(100)
    return [AdminRole(**r) for r in roles]

@router.post("/roles")
async def create_role(role: AdminRole):
    db = get_db()
    await db.admin_roles.insert_one(role.model_dump())
    return role

# --- TEAMS ---
@router.get("/teams", response_model=List[AdminTeam])
async def get_teams():
    db = get_db()
    teams = await db.admin_teams.find().to_list(100)
    return [AdminTeam(**t) for t in teams]

@router.post("/teams")
async def create_team(team: AdminTeam):
    db = get_db()
    await db.admin_teams.insert_one(team.model_dump())
    return team

# --- SESSIONS ---
@router.get("/sessions", response_model=List[AdminSession])
async def get_sessions():
    db = get_db()
    sessions = await db.admin_sessions.find().sort("last_active", -1).to_list(100)
    return [AdminSession(**s) for s in sessions]

# --- SECURITY ---
@router.get("/security", response_model=SecurityPolicy)
async def get_security_policy():
    db = get_db()
    policy = await db.admin_security.find_one({})
    if not policy:
        policy = SecurityPolicy().model_dump()
        await db.admin_security.insert_one(policy)
    return SecurityPolicy(**policy)

@router.post("/security")
async def update_security_policy(policy: SecurityPolicy):
    db = get_db()
    await db.admin_security.update_one({}, {"$set": policy.model_dump()}, upsert=True)
    return policy

# --- INVITES ---
@router.get("/invites", response_model=List[AdminInvite])
async def get_invites():
    db = get_db()
    return [AdminInvite(**i) for i in await db.admin_invites.find().to_list(100)]

@router.post("/invites")
async def create_invite(invite: AdminInvite):
    db = get_db()
    await db.admin_invites.insert_one(invite.model_dump())
    return invite

# --- API KEYS ---
@router.get("/keys", response_model=List[AdminAPIKey])
async def get_api_keys():
    db = get_db()
    return [AdminAPIKey(**k) for k in await db.admin_keys.find().to_list(100)]

@router.post("/keys")
async def create_api_key(key: AdminAPIKey):
    db = get_db()
    await db.admin_keys.insert_one(key.model_dump())
    return key

# --- SEED ---
@router.post("/seed")
async def seed_admin():
    db = get_db()
    if await db.admins.count_documents({}) == 0:
        await db.admins.insert_one(AdminUser(username="superadmin", email="admin@casino.com", full_name="Super Admin", role="super_admin").model_dump())
    if await db.admin_roles.count_documents({}) == 0:
        await db.admin_roles.insert_one(AdminRole(name="Super Admin", description="Full Access", permissions=["*"], user_count=1).model_dump())
    return {"message": "Admin Seeded"}
