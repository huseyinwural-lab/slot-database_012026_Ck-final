from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid

# KYC
class KYCDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    player_id: str
    player_username: str
    type: str # passport, id_card, utility_bill
    status: str = "pending" # pending, approved, rejected
    file_url: str
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reviewed_at: Optional[datetime] = None
    admin_note: Optional[str] = None

# CRM
class Campaign(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    subject: str
    content: str
    segment: str
    channel: str # email, sms, push
    status: str = "draft" # draft, sent, scheduled
    sent_at: Optional[datetime] = None
    stats: Dict[str, int] = {"sent": 0, "opened": 0, "clicked": 0}

# CMS
class CMSPage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    slug: str
    content: str
    status: str = "published"
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Banner(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    image_url: str
    target_url: str
    position: str # home_slider, sidebar
    active: bool = True

# Affiliate
class Affiliate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    commission_rate: float = 0.25 # 25%
    total_earnings: float = 0.0
    status: str = "active"

# Risk
class RiskRule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    condition: str # e.g. "deposit > 10000"
    action: str # "flag", "block"
    severity: str # low, medium, high
    active: bool = True

# Admin
class AdminUser(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    role: str # super_admin, support, finance
    active: bool = True
    last_login: Optional[datetime] = None

# Logs
class SystemLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    level: str # info, error, warning
    service: str # payment, game, auth
    message: str
    details: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Responsible Gaming
class RGLimit(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    player_id: str
    type: str # deposit_limit, loss_limit
    amount: float
    period: str # daily, weekly, monthly
    set_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
