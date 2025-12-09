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

# --- CRM ENUMS ---
class ChannelType(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"
    WHATSAPP = "whatsapp"

class CampaignStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class MessageStatus(str, Enum):
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"
    OPENED = "opened"
    CLICKED = "clicked"
    UNSUBSCRIBED = "unsubscribed"

# --- CRM MODELS ---

class ChannelConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str # "Sendgrid Main"
    type: ChannelType
    provider: str # "sendgrid", "twilio"
    config: Dict[str, Any] = {} # api_key, sender_email
    rate_limits: Dict[str, int] = {"max_per_minute": 60}
    enabled: bool = True
    default_locale: str = "en"
    supported_locales: List[str] = ["en", "tr"]

class PlayerCommPrefs(BaseModel):
    player_id: str
    email: Optional[str] = None
    phone: Optional[str] = None
    preferred_language: str = "en"
    channels_allowed: Dict[str, bool] = {"email": True, "sms": True, "push": True}
    marketing_opt_in: bool = True
    marketing_opt_in_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    transactional_only: bool = False
    quiet_hours_enabled: bool = False
    quiet_hours_start: Optional[str] = "22:00"
    quiet_hours_end: Optional[str] = "08:00"

class Segment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str # "VIP Users"
    description: Optional[str] = None
    type: str = "dynamic" # dynamic, static
    rule_definition: Dict[str, Any] = {} # {"vip_level": {"$gte": 2}}
    estimated_size: int = 0
    tags: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MessageTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    channel: ChannelType
    category: str = "marketing" # transactional, marketing
    locale: str = "en"
    subject: Optional[str] = None
    body_html: Optional[str] = None
    body_text: Optional[str] = None
    placeholders: List[str] = [] # ["username", "bonus_amount"]
    status: str = "active"

class Campaign(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: str = "one_time" # one_time, recurring, journey
    channel: ChannelType
    segment_id: str
    template_id: str
    goal: Optional[str] = None # deposit, login
    status: CampaignStatus = CampaignStatus.DRAFT
    schedule_type: str = "immediate"
    start_at: Optional[datetime] = None
    stats: Dict[str, int] = {"sent": 0, "opened": 0, "clicked": 0}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class JourneyStep(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    delay_days: int = 0
    channel: ChannelType
    template_id: str

class Journey(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    trigger_event: str # registration, first_deposit
    steps: List[JourneyStep] = []
    status: str = "active"

class MessageLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    player_id: str
    campaign_id: Optional[str] = None
    template_id: str
    channel: ChannelType
    sent_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: MessageStatus = MessageStatus.SENT
    metadata: Dict[str, Any] = {}

class InAppMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    player_id: str
    title: str
    body: str
    type: str = "info"
    is_read: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# --- EXISTING MODULES (Preserved) ---
class KYCDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    player_id: str
    player_username: str
    type: str 
    status: str = "pending"
    file_url: str
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reviewed_at: Optional[datetime] = None
    admin_note: Optional[str] = None

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

# KYC extra models
class KYCLevel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str 
    description: str
    requirements: List[str] = [] 
    limits: Dict[str, float] = {}
    active: bool = True

class KYCRule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    condition: str 
    target_level: str 
    action: str 
    active: bool = True

class KYCCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    player_id: str
    type: str 
    status: str 
    provider: str = "Internal Mock"
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    result_details: Dict[str, Any] = {}

class KYCAuditLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entity_id: str 
    admin_id: str
    action: str 
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
