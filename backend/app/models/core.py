from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
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

# Core Models
class Player(BaseModel):
    id: str = Field(..., description="Player ID")
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

class Transaction(BaseModel):
    id: str = Field(..., description="Transaction ID")
    player_id: str
    type: TransactionType
    amount: float
    currency: str = "USD"
    status: TransactionStatus = TransactionStatus.PENDING
    method: str  
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processed_at: Optional[datetime] = None
    admin_note: Optional[str] = None

class Game(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    provider: str
    category: str # slot, live, table
    rtp: float
    status: str = "active"
    image_url: Optional[str] = None

class Bonus(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: str # deposit, nodeposit, freespins
    amount: float
    wager_req: int
    status: str = "active"
    valid_until: Optional[datetime] = None

class TicketMessage(BaseModel):
    sender: str # 'admin' or 'player'
    text: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Ticket(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    player_id: str
    player_username: str
    subject: str
    status: str = "open" # open, answered, closed
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
