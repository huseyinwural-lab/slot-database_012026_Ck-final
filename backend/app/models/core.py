from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid

# Enums
class PlayerStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    BANNED = "banned"
    SELF_EXCLUDED = "self_excluded"

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

class TransactionStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING_SECOND_APPROVAL = "waiting_second_approval" 
    FRAUD_FLAGGED = "fraud_flagged"

# --- NEW GAME STATUS ENUMS ---
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

# Core Models
class Player(BaseModel):
    id: str = Field(..., description="Player ID")
    tenant_id: str = "default_casino" 
    username: str
    email: EmailStr
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    dob: Optional[datetime] = None
    address: Optional[str] = None
    balance_real: float = 0.0
    balance_bonus: float = 0.0
    balance_locked: float = 0.0 
    status: PlayerStatus = PlayerStatus.ACTIVE
    vip_level: int = 1
    kyc_status: KYCStatus = KYCStatus.NOT_SUBMITTED
    registered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None
    country: str = "Unknown"
    risk_score: str = "low" 
    tags: List[str] = [] 
    luck_boost_factor: float = 1.0 
    luck_boost_remaining_spins: int = 0

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
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processed_at: Optional[datetime] = None
    admin_note: Optional[str] = None
    approver_id: Optional[str] = None 

# --- GAME ADVANCED MODELS ---

class Paytable(BaseModel):
    version: str = "1.0.0"
    symbols: List[Dict[str, Any]] = [] # {id, name, pays: [x3, x4, x5]}
    lines: int = 20

class JackpotConfig(BaseModel):
    type: str # grand, major, minor, mini
    seed_amount: float
    contribution_percent: float
    hit_frequency: float
    current_value: float = 0.0

class ReelStrip(BaseModel):
    reel_id: int
    symbols: List[str] # ["A", "K", "Q", "J", ...]
    weights: Optional[List[int]] = None

class GameConfig(BaseModel):
    rtp: float = 96.0
    volatility: str = "medium" 
    min_bet: float = 0.10
    max_bet: float = 100.00
    max_win_multiplier: int = 5000
    bonus_buy_enabled: bool = False
    paytable: Optional[Paytable] = None
    jackpots: List[JackpotConfig] = []
    reel_strips: List[ReelStrip] = []
    version: str = "1.0.0"

class Game(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = "default_casino"
    name: str
    provider: str
    category: str 
    
    # New Status Fields
    business_status: BusinessStatus = BusinessStatus.DRAFT
    runtime_status: RuntimeStatus = RuntimeStatus.OFFLINE
    
    # New Special Fields
    is_special_game: bool = False
    special_type: SpecialType = SpecialType.NONE
    
    image_url: Optional[str] = None
    configuration: GameConfig = Field(default_factory=GameConfig)
    tags: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Auto-Suggestion Flags (Transient)
    suggestion_reason: Optional[str] = None

class CustomTable(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    game_type: str # Blackjack, Roulette
    provider: str
    
    # Updated Fields
    business_status: BusinessStatus = BusinessStatus.DRAFT
    runtime_status: RuntimeStatus = RuntimeStatus.OFFLINE
    is_special_game: bool = False
    special_type: SpecialType = SpecialType.NONE
    
    currency: str = "USD"
    min_bet: float
    max_bet: float
    seats: int = 7
    dealer_language: str = "EN"
    schedule_start: Optional[str] = None # "18:00"
    schedule_end: Optional[str] = None # "02:00"
    visibility_segments: List[str] = [] # ["VIP", "TR"]

class GameUploadLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    admin_id: str
    provider: str
    total_games: int
    success_count: int
    error_count: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# --- BONUS & OTHERS ---

class BonusRule(BaseModel):
    min_deposit: Optional[float] = None
    reward_amount: Optional[float] = None
    reward_percentage: Optional[float] = None
    luck_boost_factor: Optional[float] = None
    luck_boost_spins: Optional[int] = None
    cashback_percentage: Optional[float] = None

class Bonus(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: str
    description: str = ""
    wager_req: int = 35
    status: str = "active"
    valid_until: Optional[datetime] = None
    rules: BonusRule = Field(default_factory=BonusRule)
    auto_apply: bool = False

class TicketMessage(BaseModel):
    sender: str 
    text: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Ticket(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    player_id: str
    player_username: str
    subject: str
    status: str = "open" 
    priority: str = "medium"
    messages: List[TicketMessage] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class KPIMetric(BaseModel):
    value: float
    change_percent: float 
    trend: str 

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

# --- NEW ARCHITECTURE MODELS ---

class FeatureFlag(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    key: str 
    description: str
    is_enabled: bool = False
    rollout_percentage: int = 0 
    target_countries: List[str] = [] 

class ApprovalRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str 
    related_entity_id: str 
    requester_admin: str
    amount: Optional[float] = None
    status: str = "pending" 
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    details: Dict[str, Any] = {}

class AuditLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    admin_id: str
    action: str
    target_id: str
    details: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class LoginLog(BaseModel):
    player_id: str
    ip_address: str
    location: str
    device_info: str
    status: str 
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
