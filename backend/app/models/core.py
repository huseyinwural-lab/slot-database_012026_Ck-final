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
    FRAUD_FLAGGED = "fraud_flagged" # New status

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
    registration_ip: Optional[str] = None
    referral_source: Optional[str] = None
    
    last_login: Optional[datetime] = None
    last_login_ip: Optional[str] = None
    
    country: str = "Unknown"
    risk_score: str = "low" 
    
    tags: List[str] = [] 
    notes: Optional[str] = None 
    
    luck_boost_factor: float = 1.0 
    luck_boost_remaining_spins: int = 0

class Transaction(BaseModel):
    id: str = Field(..., description="Transaction ID")
    tenant_id: str = "default_casino"
    player_id: str
    player_username: Optional[str] = None # Denormalized for lists
    type: TransactionType
    amount: float
    currency: str = "USD"
    status: TransactionStatus = TransactionStatus.PENDING
    method: str  
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processed_at: Optional[datetime] = None
    admin_note: Optional[str] = None
    approver_id: Optional[str] = None 
    reference_id: Optional[str] = None # Provider reference
    provider_response: Optional[Dict[str, Any]] = None # Raw response log

class GameConfig(BaseModel):
    rtp: float = 96.0
    volatility: str = "medium" 
    paytable_id: str = "standard"
    min_bet: float = 0.10
    max_bet: float = 100.00
    max_win_multiplier: int = 5000
    bonus_buy_enabled: bool = False

class Game(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = "default_casino"
    name: str
    provider: str
    category: str 
    status: str = "active"
    image_url: Optional[str] = None
    configuration: GameConfig = Field(default_factory=GameConfig)

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
    status: str # success, failed
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
