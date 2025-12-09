from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime, timezone
from enum import Enum

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
    risk_score: str = "low" # low, medium, high

class Transaction(BaseModel):
    id: str = Field(..., description="Transaction ID")
    player_id: str
    type: TransactionType
    amount: float
    currency: str = "USD"
    status: TransactionStatus = TransactionStatus.PENDING
    method: str  # e.g., "credit_card", "crypto", "bank_transfer"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processed_at: Optional[datetime] = None
    admin_note: Optional[str] = None

class DashboardStats(BaseModel):
    total_deposit_today: float
    total_withdrawal_today: float
    net_revenue_today: float
    active_players_now: int
    pending_withdrawals_count: int
    pending_kyc_count: int
    recent_registrations: List[Player]
