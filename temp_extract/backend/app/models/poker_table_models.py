from typing import Optional
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
import uuid

class PokerTable(SQLModel, table=True):
    """Poker Table Management."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(index=True)
    
    name: str
    game_type: str = "TEXAS_HOLDEM"
    limit_type: str = "NO_LIMIT" # NO_LIMIT, POT_LIMIT
    
    # Financials
    small_blind: float
    big_blind: float
    min_buyin: float
    max_buyin: float
    currency: str = "USD"
    
    # Rake Config Link
    rake_profile_id: Optional[str] = Field(default=None, index=True)
    
    # State
    status: str = "active" # active, maintenance, closed
    current_players: int = 0
    max_players: int = 6
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PokerSession(SQLModel, table=True):
    """Player Session at a Table."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(index=True)
    
    player_id: str = Field(index=True)
    table_id: str = Field(foreign_key="pokertable.id", index=True)
    
    status: str = "active" # active, ended
    buyin_total: float = 0.0
    cashout_total: float = 0.0
    
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None
