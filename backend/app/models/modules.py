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

# --- CMS ENUMS ---
class CMSStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    SCHEDULED = "scheduled"
    ARCHIVED = "archived"

class CMSPageType(str, Enum):
    HOMEPAGE = "homepage"
    PROMO = "promo"
    STATIC = "static"
    BLOG = "blog"
    LANDING = "landing"

class CMSBannerPosition(str, Enum):
    HOME_HERO = "home_hero"
    LOBBY_TOP = "lobby_top"
    MOBILE_ONLY = "mobile_only"
    SIDEBAR = "sidebar"

# --- ADMIN ENUMS ---
class AdminStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    LOCKED = "locked"
    INVITED = "invited"

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
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AdminTeam(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    member_count: int = 0
    default_role_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AdminUser(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: EmailStr
    full_name: str
    role: str # role_id or name
    department: str = "General"
    status: AdminStatus = AdminStatus.ACTIVE
    is_2fa_enabled: bool = False
    last_login: Optional[datetime] = None
    last_ip: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AdminSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    admin_id: str
    admin_name: str
    ip_address: str
    device_info: str
    login_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_active: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
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
    sent_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime

class AdminAPIKey(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    owner_id: str # Admin or Team ID
    key_prefix: str # "sk_..."
    permissions: List[str] = []
    status: str = "active"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_used: Optional[datetime] = None

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
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    risk_level: str = "low"  # low, medium, high, critical

class AdminLoginHistory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    admin_id: str
    admin_name: str
    login_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
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
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_by: str

class AdminIPRestriction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    admin_id: Optional[str] = None  # If None, applies to all admins
    ip_address: str
    restriction_type: str  # "allowed", "blocked"
    reason: Optional[str] = None
    added_by: str
    added_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
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
    first_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

# --- REPORTS MODELS ---

class ReportSchedule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    report_type: str 
    frequency: str 
    recipients: List[str] = []
    format: str = "pdf"
    next_run: datetime
    active: bool = True

class ExportJob(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str
    status: str = "processing" 
    requested_by: str
    download_url: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# --- CMS MODELS ---

class CMSPage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    slug: str
    language: str = "en"
    template: CMSPageType = CMSPageType.STATIC
    status: CMSStatus = CMSStatus.DRAFT
    content_blocks: List[Dict[str, Any]] = [] 
    seo: Dict[str, Any] = {} 
    publish_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_by: Optional[str] = None

class CMSMenu(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    location: str 
    items: List[Dict[str, Any]] = [] 
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CMSBanner(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str 
    position: CMSBannerPosition
    language: str = "en"
    image_desktop: str
    image_mobile: Optional[str] = None
    link_url: Optional[str] = None
    status: CMSStatus = CMSStatus.DRAFT
    priority: int = 0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    targeting: Dict[str, Any] = {} 

class CMSLayout(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str 
    sections: List[Dict[str, Any]] = [] 
    status: CMSStatus = CMSStatus.DRAFT

class CMSCollection(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: str 
    rules: Dict[str, Any] = {}
    game_ids: List[str] = []

class CMSPopup(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    type: str 
    targeting: Dict[str, Any] = {}
    status: CMSStatus = CMSStatus.DRAFT

class CMSRedirect(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    from_url: str
    to_url: str
    type: int = 301

class CMSTranslation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    key: str
    default_text: str
    translations: Dict[str, str] = {} 

class CMSMedia(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    type: str
    url: str
    size: int
    tags: List[str] = []
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CMSLegalDoc(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str 
    version: str
    content: str
    effective_date: datetime
    status: CMSStatus = CMSStatus.DRAFT

class CMSExperiment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    target_type: str 
    variants: List[Dict[str, Any]] = []
    status: str = "running"
    results: Dict[str, Any] = {}

class CMSMaintenance(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message: str
    type: str 
    start_time: datetime
    end_time: datetime
    active: bool = True

class CMSAuditLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    admin_id: str
    action: str
    target_type: str
    target_id: str
    diff: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CMSDashboardStats(BaseModel):
    published_pages: int
    active_banners: int
    draft_count: int
    scheduled_count: int
    recent_changes: List[CMSAuditLog] = []

# --- EXISTING MODULES (RG, Risk, etc.) ---

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
    exclusion_end: Optional[datetime] = None 
    last_assessment_date: Optional[datetime] = None
    notes: List[Dict[str, Any]] = []

class RGRule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    conditions: Dict[str, Any] = {} 
    actions: List[str] = [] 
    severity: RGAlertSeverity
    active: bool = True

class RGAlert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    player_id: str
    rule_id: Optional[str] = None
    type: str 
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
    risk_distribution: Dict[str, int] 

class RiskRuleCondition(BaseModel):
    field: str 
    operator: str 
    value: Any
    description: Optional[str] = None

class RiskRuleAction(BaseModel):
    type: RiskActionType
    parameters: Dict[str, Any] = {} 

class RiskRule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    category: RiskCategory
    severity: RiskSeverity
    priority: int = 1
    status: str = "active" 
    conditions: List[RiskRuleCondition] = []
    actions: List[RiskRuleAction] = []
    score_impact: int = 0
    version: int = 1
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class VelocityRule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str 
    event_type: str 
    time_window_minutes: int
    threshold_count: int
    action: RiskActionType
    status: str = "active"

class BlacklistEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str 
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
    evidence_ids: List[str] = [] 
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
    related_id: str 
    type: str 
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

# --- SYSTEM LOGS ---

class LogSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ServiceStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"

class JobStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"
    RUNNING = "running"

class DeployStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    ROLLBACK = "rollback"
    CANCELED = "canceled"

class SystemEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    module: str
    severity: LogSeverity
    event_type: str
    message: str
    host: Optional[str] = None
    correlation_id: Optional[str] = None

class CronLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_name: str
    job_id: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    duration_ms: Optional[float] = None
    status: JobStatus = JobStatus.RUNNING
    error_message: Optional[str] = None

class ServiceHealth(BaseModel):
    service_name: str
    status: ServiceStatus
    latency_ms: float
    error_rate: float
    instance_count: int
    last_heartbeat: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DeploymentLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    environment: str
    service: str
    version: str
    initiated_by: str
    status: DeployStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    changelog: str

class ConfigChangeLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    admin_id: str
    target: str
    diff: Dict[str, Any] 
    severity: LogSeverity
    requires_restart: bool = False

class ErrorLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    service: str
    error_type: str
    severity: LogSeverity
    message: str
    stack_trace: Optional[str] = None
    impact_users: int = 0
    correlation_id: Optional[str] = None

class QueueLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    queue_name: str
    payload_type: str
    started_at: datetime
    duration_ms: float
    retries: int = 0
    status: str
    error: Optional[str] = None

class DBLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    execution_time_ms: float
    query_snippet: str
    affected_rows: int
    is_slow: bool = False

class CacheLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    cache_type: str 
    operation: str 
    key: str
    ttl: int

class LogArchive(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    log_type: str
    date_range: str
    size_mb: float
    storage_type: str 
    status: str 

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

class SystemLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    level: str 
    service: str 
    message: str
    details: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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


# --- FEATURE FLAGS & A/B TESTING ENUMS ---
class FlagStatus(str, Enum):
    ON = "on"
    OFF = "off"
    SCHEDULED = "scheduled"

class FlagType(str, Enum):
    BOOLEAN = "boolean"
    STRING = "string"
    NUMBER = "number"
    JSON = "json"

class FlagScope(str, Enum):
    FRONTEND = "frontend"
    BACKEND = "backend"
    BOTH = "both"

class Environment(str, Enum):
    PRODUCTION = "production"
    STAGING = "staging"
    DEVELOPMENT = "development"

class ExperimentStatus(str, Enum):
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"

class MetricType(str, Enum):
    CTR = "ctr"
    CONVERSION = "conversion"
    DEPOSIT = "deposit"
    RETENTION = "retention"
    GAME_REVENUE = "game_revenue"
    SESSION_TIME = "session_time"

# --- FEATURE FLAGS MODELS ---

class FeatureFlag(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    flag_id: str  # user-friendly ID like "new_payment_flow"
    name: str
    description: str
    status: FlagStatus = FlagStatus.OFF
    type: FlagType = FlagType.BOOLEAN
    default_value: Any = False
    scope: FlagScope = FlagScope.BOTH
    environment: Environment = Environment.PRODUCTION
    targeting: Dict[str, Any] = {}  # {rollout_percentage, countries, vip_levels, tags, device}
    group: Optional[str] = None  # "Payments", "Games", "Fraud", etc.
    last_updated_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    scheduled_activation: Optional[datetime] = None

class FlagGroup(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # "Payments", "Games", "Fraud", "CMS", "CRM"
    description: str
    flag_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Segment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    rules: List[Dict[str, Any]] = []  # [{field, operator, value}]
    population_size: int = 0
    usage_count: int = 0  # how many flags/experiments use this
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ExperimentVariant(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # "A", "B", "C"
    traffic_percentage: float
    value_override: Any = None
    description: Optional[str] = None

class Experiment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    status: ExperimentStatus = ExperimentStatus.DRAFT
    variants: List[ExperimentVariant] = []
    feature_flag_id: Optional[str] = None
    targeting: Dict[str, Any] = {}
    primary_metric: MetricType
    secondary_metrics: List[MetricType] = []
    min_sample_size: int = 1000
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    owner: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ExperimentResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    experiment_id: str
    variant_id: str
    variant_name: str
    users_exposed: int = 0
    conversions: int = 0
    conversion_rate: float = 0.0
    revenue: float = 0.0
    deposit_count: int = 0
    statistical_confidence: float = 0.0
    is_winner: bool = False
    metrics: Dict[str, Any] = {}
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class FlagAnalytics(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    flag_id: str
    date: datetime
    activation_rate: float = 0.0
    traffic_distribution: Dict[str, int] = {}
    error_rate: float = 0.0
    conversion_impact: float = 0.0
    player_behavior_changes: Dict[str, Any] = {}

class FlagAuditLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    admin_id: str
    admin_name: str
    action: str  # created, updated, deleted, activated, deactivated
    target_type: str  # "flag" or "experiment"
    target_id: str
    target_name: str
    before_value: Optional[Dict[str, Any]] = None
    after_value: Optional[Dict[str, Any]] = None
    ip_address: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class EnvironmentComparison(BaseModel):
    flag_id: str
    flag_name: str
    production: Dict[str, Any]
    staging: Dict[str, Any]
    differences: List[str] = []



# --- SIMULATION LAB ENUMS ---
class SimulationType(str, Enum):
    GAME_MATH = "game_math"
    PORTFOLIO = "portfolio"
    BONUS = "bonus"
    COHORT_LTV = "cohort_ltv"
    RISK = "risk"
    RG = "rg"
    AB_VARIANT = "ab_variant"
    MIXED = "mixed"

class SimulationStatus(str, Enum):
    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class GameType(str, Enum):
    SLOTS = "slots"
    BLACKJACK = "blackjack"
    ROULETTE = "roulette"
    BACCARAT = "baccarat"
    CRASH = "crash"
    OTHER = "other"

# --- SIMULATION LAB MODELS ---

class SimulationRun(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    simulation_type: SimulationType
    status: SimulationStatus = SimulationStatus.DRAFT
    input_snapshot: Dict[str, Any] = {}
    created_by: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    notes: str = ""
    tags: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class GameMathSimulation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str
    game_type: GameType
    game_id: Optional[str] = None
    game_name: str
    spins_to_simulate: int = 10000
    seed: Optional[int] = None
    rtp_override: Optional[float] = None
    bet_config: Dict[str, Any] = {}
    results: Dict[str, Any] = {}
    distribution: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PortfolioSimulation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str
    games: List[Dict[str, Any]] = []
    current_ggr: float = 0.0
    simulated_ggr: float = 0.0
    current_ngr: float = 0.0
    simulated_ngr: float = 0.0
    jackpot_cost: float = 0.0
    bonus_cost: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BonusSimulation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str
    bonus_template_id: str
    bonus_type: str
    current_percentage: float
    new_percentage: float
    current_wagering: float
    new_wagering: float
    max_win: float
    target_segment: str
    expected_participants: int
    results: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CohortLTVSimulation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str
    segment_id: str
    segment_name: str
    time_horizon_days: int = 90
    baseline_ltv: float = 0.0
    simulated_ltv: float = 0.0
    deposit_frequency: float = 0.0
    churn_rate: float = 0.0
    bonus_cost: float = 0.0
    rg_flag_rate: float = 0.0
    fraud_risk_impact: float = 0.0
    policy_changes: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RiskSimulation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str
    risk_rules: List[Dict[str, Any]] = []
    time_window_days: int = 30
    total_alerts_current: int = 0
    total_alerts_simulated: int = 0
    fraud_caught: int = 0
    false_positives: int = 0
    auto_freeze_count: int = 0
    withdrawal_blocks: int = 0
    lost_revenue: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RGSimulation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str
    current_policy: Dict[str, Any] = {}
    new_policy: Dict[str, Any] = {}
    affected_players: int = 0
    deposits_reduction: float = 0.0
    high_loss_reduced: float = 0.0
    revenue_impact: float = 0.0
    players_hitting_limit_current: int = 0
    players_hitting_limit_simulated: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ABVariantSimulation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str
    experiment_id: str
    experiment_name: str
    variants: List[Dict[str, Any]] = []
    player_behaviour_model: Dict[str, Any] = {}
    conversion_uplift: float = 0.0
    revenue_uplift: float = 0.0
    risk_uptick: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ScenarioBuilder(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str
    scenario_name: str
    scope: List[str] = []
    changes: Dict[str, Any] = {}
    time_horizon_days: int = 30
    target_players: int = 100000
    consolidated_results: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# --- SETTINGS PANEL / MULTI-TENANT ENUMS ---
class BrandStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"

class MaintenanceType(str, Enum):
    FULL = "full"
    GAMES = "games"
    PAYMENTS = "payments"
    PARTIAL = "partial"

class ConfigEnvironment(str, Enum):
    STAGING = "staging"
    PRODUCTION = "production"
    QA = "qa"

class ConfigStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    LIVE = "live"
    ROLLED_BACK = "rolled_back"

# --- SETTINGS PANEL MODELS ---

class Brand(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    brand_name: str
    status: BrandStatus = BrandStatus.ACTIVE
    default_currency: str = "USD"
    default_language: str = "en"
    domains: List[str] = []
    languages_supported: List[str] = ["en"]
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    contact_info: Dict[str, Any] = {}
    timezone: str = "UTC"
    country_availability: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DomainMarket(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    domain: str
    brand_id: str
    market: str  # TR, EU, LATAM, CA
    status: str = "active"
    geo_targeting_rules: Dict[str, Any] = {}
    currency: str = "USD"
    payment_methods: List[str] = []
    rg_ruleset: str = "default"
    regulatory_class: str = "standard"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Currency(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    currency_code: str
    symbol: str
    exchange_rate: float = 1.0
    base_currency: str = "USD"
    update_method: str = "manual"  # manual or API
    rounding_rules: Dict[str, Any] = {}
    min_deposit: float = 10.0
    max_deposit: float = 10000.0
    min_bet: float = 0.1
    max_bet: float = 1000.0
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PaymentProvider(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    provider_name: str
    brand_id: str
    provider_type: str  # deposit or withdrawal
    api_keys: Dict[str, str] = {}  # masked
    status: str = "active"
    availability_countries: List[str] = []
    min_amount: float = 10.0
    max_amount: float = 10000.0
    fees: Dict[str, Any] = {}
    last_health_check: Optional[datetime] = None
    health_status: str = "unknown"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CountryRule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    country_code: str
    country_name: str
    is_allowed: bool = True
    games_allowed: bool = True
    bonuses_allowed: bool = True
    kyc_level: int = 1
    payment_restrictions: List[str] = []
    default_language: str = "en"
    regulatory_notes: str = ""
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class GameAvailabilityRule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    game_id: str
    brand_id: str
    country_code: str
    is_allowed: bool = True
    rtp_override_allowed: bool = False
    provider_restrictions: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CommunicationProvider(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    provider_name: str
    provider_type: str  # email, sms, push
    api_keys: Dict[str, str] = {}
    from_name: Optional[str] = None
    from_number: Optional[str] = None
    rate_limits: Dict[str, int] = {}
    country_restrictions: List[str] = []
    status: str = "active"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RegulatorySettings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    jurisdiction: str
    age_verification_required: bool = True
    min_age: int = 18
    kyc_tiers: List[Dict[str, Any]] = []
    self_exclusion_rules: Dict[str, Any] = {}
    betting_limits: Dict[str, Any] = {}
    min_rtp_requirement: float = 85.0
    aml_threshold: float = 10000.0
    pep_check_required: bool = True
    rg_messages: Dict[str, str] = {}
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PlatformDefaults(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    default_language: str = "en"
    default_currency: str = "USD"
    default_timezone: str = "UTC"
    session_timeout_minutes: int = 30
    password_min_length: int = 8
    require_2fa: bool = False
    cache_ttl_seconds: int = 300
    pagination_default: int = 20
    api_rate_limit_per_minute: int = 60
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class APIKey(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    key_name: str
    key_hash: str  # hashed API key
    owner: str  # brand_id or "system"
    permissions: List[str] = []
    last_used: Optional[datetime] = None
    status: str = "active"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Webhook(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    endpoint_url: str
    secret_token: str
    retry_policy: Dict[str, Any] = {"max_retries": 3, "backoff": "exponential"}
    status: str = "active"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ThemeBranding(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    brand_id: str
    logo_url: Optional[str] = None
    color_palette: Dict[str, str] = {}
    typography: Dict[str, str] = {}
    background_images: List[str] = []
    email_templates: Dict[str, str] = {}
    custom_css: Optional[str] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MaintenanceSchedule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    brand_id: str
    maintenance_type: MaintenanceType
    start_time: datetime
    end_time: datetime
    message: Dict[str, str] = {}  # multilingual
    affecting: List[str] = ["entire_site"]
    status: str = "scheduled"
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ConfigVersion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    version_number: str
    created_by: str
    environment: ConfigEnvironment
    change_summary: str
    config_snapshot: Dict[str, Any] = {}
    status: ConfigStatus = ConfigStatus.DRAFT
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deployed_at: Optional[datetime] = None

class ConfigAuditLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    admin_id: str
    admin_name: str
    action: str
    module: str
    before_value: Optional[Dict[str, Any]] = None
    after_value: Optional[Dict[str, Any]] = None
    ip_address: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


