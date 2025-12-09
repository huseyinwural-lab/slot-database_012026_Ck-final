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

# Core Models
class Player(BaseModel):
    id: str = Field(..., description="Player ID")
    tenant_id: str = "default_casino" 
    username: str
    email: EmailStr
    phone: Optional[str] = None
    balance_real: float = 0.0
    balance_bonus: float = 0.0
    status: PlayerStatus = PlayerStatus.ACTIVE
    vip_level: int = 1
    kyc_status: KYCStatus = KYCStatus.NOT_SUBMITTED
    registered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None
    country: str = "Unknown"
    risk_score: str = "low" 
    address: Optional[str] = None
    dob: Optional[datetime] = None
    luck_boost_factor: float = 1.0 
    luck_boost_remaining_spins: int = 0

class Transaction(BaseModel):
    id: str = Field(..., description="Transaction ID")
    tenant_id: str = "default_casino"
    player_id: str
    type: TransactionType
    amount: float
    currency: str = "USD"
    status: TransactionStatus = TransactionStatus.PENDING
    method: str  
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processed_at: Optional[datetime] = None
    admin_note: Optional[str] = None
    approver_id: Optional[str] = None 

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
    change_percent: float # compared to yesterday
    trend: str # up, down, neutral

class DashboardStats(BaseModel):
    # Core Financials
    ggr: KPIMetric
    ngr: KPIMetric
    total_bets: KPIMetric
    total_wins: KPIMetric
    
    # Operation Health
    provider_health: List[Dict[str, str]] # {provider: "UP", status: "stable"}
    payment_health: List[Dict[str, str]] # {method: "Papara", status: "UP"}
    
    # Risk Snapshot
    risk_alerts: Dict[str, int] # {high_risk_withdrawals: 5, vpn_users: 12}
    
    # Live Activity
    online_users: int
    active_sessions: int
    peak_sessions_24h: int
    
    # Bonus Perf
    bonuses_given_today_count: int
    bonuses_given_today_amount: float
    
    # Lists
    top_games: List[Dict[str, Any]] # name, provider, revenue
    recent_registrations: List[Player]
    
    # Pending
    pending_withdrawals_count: int
    pending_kyc_count: int

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
