from typing import Optional, Dict, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON
import uuid

class Game(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(index=True)
    provider_id: str = Field(index=True) # e.g. "pragmatic", "mock"
    external_id: str = Field(index=True) # Provider's game ID
    title: str
    type: str = "slot" # slot, live, table
    rtp: float = 96.5
    is_active: bool = True
    configuration: Dict = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)

class GameSession(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(index=True)
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
    tenant_id: str = Field(index=True)
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
    
    # Unique event ID from provider (Idempotency Key)
    provider_event_id: str = Field(unique=True, index=True)
    
    type: str # BET, WIN, REFUND
    amount: float
    currency: str
    
    # Wallet Transaction Reference
    tx_id: Optional[str] = Field(index=True)
class CallbackNonce(SQLModel, table=True):
    """Replay Protection Store"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    provider_id: str = Field(index=True)
    nonce: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    
    # Constraint: Unique (provider, nonce) handled by logic or composite index manually if needed
    # For now, simplistic check

    
    created_at: datetime = Field(default_factory=datetime.utcnow)
