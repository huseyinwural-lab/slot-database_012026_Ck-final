from fastapi import APIRouter, HTTPException, Body, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import uuid
import random
from pydantic import BaseModel, EmailStr
from app.models.modules import (
    AdminUser, AdminRole, AdminTeam, AdminSession, SecurityPolicy, AdminInvite, AdminAPIKey,
    AdminStatus, InviteStatus, SystemEvent, LogSeverity, AdminActivityLog, AdminLoginHistory,
    AdminPermissionMatrix, AdminIPRestriction, AdminDeviceRestriction
)
from app.utils.auth import get_password_hash, create_access_token, get_current_admin
from config import settings
from motor.motor_asyncio import AsyncIOMotorClient

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

from app.core.errors import AppError
from app.core.database import db_wrapper

def get_db():
    return db_wrapper.db

# --- USERS ---
@router.get("/users", response_model=List[AdminUser])
async def get_admins(current_admin: AdminUser = Depends(get_current_admin)):
    db = get_db()
    
    # Super Admin can see all admins, others only see their tenant's admins
    query = {}
    if current_admin.role != "Super Admin":
        query["tenant_id"] = current_admin.tenant_id
    
    users = await db.admins.find(query).to_list(100)
    return [AdminUser(**u) for u in users]

class AdminUserCreateRequest(BaseModel):
    full_name: str
    email: EmailStr
    role: str
    tenant_role: Optional[str] = "tenant_admin"  # New field for tenant role
    allowed_modules: List[str] = []
    password_mode: str  # "manual" | "invite"
    password: Optional[str] = None
    tenant_id: Optional[str] = None  # If not provided, use default


@router.post("/users")
async def create_admin(payload: AdminUserCreateRequest):
    db = get_db()

    if payload.password_mode not in {"manual", "invite"}:
        raise AppError(error_code="INVALID_PASSWORD_MODE", message="Password mode must be 'manual' or 'invite'", status_code=400)

    if payload.password_mode == "manual" and not payload.password:
        raise AppError(error_code="PASSWORD_REQUIRED_FOR_MANUAL_MODE", message="Password is required when mode is manual", status_code=400)

    username = payload.email.split("@")[0]

    password_hash = None
    status = AdminStatus.ACTIVE
    invite_token = None
    invite_expires_at = None

    if payload.password_mode == "manual":
        from app.utils.auth import get_password_hash

        password_hash = get_password_hash(payload.password)
    else:
        # Invite mode: user will set password on first login via invite token
        status = AdminStatus.INVITED
        invite_expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        invite_token = create_access_token(
            data={"sub": None, "email": payload.email, "purpose": "invite"},
            expires_delta=timedelta(days=7),
        )

    # Use provided tenant_id or default to "default_casino"
    tenant_id = payload.tenant_id if payload.tenant_id else "default_casino"
    
    user = AdminUser(
        username=username,
        email=payload.email,
        full_name=payload.full_name,
        role=payload.role,
        tenant_role=payload.tenant_role, # Save tenant role
        tenant_id=tenant_id,
        allowed_modules=payload.allowed_modules,
        status=status,
        password_hash=password_hash,
        invite_token=invite_token,
        invite_expires_at=invite_expires_at,
    )

    await db.admins.insert_one(user.model_dump())
    # For manual mode, invite_token will be None; for invite mode, return token to caller
    return {"user": user, "invite_token": invite_token}

@router.put("/users/{id}/status")
async def update_admin_status(id: str, status: str = Body(..., embed=True)):
    db = get_db()
    await db.admins.update_one({"id": id}, {"$set": {"status": status}})
    return {"message": "Status updated"}

# --- ROLES ---
@router.get("/roles", response_model=List[AdminRole])
async def get_roles(current_admin: AdminUser = Depends(get_current_admin)):
    db = get_db()
    # Roles are typically global, but we can add tenant_id if needed
    # For now, keeping it global for all admins
    roles = await db.admin_roles.find().to_list(100)
    return [AdminRole(**r) for r in roles]

@router.post("/roles")
async def create_role(role: AdminRole):
    db = get_db()
    await db.admin_roles.insert_one(role.model_dump())
    return role

# --- TEAMS ---
@router.get("/teams", response_model=List[AdminTeam])
async def get_teams(current_admin: AdminUser = Depends(get_current_admin)):
    db = get_db()
    # Teams could be tenant-specific if the model supports it
    teams = await db.admin_teams.find().to_list(100)
    return [AdminTeam(**t) for t in teams]

@router.post("/teams")
async def create_team(team: AdminTeam):
    db = get_db()
    await db.admin_teams.insert_one(team.model_dump())
    return team

