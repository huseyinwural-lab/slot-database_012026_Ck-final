from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum
import uuid

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
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())

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
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class Payout(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    affiliate_id: str
    amount: float
    period_start: datetime
    period_end: datetime
    status: PayoutStatus = PayoutStatus.PENDING
    payment_method: str = "bank_transfer"
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class Creative(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: str 
    size: Optional[str] = None
    url: str
    preview_url: Optional[str] = None
    status: str = "active"
