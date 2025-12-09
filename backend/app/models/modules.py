from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid

# --- RISK ENUMS ---
class RiskSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RiskCategory(str, Enum):
    ACCOUNT = "account"
    DEVICE = "device"
    IP_GEO = "ip_geo"
    PAYMENT = "payment"
    BONUS_ABUSE = "bonus_abuse"
    GAME_BEHAVIOR = "game_behavior"
    VELOCITY = "velocity"
    KYC_IDENTITY = "kyc_identity"
    RESPONSIBLE_GAMING = "rg"

class RiskActionType(str, Enum):
    WITHDRAW_FREEZE = "withdraw_freeze"
    ACCOUNT_BLOCK = "account_block"
    LOGIN_BLOCK = "login_block"
    BONUS_CANCEL = "bonus_cancel"
    RISK_SCORE_INCREASE = "risk_score_increase"
    MANUAL_REVIEW = "manual_review"
    ALERT_TEAM = "alert_team"
    TAG_PLAYER = "tag_player"

class RiskCaseStatus(str, Enum):
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    ESCALATED = "escalated"
    CLOSED_FALSE_POSITIVE = "closed_false_positive"
    CLOSED_CONFIRMED = "closed_confirmed"

# --- RG ENUMS ---
class RGAlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RGCaseStatus(str, Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"

class ExclusionType(str, Enum):
    COOL_OFF = "cool_off"
    SELF_EXCLUSION = "self_exclusion"
    PERMANENT_BAN = "permanent_ban"

# --- RG MODELS ---

class RGLimitConfig(BaseModel):
    deposit_daily: Optional[float] = None
    deposit_weekly: Optional[float] = None
    deposit_monthly: Optional[float] = None
    loss_daily: Optional[float] = None
    loss_weekly: Optional[float] = None
    loss_monthly: Optional[float] = None
    session_time_daily_minutes: Optional[int] = None
    wager_daily: Optional[float] = None

class PlayerRGProfile(BaseModel):
    player_id: str
    risk_level: RGAlertSeverity = RGAlertSeverity.LOW
    active_limits: RGLimitConfig = Field(default_factory=RGLimitConfig)
    exclusion_active: bool = False
    exclusion_type: Optional[ExclusionType] = None
    exclusion_start: Optional[datetime] = None
    exclusion_end: Optional[datetime] = None # None = indefinite
    last_assessment_date: Optional[datetime] = None
    notes: List[Dict[str, Any]] = []

class RGRule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    conditions: Dict[str, Any] = {} # e.g. {"net_loss_daily": {">": 1000}}
    actions: List[str] = [] # ["alert_team", "suggest_limit"]
    severity: RGAlertSeverity
    active: bool = True

class RGAlert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    player_id: str
    rule_id: Optional[str] = None
    type: str # "high_loss", "long_session"
    severity: RGAlertSeverity
    status: str = "new"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None
    assigned_to: Optional[str] = None

class RGCase(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    player_id: str
    linked_alerts: List[str] = []
    risk_level: RGAlertSeverity
    status: RGCaseStatus = RGCaseStatus.NEW
    notes: List[Dict[str, Any]] = []
    actions_taken: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RGDashboardStats(BaseModel):
    active_self_exclusions: int
    active_cool_offs: int
    players_with_limits: int
    high_loss_alerts_7d: int
    open_cases: int
    risk_distribution: Dict[str, int] # {low: 100, high: 5}

# --- RISK MODELS ---

class RiskRuleCondition(BaseModel):
    field: str # e.g. "deposit_velocity_1h"
    operator: str # "gt", "lt", "eq", "contains"
    value: Any
    description: Optional[str] = None

class RiskRuleAction(BaseModel):
    type: RiskActionType
    parameters: Dict[str, Any] = {} # e.g. {score: 50}

class RiskRule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    category: RiskCategory
    severity: RiskSeverity
    priority: int = 1
    status: str = "active" # active, testing, paused
    conditions: List[RiskRuleCondition] = []
    actions: List[RiskRuleAction] = []
    score_impact: int = 0
    version: int = 1
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class VelocityRule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str # e.g. "Login Spike"
    event_type: str # login, deposit, registration
    time_window_minutes: int
    threshold_count: int
    action: RiskActionType
    status: str = "active"

class BlacklistEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str # ip, device, email_domain, bin, crypto_address
    value: str
    reason: str
    added_by: str
    added_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None

class DeviceProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    fingerprint_hash: str
    player_ids: List[str] = [] 
    user_agent: str
    ip_address: str
    is_rooted: bool = False
    is_emulator: bool = False
    trust_score: int = 100
    last_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RiskCase(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    player_id: str
    risk_score: int
    severity: RiskSeverity
    triggered_rules: List[str] = [] 
    status: RiskCaseStatus = RiskCaseStatus.OPEN
    assigned_to: Optional[str] = None
    notes: List[Dict[str, Any]] = [] 
    evidence_ids: List[str] = [] # Linked evidence
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RiskAlert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str 
    message: str
    severity: RiskSeverity
    player_id: Optional[str] = None
    metadata: Dict[str, Any] = {}
    is_resolved: bool = False
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Evidence(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    related_id: str # PlayerID, TransactionID, CaseID
    type: str # screenshot, document, log_export
    description: str
    file_url: Optional[str] = None
    uploaded_by: str
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tags: List[str] = []

class RiskDashboardStats(BaseModel):
    daily_alerts: int
    open_cases: int
    high_risk_players: int
    suspicious_withdrawals: int
    bonus_abuse_alerts: int
    risk_trend: List[Dict[str, Any]] 
    category_breakdown: Dict[str, int]

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

# --- AFFILIATE ENUMS ---
class AffiliateStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    BANNED = "banned"

class CommissionModel(str, Enum):
    CPA = "cpa"
    REVSHARE = "revshare"
    HYBRID = "hybrid"
    CPL = "cpl"

class PayoutStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    PAID = "paid"
    REJECTED = "rejected"

# --- SUPPORT ENUMS ---
class TicketPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_PLAYER = "waiting_player"
    SOLVED = "solved"
    CLOSED = "closed"

class ChatStatus(str, Enum):
    QUEUED = "queued"
    ACTIVE = "active"
    ENDED = "ended"
    MISSED = "missed"

# --- SUPPORT MODELS ---

class CannedResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    category: str 
    language: str = "en"
    tags: List[str] = []

class Macro(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    actions: List[Dict[str, Any]] = [] 
    active: bool = True

class SupportWorkflow(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    trigger_event: str 
    conditions: Dict[str, Any] = {} 
    actions: List[Dict[str, Any]] = []
    active: bool = True

class KnowledgeBaseArticle(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    slug: str
    content: str
    category: str
    language: str = "en"
    is_internal: bool = False
    tags: List[str] = []
    views: int = 0
    helpful_count: int = 0
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    sender_type: str 
    sender_id: str
    sender_name: str
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    attachments: List[str] = []

class ChatSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    player_id: str
    player_name: str
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    status: ChatStatus = ChatStatus.QUEUED
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None
    rating: Optional[int] = None
    tags: List[str] = []
    messages: List[ChatMessage] = []

class SupportTicket(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    subject: str
    description: str
    player_id: str
    player_email: str
    category: str
    priority: TicketPriority = TicketPriority.NORMAL
    status: TicketStatus = TicketStatus.OPEN
    assigned_agent_id: Optional[str] = None
    channel: str = "email" 
    tags: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    messages: List[Dict[str, Any]] = [] 
    
class AgentPerformance(BaseModel):
    agent_id: str
    agent_name: str
    tickets_solved: int = 0
    avg_response_time_mins: float = 0.0
    csat_score: float = 0.0
    active_chats: int = 0
    status: str = "online" 

# --- AFFILIATE MODELS ---

class CommissionPlan(BaseModel):
    model: CommissionModel = CommissionModel.REVSHARE
    cpa_amount: float = 0.0
    cpa_currency: str = "USD"
    revshare_percentage: float = 25.0
    hybrid_cpa: float = 0.0
    hybrid_revshare: float = 0.0
    negative_carryover: bool = True

class Affiliate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: EmailStr
    company_name: Optional[str] = None
    status: AffiliateStatus = AffiliateStatus.PENDING
    account_manager_id: Optional[str] = None
    group: str = "Standard" 
    country: str = "Unknown"
    balance: float = 0.0
    total_earnings: float = 0.0
    total_paid: float = 0.0
    currency: str = "USD"
    default_plan: CommissionPlan = Field(default_factory=CommissionPlan)
    tracking_link_template: Optional[str] = None
    postback_url: Optional[str] = None
    total_clicks: int = 0
    total_registrations: int = 0
    total_ftd: int = 0 
    last_activity_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AffiliateOffer(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    brand_id: str = "default"
    model: CommissionModel
    default_commission: CommissionPlan
    landing_pages: List[str] = []
    allowed_countries: List[str] = []
    status: str = "active"

class TrackingLink(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    affiliate_id: str
    offer_id: str
    name: str
    url: str
    sub_ids: Dict[str, str] = {} 

class Conversion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    affiliate_id: str
    offer_id: Optional[str] = None
    player_id: str
    event_type: str 
    amount: float = 0.0
    commission: float = 0.0
    status: str = "approved"
    sub_ids: Dict[str, str] = {}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Payout(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    affiliate_id: str
    amount: float
    period_start: datetime
    period_end: datetime
    status: PayoutStatus = PayoutStatus.PENDING
    payment_method: str = "bank_transfer"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Creative(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: str 
    size: Optional[str] = None
    url: str
    preview_url: Optional[str] = None
    status: str = "active"

# --- CRM MODELS ---

class ChannelConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str 
    type: ChannelType
    provider: str 
    config: Dict[str, Any] = {} 
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
    name: str 
    description: Optional[str] = None
    type: str = "dynamic" 
    rule_definition: Dict[str, Any] = {} 
    estimated_size: int = 0
    tags: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MessageTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    channel: ChannelType
    category: str = "marketing" 
    locale: str = "en"
    subject: Optional[str] = None
    body_html: Optional[str] = None
    body_text: Optional[str] = None
    placeholders: List[str] = [] 
    status: str = "active"

class Campaign(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: str = "one_time" 
    channel: ChannelType
    segment_id: str
    template_id: str
    goal: Optional[str] = None 
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
    trigger_event: str 
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