# --- SESSIONS ---
@router.get("/sessions", response_model=List[AdminSession])
async def get_sessions(current_admin: AdminUser = Depends(get_current_admin)):
    db = get_db()
    
    # Filter sessions by tenant (join with admin users)
    query = {}
    if current_admin.role != "Super Admin":
        # Get admin IDs from same tenant
        tenant_admins = await db.admins.find(
            {"tenant_id": current_admin.tenant_id},
            {"_id": 0, "id": 1}
        ).to_list(1000)
        admin_ids = [a["id"] for a in tenant_admins]
        query["admin_id"] = {"$in": admin_ids}
    
    sessions = await db.admin_sessions.find(query).sort("last_active", -1).to_list(100)
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
async def get_invites(current_admin: AdminUser = Depends(get_current_admin)):
    db = get_db()
    
    # Filter invites by tenant
    query = {}
    if current_admin.role != "Super Admin":
        query["tenant_id"] = current_admin.tenant_id
    
    return [AdminInvite(**i) for i in await db.admin_invites.find(query).to_list(100)]

@router.post("/invites")
async def create_invite(invite: AdminInvite):
    db = get_db()
    await db.admin_invites.insert_one(invite.model_dump())
    return invite

# --- API KEYS ---
@router.get("/keys", response_model=List[AdminAPIKey])
async def get_api_keys(current_admin: AdminUser = Depends(get_current_admin)):
    db = get_db()
    
    # Filter API keys by tenant
    query = {}
    if current_admin.role != "Super Admin":
        query["tenant_id"] = current_admin.tenant_id
    
    return [AdminAPIKey(**k) for k in await db.admin_keys.find(query).to_list(100)]

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
    
    # Always seed fresh data for demo
    admin_count = await db.admins.count_documents({})
    
    # Default demo passwords (development/demo only):
    # admin@casino.com / Admin123!
    password_hash = get_password_hash("Admin123!")
    
    # Create admin users
    if admin_count == 0:
        admin_users = [
            AdminUser(username="superadmin", email="admin@casino.com", full_name="Super Admin", role="Super Admin", password_hash=password_hash),
            AdminUser(username="manager1", email="manager@casino.com", full_name="Ahmet Yılmaz", role="Manager", password_hash=password_hash),
            AdminUser(username="support1", email="support@casino.com", full_name="Ayşe Demir", role="Support", password_hash=password_hash)
        ]
        for admin in admin_users:
            await db.admins.insert_one(admin.model_dump())
    else:
        # Ensure admin@casino.com has correct password for testing
        await db.admins.update_one(
            {"email": "admin@casino.com"},
            {"$set": {"password_hash": password_hash}},
            upsert=True
        )
        # Get existing admin users for activity logs
        existing_admins = await db.admins.find().to_list(100)
        admin_users = [AdminUser(**admin) for admin in existing_admins]
        
        # Seed activity logs for all admins
        activity_logs = [
            AdminActivityLog(
                admin_id=admin_users[0].id,
                admin_name="Super Admin",
                action="player_limit_change",
                module="players",
                ip_address="192.168.1.100",
                before_snapshot={"deposit_limit": 1000},
                after_snapshot={"deposit_limit": 5000},
                risk_level="medium"
            ),
            AdminActivityLog(
                admin_id=admin_users[0].id,
                admin_name="Super Admin",
                action="bonus_manual_load",
                module="bonuses",
                ip_address="192.168.1.100",
                before_snapshot={},
                after_snapshot={"bonus_amount": 100, "player_id": "p123"},
                risk_level="high"
            ),
            AdminActivityLog(
                admin_id=admin_users[1].id,
                admin_name="Ahmet Yılmaz",
                action="game_rtp_change",
                module="games",
                ip_address="192.168.1.101",
                before_snapshot={"rtp": 96.5},
                after_snapshot={"rtp": 95.0},
                risk_level="critical"
            ),
            AdminActivityLog(
                admin_id=admin_users[1].id,
                admin_name="Ahmet Yılmaz",
                action="withdrawal_approve",
                module="finance",
                ip_address="192.168.1.101",
                before_snapshot={},
                after_snapshot={"amount": 10000, "player_id": "p456"},
                risk_level="high"
            ),
            AdminActivityLog(
                admin_id=admin_users[2].id,
                admin_name="Ayşe Demir",
                action="cms_content_update",
                module="cms",
                ip_address="192.168.1.102",
                before_snapshot={"title": "Old Title"},
                after_snapshot={"title": "New Title"},
                risk_level="low"
            )
        ]
        for log in activity_logs:
            await db.admin_activity_log.insert_one(log.model_dump())
        
        # Seed login history
        login_history_entries = [
            AdminLoginHistory(
                admin_id=admin_users[0].id,
                admin_name="Super Admin",
                ip_address="192.168.1.100",
                device_info="Chrome/120.0 (Windows 10)",
                location="Istanbul, TR",
                result="success"
            ),
            AdminLoginHistory(
                admin_id=admin_users[0].id,
                admin_name="Super Admin",
                ip_address="192.168.1.100",
                device_info="Chrome/120.0 (Windows 10)",
                location="Istanbul, TR",
                result="success"
            ),
            AdminLoginHistory(
                admin_id=admin_users[1].id,
                admin_name="Ahmet Yılmaz",
                ip_address="192.168.1.101",
                device_info="Firefox/119.0 (Mac OS)",
                location="Ankara, TR",
                result="failed",
                failure_reason="wrong_password",
                is_suspicious=True
            ),
            AdminLoginHistory(
                admin_id=admin_users[1].id,
                admin_name="Ahmet Yılmaz",
                ip_address="192.168.1.101",
                device_info="Firefox/119.0 (Mac OS)",
                location="Ankara, TR",
                result="success"
            ),
            AdminLoginHistory(
                admin_id=admin_users[2].id,
                admin_name="Ayşe Demir",
                ip_address="10.0.0.50",
                device_info="Safari/17.0 (iOS 17)",
                location="Izmir, TR",
                result="success"
            ),
            AdminLoginHistory(
                admin_id=admin_users[0].id,
                admin_name="Super Admin",
                ip_address="203.0.113.45",
                device_info="Chrome/120.0 (Unknown)",
                location="Moscow, RU",
                result="failed",
                failure_reason="ip_blocked",
                is_suspicious=True
            )
        ]
        for entry in login_history_entries:
            await db.admin_login_history.insert_one(entry.model_dump())
        
        # Seed IP restrictions
        ip_restrictions = [
            AdminIPRestriction(
                admin_id=None,
                ip_address="192.168.1.0/24",
                restriction_type="allowed",
                reason="Office network",
                added_by="system"
            ),
            AdminIPRestriction(
                admin_id=None,
                ip_address="203.0.113.0/24",
                restriction_type="blocked",
                reason="Suspicious login attempts",
                added_by="Super Admin"
            )
        ]
        for restriction in ip_restrictions:
            await db.admin_ip_restrictions.insert_one(restriction.model_dump())
        
        # Seed device restrictions
        device_restrictions = [
            AdminDeviceRestriction(
                admin_id=admin_users[0].id,
                device_fingerprint="fp_abc123xyz",
                device_name="Work Laptop",
                device_type="desktop",
                browser_info="Chrome 120 / Windows 10",
                status="approved",
                approved_by="system"
            ),
            AdminDeviceRestriction(
                admin_id=admin_users[1].id,
                device_fingerprint="fp_def456uvw",
                device_name="iPhone 15",
                device_type="mobile",
                browser_info="Safari 17 / iOS",
                status="pending"
            ),
            AdminDeviceRestriction(
                admin_id=admin_users[2].id,
                device_fingerprint="fp_ghi789rst",
                device_name="Unknown Device",
                device_type="unknown",
                browser_info="Unknown",
                status="blocked",
                approved_by="Super Admin"
            )
        ]
        for device in device_restrictions:
            await db.admin_device_restrictions.insert_one(device.model_dump())
    
    # Seed roles
    if await db.admin_roles.count_documents({}) == 0:
        roles = [
            AdminRole(name="Super Admin", description="Tam Yetkili", permissions=["*"], user_count=1),
            AdminRole(
                name="Manager",
                description="Yönetici - Çoğu modüle erişim",
                permissions=[
                    "PLAYERS_READ",
                    "PLAYERS_WRITE",
                    "FINANCE_READ",
                    "GAMES_READ",
                    "BONUSES_MANAGE",
                    "REPORTS_VIEW",
                ],
                user_count=1,
            ),
            AdminRole(
                name="Support",
                description="Destek - Sadece okuma yetkisi",
                permissions=["PLAYERS_READ", "SUPPORT_READ", "SUPPORT_WRITE"],
                user_count=1,
            ),
        ]
        for role in roles:
            await db.admin_roles.insert_one(role.model_dump())
            
            # Seed permission matrix for each role
            modules = ["players", "finance", "games", "bonuses", "support", "risk", "cms", "reports"]
            for module in modules:
                if role.name == "Super Admin":
                    perms = {"read": True, "write": True, "approve": True, "export": True, "restricted": True}
                elif role.name == "Manager":
                    perms = {"read": True, "write": module in ["players", "games"], "approve": module == "finance", "export": True, "restricted": False}
                else:  # Support
                    perms = {"read": module in ["players", "support"], "write": module == "support", "approve": False, "export": False, "restricted": False}
                    
                matrix = AdminPermissionMatrix(
                    role_id=role.id,
                    role_name=role.name,
                    module=module,
                    permissions=perms,
                    updated_by="system"
                )
                await db.admin_permission_matrix.insert_one(matrix.model_dump())
    
    return {"message": "Admin Seeded with Critical Modules"}
