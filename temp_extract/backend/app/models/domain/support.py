from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

# --- SUPPORT ENUMS ---
class TicketPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_PLAYER = "waiting_player"
    SOLVED = "solved"
    CLOSED = "closed"

class ChatStatus(str, Enum):
    QUEUED = "queued"
    ACTIVE = "active"
    ENDED = "ended"
    MISSED = "missed"

# --- SUPPORT MODELS ---

class CannedResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    category: str 
    language: str = "en"
    tags: List[str] = []

class Macro(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    actions: List[Dict[str, Any]] = [] 
    active: bool = True

class SupportWorkflow(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    trigger_event: str 
    conditions: Dict[str, Any] = {} 
    actions: List[Dict[str, Any]] = []
    active: bool = True

class KnowledgeBaseArticle(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    slug: str
    content: str
    category: str
    language: str = "en"
    is_internal: bool = False
    tags: List[str] = []
    views: int = 0
    helpful_count: int = 0
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    sender_type: str 
    sender_id: str
    sender_name: str
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.utcnow())
    attachments: List[str] = []

class ChatSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    player_id: str
    player_name: str
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    status: ChatStatus = ChatStatus.QUEUED
    started_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    ended_at: Optional[datetime] = None
    rating: Optional[int] = None
    tags: List[str] = []
    messages: List[ChatMessage] = []

class SupportTicket(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    subject: str
    description: str
    player_id: str
    player_email: str
    category: str
    priority: TicketPriority = TicketPriority.NORMAL
    status: TicketStatus = TicketStatus.OPEN
    assigned_agent_id: Optional[str] = None
    channel: str = "email" 
    tags: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    messages: List[Dict[str, Any]] = [] 
    
class AgentPerformance(BaseModel):
    agent_id: str
    agent_name: str
    tickets_solved: int = 0
    avg_response_time_mins: float = 0.0
    csat_score: float = 0.0
    active_chats: int = 0
    status: str = "online" 
