from typing import Optional, Dict, TYPE_CHECKING
from datetime import datetime, date
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON, UniqueConstraint
import uuid

if TYPE_CHECKING:
    from app.models.sql_models import Tenant

class Game(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(foreign_key="tenant.id", index=True)
    
    provider_id: str = Field(index=True)
    external_id: str = Field(index=True)
    type: str = "slot"
    rtp: float = 96.5
    is_active: bool = True
    
    name: str = ""
    provider: str = "unknown"
    category: str = "slot"
    status: str = "draft"
    image_url: Optional[str] = None
    
    configuration: Dict = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)

    tenant: "Tenant" = Relationship(back_populates="games")

class GameSession(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(foreign_key="tenant.id", index=True)
    player_id: str = Field(index=True)
    game_id: str = Field(foreign_key="game.id")
    provider_session_id: str = Field(index=True)
    currency: str = "USD"
    status: str = "active" 
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity_at: datetime = Field(default_factory=datetime.utcnow)

class GameRound(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(foreign_key="tenant.id", index=True)
    player_id: str = Field(index=True)
    session_id: str = Field(foreign_key="gamesession.id")
    game_id: str = Field(foreign_key="game.id")
    
    provider_round_id: str = Field(index=True)
    status: str = "open"
    
    total_bet: float = 0.0
    total_win: float = 0.0
    currency: str = Field(default="USD", index=True)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class GameEvent(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    round_id: str = Field(foreign_key="gameround.id", index=True)
    player_id: str = Field(index=True)
    
    provider_event_id: str = Field(index=True) 
    provider: str = Field(index=True)
    type: str 
    amount: float
    currency: str
    
    tx_id: Optional[str] = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CallbackNonce(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    provider_id: str = Field(index=True)
    nonce: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime

# Phase 4C: Aggregation Table
class DailyGameAggregation(SQLModel, table=True):
    __tablename__ = "daily_game_aggregation"
    # Note: Use 'date' string in constraint referencing the DB column name
    __table_args__ = (
        UniqueConstraint("tenant_id", "date", "provider", "currency", name="uq_daily_game_agg"),
        {'extend_existing': True}
    )

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(index=True)
    # The field name in python is 'date_val', mapped to DB column 'date'
    date_val: date = Field(index=True, sa_column=Column("date", sa.Date))
    
    provider: str = Field(index=True)
    currency: str = Field(index=True)
    
    total_bet: float = 0.0
    total_win: float = 0.0
    rounds_count: int = 0
    active_players: int = 0
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
