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

# --- ACTIVITY LOG (AUDIT) ---
@router.get("/activity-log", response_model=List[AdminActivityLog])
async def get_activity_log(
    admin_id: Optional[str] = Query(None),
    module: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    limit: int = Query(100, le=1000)
):
    db = get_db()
    filter_query = {}
    if admin_id:
        filter_query["admin_id"] = admin_id
    if module:
        filter_query["module"] = module
    if action:
        filter_query["action"] = action
    
    logs = await db.admin_activity_log.find(filter_query).sort("timestamp", -1).limit(limit).to_list(limit)
    return [AdminActivityLog(**log) for log in logs]

@router.post("/activity-log")
async def create_activity_log(log: AdminActivityLog):
    db = get_db()
    await db.admin_activity_log.insert_one(log.model_dump())
    return log

# --- LOGIN HISTORY ---
@router.get("/login-history", response_model=List[AdminLoginHistory])
async def get_login_history(
    admin_id: Optional[str] = Query(None),
    result: Optional[str] = Query(None),
    suspicious_only: bool = Query(False),
    limit: int = Query(100, le=1000)
):
    db = get_db()
    filter_query = {}
    if admin_id:
        filter_query["admin_id"] = admin_id
    if result:
        filter_query["result"] = result
    if suspicious_only:
        filter_query["is_suspicious"] = True
    
    history = await db.admin_login_history.find(filter_query).sort("login_time", -1).limit(limit).to_list(limit)
    return [AdminLoginHistory(**h) for h in history]

@router.post("/login-history")
async def create_login_history(history: AdminLoginHistory):
    db = get_db()
    await db.admin_login_history.insert_one(history.model_dump())
    return history

# --- PERMISSION MATRIX ---
@router.get("/permission-matrix", response_model=List[AdminPermissionMatrix])
async def get_permission_matrix(role_id: Optional[str] = Query(None)):
    db = get_db()
    filter_query = {}
    if role_id:
        filter_query["role_id"] = role_id
    
    matrix = await db.admin_permission_matrix.find(filter_query).to_list(1000)
    return [AdminPermissionMatrix(**m) for m in matrix]

@router.post("/permission-matrix")
async def create_permission_matrix(matrix: AdminPermissionMatrix):
    db = get_db()
    await db.admin_permission_matrix.insert_one(matrix.model_dump())
    return matrix

@router.put("/permission-matrix/{role_id}/{module}")
async def update_permission_matrix(role_id: str, module: str, permissions: Dict[str, bool] = Body(...)):
    db = get_db()
    await db.admin_permission_matrix.update_one(
        {"role_id": role_id, "module": module},
        {"$set": {"permissions": permissions, "updated_at": datetime.now(timezone.utc)}},
        upsert=True
    )
    return {"message": "Permissions updated"}

# --- IP RESTRICTIONS ---
@router.get("/ip-restrictions", response_model=List[AdminIPRestriction])
async def get_ip_restrictions(
    admin_id: Optional[str] = Query(None),
    restriction_type: Optional[str] = Query(None)
):
    db = get_db()
    filter_query = {"is_active": True}
    if admin_id:
        filter_query["admin_id"] = admin_id
    if restriction_type:
        filter_query["restriction_type"] = restriction_type
    
    restrictions = await db.admin_ip_restrictions.find(filter_query).to_list(1000)
    return [AdminIPRestriction(**r) for r in restrictions]

@router.post("/ip-restrictions")
async def create_ip_restriction(restriction: AdminIPRestriction):
    db = get_db()
    await db.admin_ip_restrictions.insert_one(restriction.model_dump())
    return restriction

@router.delete("/ip-restrictions/{restriction_id}")
async def remove_ip_restriction(restriction_id: str):
    db = get_db()
    await db.admin_ip_restrictions.update_one(
        {"id": restriction_id},
        {"$set": {"is_active": False}}
    )
    return {"message": "IP restriction removed"}

# --- DEVICE RESTRICTIONS ---
@router.get("/device-restrictions", response_model=List[AdminDeviceRestriction])
async def get_device_restrictions(
    admin_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    db = get_db()
    filter_query = {}
    if admin_id:
        filter_query["admin_id"] = admin_id
    if status:
        filter_query["status"] = status
    
    devices = await db.admin_device_restrictions.find(filter_query).sort("last_seen", -1).to_list(1000)
    return [AdminDeviceRestriction(**d) for d in devices]

@router.post("/device-restrictions")
async def create_device_restriction(device: AdminDeviceRestriction):
    db = get_db()
    await db.admin_device_restrictions.insert_one(device.model_dump())
    return device

@router.put("/device-restrictions/{device_id}/approve")
async def approve_device(device_id: str, approved_by: str = Body(..., embed=True)):
    db = get_db()
    await db.admin_device_restrictions.update_one(
        {"id": device_id},
        {"$set": {
            "status": "approved",
            "approved_by": approved_by,
            "approved_at": datetime.now(timezone.utc)
        }}
    )
    return {"message": "Device approved"}

# --- ENHANCED SECURITY POLICY ---
@router.put("/security/ip-restrictions")
async def update_security_ip_restrictions(
    allowed_ips: List[str] = Body(...),
    blocked_ips: List[str] = Body(...)
):
    db = get_db()
    await db.admin_security.update_one(
        {},
        {"$set": {
            "allowed_ips": allowed_ips,
            "blocked_ips": blocked_ips
        }},
        upsert=True
    )
    return {"message": "IP restrictions updated"}

# --- SEED ---
@router.post("/seed")
async def seed_admin():
    db = get_db()
    
    # Seed basic admin and role
    if await db.admins.count_documents({}) == 0:
        admin_user = AdminUser(username="superadmin", email="admin@casino.com", full_name="Super Admin", role="super_admin")
        await db.admins.insert_one(admin_user.model_dump())
        
        # Seed sample activity log
        activity_log = AdminActivityLog(
            admin_id=admin_user.id,
            admin_name="Super Admin",
            action="system_setup",
            module="admin",
            ip_address="127.0.0.1",
            before_snapshot={},
            after_snapshot={"status": "initialized"}
        )
        await db.admin_activity_log.insert_one(activity_log.model_dump())
        
        # Seed sample login history
        login_history = AdminLoginHistory(
            admin_id=admin_user.id,
            admin_name="Super Admin",
            ip_address="127.0.0.1",
            device_info="Chrome/120.0 (Windows)",
            result="success"
        )
        await db.admin_login_history.insert_one(login_history.model_dump())
    
    if await db.admin_roles.count_documents({}) == 0:
        role = AdminRole(name="Super Admin", description="Full Access", permissions=["*"], user_count=1)
        await db.admin_roles.insert_one(role.model_dump())
        
        # Seed permission matrix for super admin role
        modules = ["players", "finance", "games", "bonuses", "support", "risk", "cms", "reports"]
        for module in modules:
            matrix = AdminPermissionMatrix(
                role_id=role.id,
                role_name="Super Admin",
                module=module,
                permissions={
                    "read": True,
                    "write": True,
                    "approve": True,
                    "export": True,
                    "restricted": True
                },
                updated_by="system"
            )
            await db.admin_permission_matrix.insert_one(matrix.model_dump())
    
    return {"message": "Admin Seeded with Critical Modules"}
