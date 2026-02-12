from typing import Optional, Dict, TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON
import uuid

if TYPE_CHECKING:
    from app.models.sql_models import Tenant

class Game(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(foreign_key="tenant.id", index=True)
    
    # Modern fields (Sprint B+)
    provider_id: str = Field(index=True) # e.g. "pragmatic", "mock"
    external_id: str = Field(index=True) # Provider's game ID
    type: str = "slot" # slot, live, table
    rtp: float = 96.5
    is_active: bool = True
    
    # Legacy fields (from sql_models.py) - Kept for compatibility
    name: str = ""
    provider: str = "unknown" # Legacy field
    category: str = "slot"    # Legacy field
    status: str = "draft"
    image_url: Optional[str] = None
    
    configuration: Dict = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    tenant: "Tenant" = Relationship(back_populates="games")

class GameSession(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(foreign_key="tenant.id", index=True)
    player_id: str = Field(index=True)
    game_id: str = Field(foreign_key="game.id")
    provider_session_id: str = Field(index=True)
    currency: str = "USD"
    status: str = "active" # active, closed
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity_at: datetime = Field(default_factory=datetime.utcnow)

class GameRound(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(foreign_key="tenant.id", index=True)
    player_id: str = Field(index=True)
    session_id: str = Field(foreign_key="gamesession.id")
    game_id: str = Field(foreign_key="game.id")
    
    # Provider's Round ID (Must be unique per provider)
    provider_round_id: str = Field(index=True)
    
    status: str = "open" # open, completed, rolled_back
    
    total_bet: float = 0.0
    total_win: float = 0.0
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class GameEvent(SQLModel, table=True):
    """Immutable audit log of every spin/event"""
    __table_args__ = {'extend_existing': True}
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    round_id: str = Field(foreign_key="gameround.id", index=True)
    player_id: str = Field(index=True) # Added Phase 4
    
    # Unique event ID from provider (Idempotency Key)
    # We remove unique=True here to allow composite constraint in DB migration, 
    # but index=True is fine for lookup.
    provider_event_id: str = Field(index=True) 
    provider: str = Field(index=True) # Added Phase 4
    
    type: str # BET, WIN, REFUND
    amount: float
    currency: str
    
    # Wallet Transaction Reference
    tx_id: Optional[str] = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow) # Ensure this exists

class CallbackNonce(SQLModel, table=True):
    """Replay Protection Store"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    provider_id: str = Field(index=True)
    nonce: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    
    # Constraint: Unique (provider, nonce) handled by logic or composite index manually if needed
