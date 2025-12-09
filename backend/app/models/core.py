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
    
    # New Fields for Luck Boost
    luck_boost_factor: float = 1.0 # 1.0 = normal, 1.5 = 50% more chance
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
    volatility: str = "medium" # low, medium, high
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
    type: str # welcome, deposit, referral, luck_boost, cashback
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

class DashboardStats(BaseModel):
    total_deposit_today: float
    total_withdrawal_today: float
    net_revenue_today: float
    active_players_now: int
    pending_withdrawals_count: int
    pending_kyc_count: int
    recent_registrations: List[Player]

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
