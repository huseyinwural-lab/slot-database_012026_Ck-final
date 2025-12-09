from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid

# --- SHARED ENUMS ---
class KYCStatus(str, Enum):
    NOT_STARTED = "not_started"
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    SUSPENDED = "suspended"

class DocStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"

# --- KYC MODELS ---

class KYCLevel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str # "Level 1", "Level 2"
    description: str
    requirements: List[str] = [] # ["id_card", "address_proof"]
    limits: Dict[str, float] = {} # {"max_daily_deposit": 1000}
    active: bool = True

class KYCRule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    condition: str # "total_deposit > 5000"
    target_level: str # "Level 2"
    action: str # "flag", "restrict"
    active: bool = True

class KYCDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    player_id: str
    player_username: str
    type: str # "id_card", "passport", "utility_bill", "bank_statement"
    sub_type: Optional[str] = None
    status: DocStatus = DocStatus.PENDING
    file_url: str
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    rejection_code: Optional[str] = None
    expiry_date: Optional[datetime] = None
    metadata: Dict[str, Any] = {} # OCR data

class KYCCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    player_id: str
    type: str # "pep", "sanctions", "adverse_media"
    status: str # "clear", "match", "failed"
    provider: str = "Internal Mock"
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    result_details: Dict[str, Any] = {}

class KYCAuditLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entity_id: str # Player ID or Doc ID
    admin_id: str
    action: str # "approve_doc", "change_level"
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class KYCDashboardStats(BaseModel):
    pending_count: int
    in_review_count: int
    approved_today: int
    rejected_today: int
    level_distribution: Dict[str, int]
    avg_review_time_mins: float
    high_risk_pending: int

# --- EXISTING MODULES (Preserved) ---
class Campaign(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    subject: str
    content: str
    segment: str
    channel: str 
    status: str = "draft" 
    sent_at: Optional[datetime] = None
    stats: Dict[str, int] = {"sent": 0, "opened": 0, "clicked": 0}

class CMSPage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    slug: str
    content: str
    status: str = "published"
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Banner(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    image_url: str
    target_url: str
    position: str 
    active: bool = True

class Affiliate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    commission_rate: float = 0.25 
    total_earnings: float = 0.0
    status: str = "active"

class RiskRule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    condition: str 
    action: str 
    severity: str 
    active: bool = True

class AdminUser(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    role: str 
    active: bool = True
    last_login: Optional[datetime] = None

class SystemLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    level: str 
    service: str 
    message: str
    details: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RGLimit(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    player_id: str
    type: str 
    amount: float
    period: str 
    set_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
