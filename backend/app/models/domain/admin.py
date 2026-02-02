from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

# --- ADMIN ENUMS ---
class AdminStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    LOCKED = "locked"
    INVITED = "invited"


class TenantRole(str, Enum):
    """
    Tenant-specific roles for granular access control
    """
    TENANT_ADMIN = "tenant_admin"      # Full access within tenant
    OPERATIONS = "operations"          # Players, Games, Bonuses
    FINANCE = "finance"                # Revenue, Reports only
    SUPPORT = "support"                # Support tickets, basic player view

class InviteStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"

# --- ADMIN MODELS ---

class AdminRole(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    permissions: List[str] = [] # "player:read", "finance:approve"
    user_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class AdminTeam(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    member_count: int = 0
    default_role_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class AdminUser(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: EmailStr
    full_name: str
    role: str  # role_id or name
    tenant_id: str = "default_casino"
    is_platform_owner: bool = False  # TRUE = Owner (can see all tenants), FALSE = Tenant admin
    tenant_role: Optional[TenantRole] = TenantRole.TENANT_ADMIN  # Default to full tenant admin
    department: str = "General"
    status: AdminStatus = AdminStatus.ACTIVE
    is_2fa_enabled: bool = False
    last_login: Optional[datetime] = None
    last_ip: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())

    # Basit modül bazlı erişim listesi (ileride RBAC ile genişletilebilir)
    allowed_modules: List[str] = []

    # Auth & security fields
    password_hash: Optional[str] = None
    is_active: bool = True
    failed_login_attempts: int = 0
    last_password_change_at: Optional[datetime] = None
    password_reset_token: Optional[str] = None
    password_reset_expires_at: Optional[datetime] = None
    invite_token: Optional[str] = None
    invite_expires_at: Optional[datetime] = None

class AdminSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    admin_id: str
    admin_name: str
    ip_address: str
    device_info: str
    login_time: datetime = Field(default_factory=lambda: datetime.utcnow())
    last_active: datetime = Field(default_factory=lambda: datetime.utcnow())
    location: Optional[str] = None
    is_suspicious: bool = False

class SecurityPolicy(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    password_min_length: int = 12
    session_timeout_minutes: int = 60
    allowed_ips: List[str] = []
    blocked_ips: List[str] = []
    require_2fa: bool = False
    max_login_attempts: int = 5

class AdminInvite(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    role: str
    status: InviteStatus = InviteStatus.PENDING
    sent_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    expires_at: datetime

class AdminAPIKey(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    owner_admin_id: str  # AdminUser.id
    tenant_id: str
    name: str
    key_prefix: str
    key_hash: str
    scopes: List[str] = []
    active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    last_used_at: Optional[datetime] = None

# --- NEW CRITICAL ADMIN MODELS ---

class AdminActivityLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    admin_id: str
    admin_name: str
    action: str  # "player_limit_change", "bonus_manual_load", "game_rtp_change", etc.
    module: str  # "players", "bonuses", "games", "finance", etc.
    target_entity_id: Optional[str] = None  # ID of affected entity
    before_snapshot: Optional[Dict[str, Any]] = None
    after_snapshot: Optional[Dict[str, Any]] = None
    ip_address: str
    user_agent: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.utcnow())
    risk_level: str = "low"  # low, medium, high, critical

class AdminLoginHistory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    admin_id: str
    admin_name: str
    login_time: datetime = Field(default_factory=lambda: datetime.utcnow())
    ip_address: str
    device_info: str
    device_fingerprint: Optional[str] = None
    location: Optional[str] = None
    result: str  # "success", "failed"
    failure_reason: Optional[str] = None  # "wrong_password", "brute_force", "ip_blocked", "2fa_failed"
    session_duration_minutes: Optional[int] = None
    is_suspicious: bool = False

class AdminPermissionMatrix(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role_id: str
    role_name: str
    module: str  # "players", "finance", "games", etc.
    permissions: Dict[str, bool] = {
        "read": False,
        "write": False, 
        "approve": False,
        "export": False,
        "restricted": False
    }
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    updated_by: str

class AdminIPRestriction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    admin_id: Optional[str] = None  # If None, applies to all admins
    ip_address: str
    restriction_type: str  # "allowed", "blocked"
    reason: Optional[str] = None
    added_by: str
    added_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    expires_at: Optional[datetime] = None
    is_active: bool = True

class AdminDeviceRestriction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    admin_id: str
    device_fingerprint: str
    device_name: Optional[str] = None
    device_type: Optional[str] = None  # "desktop", "mobile", "tablet"
    browser_info: Optional[str] = None
    status: str = "pending"  # "pending", "approved", "blocked"
    first_seen: datetime = Field(default_factory=lambda: datetime.utcnow())
    last_seen: datetime = Field(default_factory=lambda: datetime.utcnow())
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
