from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
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
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
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
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())

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
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())

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
    added_at: datetime = Field(default_factory=lambda: datetime.utcnow())
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
    last_seen: datetime = Field(default_factory=lambda: datetime.utcnow())

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
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class RiskAlert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str 
    message: str
    severity: RiskSeverity
    player_id: Optional[str] = None
    metadata: Dict[str, Any] = {}
    is_resolved: bool = False
    timestamp: datetime = Field(default_factory=lambda: datetime.utcnow())

class Evidence(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    related_id: str 
    type: str 
    description: str
    file_url: Optional[str] = None
    uploaded_by: str
    uploaded_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    tags: List[str] = []

class RiskDashboardStats(BaseModel):
    daily_alerts: int
    open_cases: int
    high_risk_players: int
    suspicious_withdrawals: int
    bonus_abuse_alerts: int
    risk_trend: List[Dict[str, Any]] 
    category_breakdown: Dict[str, int]
