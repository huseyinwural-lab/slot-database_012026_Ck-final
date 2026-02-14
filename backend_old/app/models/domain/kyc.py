from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

# --- KYC ENUMS ---
class KYCStatus(str, Enum):
    NOT_STARTED = "not_started"
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    SUSPENDED = "suspended"

class DocStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"

# --- KYC MODELS ---

class KYCDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    player_id: str
    player_username: str
    type: str 
    status: str = "pending"
    file_url: str
    uploaded_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    reviewed_at: Optional[datetime] = None
    admin_note: Optional[str] = None

class KYCLevel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str 
    description: str
    requirements: List[str] = [] 
    limits: Dict[str, float] = {}
    active: bool = True

class KYCRule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    condition: str 
    target_level: str 
    action: str 
    active: bool = True

class KYCCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    player_id: str
    type: str 
    status: str 
    provider: str = "Internal Mock"
    checked_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    result_details: Dict[str, Any] = {}

class KYCAuditLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entity_id: str 
    admin_id: str
    action: str 
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.utcnow())

class KYCDashboardStats(BaseModel):
    pending_count: int
    in_review_count: int
    approved_today: int
    rejected_today: int
    level_distribution: Dict[str, int]
    avg_review_time_mins: float
    high_risk_pending: int
