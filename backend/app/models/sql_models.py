from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON, Text
import uuid

# --- SHARED MODELS ---

class Tenant(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str = Field(index=True, unique=True)
    type: str = "renter"  # owner | renter
    features: Dict = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    admins: List["AdminUser"] = Relationship(back_populates="tenant")
    players: List["Player"] = Relationship(back_populates="tenant")
    games: List["Game"] = Relationship(back_populates="tenant")
    tickets: List["SupportTicket"] = Relationship(back_populates="tenant")
    bonuses: List["Bonus"] = Relationship(back_populates="tenant")


class AdminUser(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(foreign_key="tenant.id", index=True)
    username: str
    email: str = Field(unique=True, index=True)
    full_name: str
    password_hash: str
    role: str 
    tenant_role: Optional[str] = "tenant_admin"
    is_platform_owner: bool = False
    status: str = "active"
    is_active: bool = True
    failed_login_attempts: int = 0
    invite_token: Optional[str] = None
    password_reset_token: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    tenant: Tenant = Relationship(back_populates="admins")


class Player(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(foreign_key="tenant.id", index=True)
    username: str = Field(index=True)
    email: str = Field(index=True)
    password_hash: str
    balance_real: float = 0.0
    balance_bonus: float = 0.0
    status: str = "active"
    kyc_status: str = "pending"
    risk_score: str = "low"
    last_login: Optional[datetime] = None
    registered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    tenant: Tenant = Relationship(back_populates="players")
    transactions: List["Transaction"] = Relationship(back_populates="player")
    tickets: List["SupportTicket"] = Relationship(back_populates="player")


class Game(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(foreign_key="tenant.id", index=True)
    name: str
    provider: str
    category: str 
    status: str = "draft"
    rtp: float = 96.0
    image_url: Optional[str] = None
    configuration: Dict = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    tenant: Tenant = Relationship(back_populates="games")


class Transaction(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(foreign_key="tenant.id", index=True)
    player_id: str = Field(foreign_key="player.id", index=True)
    type: str 
    amount: float
    currency: str = "USD"
    status: str 
    method: Optional[str] = None
    provider_tx_id: Optional[str] = None
    balance_after: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    player: Player = Relationship(back_populates="transactions")


# --- NEW MODELS FOR FULL COVERAGE ---

class TicketMessage(SQLModel): # Pydantic-like model for JSON storage
    sender: str
    text: str
    timestamp: str

class SupportTicket(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(foreign_key="tenant.id", index=True)
    player_id: str = Field(foreign_key="player.id", index=True)
    subject: str
    status: str = "open" # open, answered, closed
    priority: str = "medium"
    messages: List[Dict] = Field(default=[], sa_column=Column(JSON)) # List of {sender, text, time}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    tenant: Tenant = Relationship(back_populates="tickets")
    player: Player = Relationship(back_populates="tickets")


class Bonus(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(foreign_key="tenant.id", index=True)
    name: str
    type: str # deposit_match, freespin
    rules: Dict = Field(default={}, sa_column=Column(JSON))
    status: str = "active"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    tenant: Tenant = Relationship(back_populates="bonuses")


class AuditLog(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    admin_id: str
    action: str
    module: str
    target_id: Optional[str] = None
    details: Dict = Field(default={}, sa_column=Column(JSON))
    ip_address: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Affiliate(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(foreign_key="tenant.id", index=True)
    username: str
    email: str
    commission_rate: float = 0.0
    status: str = "active"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RiskRule(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(foreign_key="tenant.id", index=True)
    name: str
    condition: str # "amount > 1000"
    action: str # "flag"
    is_active: bool = True


class ApprovalRequest(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(foreign_key="tenant.id", index=True)
    type: str # withdrawal
    related_entity_id: str
    requester_id: str
    status: str = "pending"
    details: Dict = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ContentPage(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(foreign_key="tenant.id", index=True)
    slug: str
    title: str
    content: str = Field(sa_column=Column(Text))
    status: str = "published"
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
