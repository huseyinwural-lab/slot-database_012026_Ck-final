from typing import Optional, List, Dict
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON
import uuid

# --- SHARED MODELS ---

class Tenant(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str = Field(index=True, unique=True)
    type: str = "renter"  # owner | renter
    # PostgreSQL JSONB for flexible feature flags
    features: Dict = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    admins: List["AdminUser"] = Relationship(back_populates="tenant")
    players: List["Player"] = Relationship(back_populates="tenant")
    games: List["Game"] = Relationship(back_populates="tenant")


class AdminUser(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(foreign_key="tenant.id", index=True)
    username: str
    email: str = Field(unique=True, index=True)
    full_name: str
    password_hash: str
    
    role: str # "Super Admin", "Manager"
    tenant_role: Optional[str] = "tenant_admin" # "finance", "operations"
    is_platform_owner: bool = False
    
    status: str = "active"
    is_active: bool = True
    
    # Auth fields
    failed_login_attempts: int = 0
    invite_token: Optional[str] = None
    password_reset_token: Optional[str] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
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
    
    last_login: Optional[datetime] = None
    registered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    tenant: Tenant = Relationship(back_populates="players")
    transactions: List["Transaction"] = Relationship(back_populates="player")


class Game(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(foreign_key="tenant.id", index=True)
    name: str
    provider: str
    category: str # slot, live
    status: str = "draft"
    rtp: float = 96.0
    image_url: Optional[str] = None
    
    # Flexible Config (JSON)
    configuration: Dict = Field(default={}, sa_column=Column(JSON))
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    tenant: Tenant = Relationship(back_populates="games")


class Transaction(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(foreign_key="tenant.id", index=True)
    player_id: str = Field(foreign_key="player.id", index=True)
    
    type: str # deposit, withdrawal, bet, win
    amount: float
    currency: str = "USD"
    status: str # completed, pending
    
    method: Optional[str] = None
    provider_tx_id: Optional[str] = None
    
    balance_after: float = 0.0
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    player: Player = Relationship(back_populates="transactions")
