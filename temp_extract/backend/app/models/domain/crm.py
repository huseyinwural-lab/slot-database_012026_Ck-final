from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

# --- CRM ENUMS ---
class ChannelType(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"
    WHATSAPP = "whatsapp"

class CampaignStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class MessageStatus(str, Enum):
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"
    OPENED = "opened"
    CLICKED = "clicked"
    UNSUBSCRIBED = "unsubscribed"

# --- CRM MODELS ---

class ChannelConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str 
    type: ChannelType
    provider: str 
    config: Dict[str, Any] = {} 
    rate_limits: Dict[str, int] = {"max_per_minute": 60}
    enabled: bool = True
    default_locale: str = "en"
    supported_locales: List[str] = ["en", "tr"]

class PlayerCommPrefs(BaseModel):
    player_id: str
    email: Optional[str] = None
    phone: Optional[str] = None
    preferred_language: str = "en"
    channels_allowed: Dict[str, bool] = {"email": True, "sms": True, "push": True}
    marketing_opt_in: bool = True
    marketing_opt_in_date: datetime = Field(default_factory=lambda: datetime.utcnow())
    transactional_only: bool = False
    quiet_hours_enabled: bool = False
    quiet_hours_start: Optional[str] = "22:00"
    quiet_hours_end: Optional[str] = "08:00"

class Segment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str 
    description: Optional[str] = None
    type: str = "dynamic" 
    rule_definition: Dict[str, Any] = {} 
    estimated_size: int = 0
    tags: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class MessageTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    channel: ChannelType
    category: str = "marketing" 
    locale: str = "en"
    subject: Optional[str] = None
    body_html: Optional[str] = None
    body_text: Optional[str] = None
    placeholders: List[str] = [] 
    status: str = "active"

class Campaign(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: str = "one_time" 
    channel: ChannelType
    segment_id: str
    template_id: str
    goal: Optional[str] = None 
    status: CampaignStatus = CampaignStatus.DRAFT
    schedule_type: str = "immediate"
    start_at: Optional[datetime] = None
    stats: Dict[str, int] = {"sent": 0, "opened": 0, "clicked": 0}
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class JourneyStep(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    delay_days: int = 0
    channel: ChannelType
    template_id: str

class Journey(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    trigger_event: str 
    steps: List[JourneyStep] = []
    status: str = "active"

class MessageLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    player_id: str
    campaign_id: Optional[str] = None
    template_id: str
    channel: ChannelType
    sent_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    status: MessageStatus = MessageStatus.SENT
    metadata: Dict[str, Any] = {}

class InAppMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    player_id: str
    title: str
    body: str
    type: str = "info"
    is_read: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
