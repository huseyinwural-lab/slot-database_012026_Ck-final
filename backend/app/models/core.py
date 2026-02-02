from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

# --- SHARED ENUMS (CORE) ---
class PlayerStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    BANNED = "banned"
    SELF_EXCLUDED = "self_excluded"
    LOCKED = "locked"

class KYCStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NOT_SUBMITTED = "not_submitted"

class TransactionType(str, Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    BONUS = "bonus"
    ADJUSTMENT = "adjustment"
    BET = "bet"
    WIN = "win"
    BONUS_ISSUED = "bonus_issued"
    BONUS_WAGERED = "bonus_wagered"
    BONUS_CANCELLED = "bonus_cancelled"
    JACKPOT_CONTRIBUTION = "jackpot_contribution"
    JACKPOT_WIN = "jackpot_win"

class TransactionStatus(str, Enum):
    REQUESTED = "requested"
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    PROCESSING = "processing"
    PAID = "paid"
    COMPLETED = "completed" # Legacy/Generic
    REJECTED = "rejected"
    FAILED = "failed"
    WAITING_SECOND_APPROVAL = "waiting_second_approval" 
    FRAUD_FLAGGED = "fraud_flagged"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

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

# --- GAME STATUS ENUMS ---
class BusinessStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"

class RuntimeStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    IN_EVENT = "in_event"

class SpecialType(str, Enum):
    NONE = "none"
    VIP = "vip"
    PRIVATE = "private"
    BRANDED = "branded"
    EVENT = "event"

# --- APPROVAL ENUMS ---
class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    ESCALATED = "escalated"

class ApprovalCategory(str, Enum):
    FINANCE = "finance"
    KYC = "kyc"
    BONUS = "bonus"
    GAME = "game"
    RISK = "risk"
    PLAYER = "player"
    AFFILIATE = "affiliate"
    SYSTEM = "system"

# --- CORE MODELS ---

class ApprovalRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: ApprovalCategory = ApprovalCategory.FINANCE
    action_type: str # "withdrawal_approve", "rtp_change"
    related_entity_id: str 
    requester_admin: str
    requester_role: str = "admin"
    assigned_approver_role: Optional[str] = None # "supervisor", "manager"
    assigned_approver_id: Optional[str] = None
    amount: Optional[float] = None
    status: ApprovalStatus = ApprovalStatus.PENDING
    details: Dict[str, Any] = {} # Metadata
    diff: Dict[str, Any] = {} # {old: ..., new: ...}
    notes: List[Dict[str, Any]] = [] # {admin, text, time}
    documents: List[str] = [] # URLs
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class ApprovalRule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    action_type: str
    condition: str # "amount > 5000"
    required_role: str
    auto_approve: bool = False
    sla_hours: int = 24
    active: bool = True

class Delegation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    from_admin_id: str
    to_admin_id: str
    start_date: datetime
    end_date: datetime
    categories: List[ApprovalCategory] = []
    active: bool = True

# --- OTHER CORE MODELS (Preserved) ---

class Player(BaseModel):
    id: str = Field(..., description="Player ID")
    tenant_id: str = "default_casino" 
    username: str
    is_new: bool = True
    email: EmailStr
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    dob: Optional[datetime] = None
    address: Optional[str] = None
    
    # Wallet & Financials
    balance_real: float = 0.0
    balance_bonus: float = 0.0
    balance_locked: float = 0.0 
    pending_withdrawals: float = 0.0
    total_deposits: float = 0.0
    total_withdrawals: float = 0.0
    net_position: float = 0.0 # Deposits - Withdrawals
    
    # Status & Flags
    status: PlayerStatus = PlayerStatus.ACTIVE
    vip_level: int = 1
    kyc_status: KYCStatus = KYCStatus.NOT_SUBMITTED
    kyc_level: int = 0
    account_flags: List[str] = [] # "bonus_abuse", "high_risk", "whale"
    tags: List[str] = [] 
    linked_accounts: List[str] = [] # IDs of other accounts
    
    # Technical & Tracking
    registered_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    last_login: Optional[datetime] = None
    last_ip: Optional[str] = None
    device_fingerprint: Optional[str] = None
    country: str = "Unknown"
    affiliate_source: Optional[str] = None
    
    # Risk
    risk_score: str = "low" # low, medium, high, critical
    fraud_score: int = 0 # 0-100
    
    # Gameplay
    luck_boost_factor: float = 1.0 
    luck_boost_remaining_spins: int = 0

class TransactionTimeline(BaseModel):
    status: str
    timestamp: datetime = Field(default_factory=lambda: datetime.utcnow())
    description: str
    operator: Optional[str] = None

class WageringStatus(BaseModel):
    required: float = 0.0
    current: float = 0.0
    is_met: bool = True
    remaining: float = 0.0

class Transaction(BaseModel):
    id: str = Field(..., description="Transaction ID")
    tenant_id: str = "default_casino"
    player_id: str
    player_username: Optional[str] = None 
    type: TransactionType
    amount: float
    currency: str = "USD"
    status: TransactionStatus = TransactionStatus.PENDING
    method: str  
    
    # Enhanced Financial Fields
    provider: str = "Internal" # "Papara", "Stripe", "CoinPayments"
    provider_tx_id: Optional[str] = None
    destination_address: Optional[str] = None # IBAN, Wallet Address
    affiliate_source: Optional[str] = None
    
    # User Context at Transaction Time
    ip_address: Optional[str] = None
    device_info: Optional[str] = None
    country: Optional[str] = None
    risk_score_at_time: Optional[str] = "low"
    kyc_status_at_time: Optional[str] = "pending"
    
    # Financial Context
    balance_before: Optional[float] = None
    balance_after: Optional[float] = None
    bonus_id: Optional[str] = None # Triggered bonus
    wagering_info: Optional[WageringStatus] = None # Wagering snapshot
    
    # Costs
    fee: float = 0.0
    net_amount: float = 0.0
    
    # Flags
    limit_flags: List[str] = [] # "daily_limit_exceeded"
    velocity_flags: List[str] = [] # "high_velocity"
    aml_flags: List[str] = []
    
    # Operational Fields
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    processed_at: Optional[datetime] = None
    admin_note: Optional[str] = None
    compliance_notes: List[str] = []
    approver_id: Optional[str] = None 
    
    # Detailed Views
    timeline: List[TransactionTimeline] = []
    raw_response: Optional[Dict[str, Any]] = None
    attachments: List[str] = [] # Receipt URLs

# --- GAME ADVANCED MODELS ---

class Paytable(BaseModel):
    version: str = "1.0.0"
    symbols: List[Dict[str, Any]] = [] 
    lines: int = 20

class JackpotConfig(BaseModel):
    type: str 
    seed_amount: float
    contribution_percent: float
    hit_frequency: float
    current_value: float = 0.0

class ReelStrip(BaseModel):
    reel_id: int
    symbols: List[str] 
    weights: Optional[List[int]] = None

class GameConfig(BaseModel):
    rtp: float = 96.0
    volatility: str = "medium" 
    min_bet: float = 0.10
    max_bet: float = 100.00
    max_win_multiplier: int = 5000
    min_balance_to_enter: float = 0.0
    bonus_buy_enabled: bool = False
    paytable: Optional[Paytable] = None
    jackpots: List[JackpotConfig] = []
    reel_strips: List[ReelStrip] = []
    version: str = "1.0.0"

class ClientRuntimeType(str, Enum):
    HTML5 = "html5"
    UNITY = "unity"


class ClientVariant(BaseModel):
    enabled: bool = False
    launch_url: Optional[str] = None
    runtime: ClientRuntimeType = ClientRuntimeType.HTML5
    extra: Dict[str, Any] = {}


class Game(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = "default_casino"
    name: str
    provider: str
    category: str 
    core_type: Optional[str] = None  # Added for crash/dice math config support
    business_status: BusinessStatus = BusinessStatus.DRAFT
    runtime_status: RuntimeStatus = RuntimeStatus.OFFLINE
    is_special_game: bool = False
    special_type: SpecialType = SpecialType.NONE
    image_url: Optional[str] = None
    configuration: GameConfig = Field(default_factory=GameConfig)

    # Client runtimes
    client_variants: Dict[str, ClientVariant] = {}
    primary_client_type: Optional[ClientRuntimeType] = None
    
    # Expanded Fields for Game Ops
    tags: List[str] = [] # "new", "trending", "feature_buy"
    sort_order: int = 0
    hit_frequency: Optional[float] = None
    feature_buy_available: bool = False
    countries_allowed: List[str] = [] # ["TR", "DE"] (Empty = All)
    countries_blocked: List[str] = [] 
    platform: str = "both" # "mobile", "desktop", "both"
    last_updated: datetime = Field(default_factory=lambda: datetime.utcnow())
    provider_game_id: Optional[str] = None
    
    # Metrics
    active_players_24h: int = 0
    ggr_24h: float = 0.0
    
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    suggestion_reason: Optional[str] = None

class CustomTable(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    game_type: str 
    provider: str
    business_status: BusinessStatus = BusinessStatus.DRAFT
    runtime_status: RuntimeStatus = RuntimeStatus.OFFLINE
    is_special_game: bool = False
    special_type: SpecialType = SpecialType.NONE
    currency: str = "USD"
    min_bet: float
    max_bet: float
    seats: int = 7
    dealer_language: str = "EN"
    
    # Expanded Live Table Fields
    schedule_start: Optional[str] = None 
    schedule_end: Optional[str] = None 
    visibility_segments: List[str] = [] # "vip_gold", "high_risk"
    branding_logo_url: Optional[str] = None
    uptime_percentage: float = 99.9
    
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class GameUploadLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    admin_id: str
    provider: str
    total_games: int
    success_count: int
    error_count: int
    validation_warnings: List[str] = []
    status: str = "completed" # "processing", "completed", "failed"
    timestamp: datetime = Field(default_factory=lambda: datetime.utcnow())

# --- BONUS SYSTEM (EXPANDED) ---

class BonusType(str, Enum):
    # Financial
    DEPOSIT_MATCH = "deposit_match"
    THRESHOLD_DEPOSIT = "threshold_deposit"
    HIGH_ROLLER = "high_roller"
    MANUAL_COMP = "manual_comp"
    MONEYBACK = "moneyback"
    MILESTONE = "milestone"
    LADDER = "ladder"
    
    # Balance & RTP
    RTP_BOOSTER = "rtp_booster"
    GUARANTEED_WIN = "guaranteed_win"
    SPINS_POWERUP = "spins_powerup"
    MYSTERY_RTP = "mystery_rtp"
    RAKEBACK = "rakeback"
    
    # Non-Deposit
    WELCOME_NO_DEP = "welcome_no_dep"
    REFERRAL = "referral"
    KYC_COMPLETION = "kyc_completion"
    REACTIVATION = "reactivation"
    BIRTHDAY = "birthday"
    
    # Free Spins
    FREE_SPIN_PACKAGE = "fs_package"
    MULTI_GAME_BUNDLE = "fs_bundle"
    FS_PLUS_BONUS = "fs_plus_bonus"
    VIP_FS_RELOAD = "vip_fs_reload"
    
    # Cashback
    CASHBACK_LOSS = "loss_cashback"
    CASHBACK_PERIODIC = "periodic_cashback"
    CASHBACK_PROVIDER = "provider_cashback"
    CASHBACK_GAME = "game_cashback"

class BonusTrigger(str, Enum):
    MANUAL = "manual"
    REGISTRATION = "registration"
    FIRST_LOGIN = "first_login"
    FIRST_DEPOSIT = "first_deposit"
    DEPOSIT_X = "deposit_amount"
    LOSS_X = "loss_amount"
    BET_X = "bet_amount"
    VIP_LEVEL_UP = "vip_level_up"
    SEGMENT_CHANGE = "segment_change"
    REFERRAL = "referral"
    TOURNAMENT = "tournament"
    RANDOM = "random"

class LadderTier(BaseModel):
    level: int
    deposit_amount: float
    reward_percent: float

class BonusRule(BaseModel):
    min_deposit: Optional[float] = None
    reward_amount: Optional[float] = None 
    reward_percentage: Optional[float] = None 
    max_reward: Optional[float] = None
    luck_boost_factor: Optional[float] = None
    luck_boost_spins: Optional[int] = None
    rtp_boost_percent: Optional[float] = None 
    guaranteed_win_spins: Optional[int] = None
    fs_game_ids: List[str] = []
    fs_count: Optional[int] = None
    fs_bet_value: Optional[float] = None
    cashback_percentage: Optional[float] = None
    provider_ids: List[str] = [] 
    game_ids: List[str] = [] 
    ladder_tiers: List[LadderTier] = []
    milestone_target: Optional[float] = None 
    valid_days: int = 7

class Bonus(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: BonusType = BonusType.DEPOSIT_MATCH
    category: str = "Financial" 
    trigger: BonusTrigger = BonusTrigger.MANUAL
    description: str = ""
    wager_req: int = 35
    status: str = "active"
    valid_until: Optional[datetime] = None
    rules: BonusRule = Field(default_factory=BonusRule)
    auto_apply: bool = False
    tags: List[str] = []

class TicketMessage(BaseModel):
    sender: str 
    text: str
    timestamp: datetime = Field(default_factory=lambda: datetime.utcnow())

class Ticket(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    player_id: str
    player_username: str
    subject: str
    status: str = "open" 
    priority: str = "medium"
    messages: List[TicketMessage] = []
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class KPIMetric(BaseModel):
    value: float
    change_percent: float 
    trend: str 
    description: Optional[str] = None

class DashboardStats(BaseModel):
    ggr: KPIMetric
    ngr: KPIMetric
    total_bets: KPIMetric
    total_wins: KPIMetric
    provider_health: List[Dict[str, str]] 
    payment_health: List[Dict[str, str]] 
    risk_alerts: Dict[str, int] 
    online_users: int
    active_sessions: int
    peak_sessions_24h: int
    bonuses_given_today_count: int
    bonuses_given_today_amount: float
    top_games: List[Dict[str, Any]] 
    recent_registrations: List[Player]
    pending_withdrawals_count: int
    pending_kyc_count: int

class FinancialReport(BaseModel):
    total_deposit: float
    total_withdrawal: float
    net_cashflow: float
    provider_breakdown: Dict[str, float]
    daily_stats: List[Dict[str, Any]]
    
    # Detailed additions
    ggr: float = 0.0
    ngr: float = 0.0
    bonus_cost: float = 0.0
    provider_cost: float = 0.0
    payment_fees: float = 0.0
    fraud_blocked_amount: float = 0.0
    total_player_balance: float = 0.0
    
    # Reports
    fx_impact: float = 0.0
    chargeback_count: int = 0
    chargeback_amount: float = 0.0

# --- NEW ARCHITECTURE MODELS ---

class FeatureFlag(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    key: str 
    description: str
    is_enabled: bool = False
    rollout_percentage: int = 0 
    target_countries: List[str] = [] 

class AuditLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    admin_id: str
    action: str
    target_id: str
    details: str
    timestamp: datetime = Field(default_factory=lambda: datetime.utcnow())

class LoginLog(BaseModel):
    player_id: str
    ip_address: str
    location: str
    device_info: str
    status: str 
    timestamp: datetime = Field(default_factory=lambda: datetime.utcnow())
