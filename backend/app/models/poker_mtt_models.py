from typing import Optional, List, Dict
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON
import uuid

class PokerTournament(SQLModel, table=True):
    """Poker MTT Definition."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(index=True)
    
    name: str
    game_type: str = "TEXAS_HOLDEM"
    limit_type: str = "NO_LIMIT"
    
    # Financials
    buy_in: float
    fee: float
    currency: str = "USD"
    guaranteed_prize: Optional[float] = None
    
    # Structure
    starting_chips: int = 1500
    min_players: int = 2
    max_players: int = 1000
    
    # Schedule
    start_at: datetime
    late_reg_until: Optional[datetime] = None
    
    # Re-entry / Late Reg
    reentry_max: int = 0 # 0 = Freezeout
    reentry_price: Optional[float] = None # If None, equals buy_in
    
    # State Machine: DRAFT -> REG_OPEN -> RUNNING -> FINISHED | CANCELLED
    status: str = Field(default="DRAFT", index=True)
    
    # Results
    prize_pool_total: float = 0.0
    entrants_count: int = 0
    payout_report: Dict = Field(default={}, sa_column=Column(JSON)) # List of winners/ranks
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TournamentRegistration(SQLModel, table=True):
    """Player entry record."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(index=True)
    tournament_id: str = Field(foreign_key="pokertournament.id", index=True)
    player_id: str = Field(index=True)
    
    status: str = "active" # active, busted, unread (refunded)
    buyin_amount: float
    fee_amount: float
    
    registered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # For idempotency/audit
    tx_ref_buyin: str
    tx_ref_fee: str

class RiskSignal(SQLModel, table=True):
    """Risk/Fraud Detection Event."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(index=True)
    
    player_id: Optional[str] = Field(default=None, index=True)
    target_resource_type: Optional[str] = None # 'tournament', 'hand', 'transaction'
    target_resource_id: Optional[str] = None
    
    signal_type: str # 'velocity', 'chip_dumping', 'multi_account'
    severity: str = "medium" # low, medium, high, critical
    status: str = "new" # new, acknowledged, resolved, false_positive
    
    evidence_payload: Dict = Field(default={}, sa_column=Column(JSON))
    
    # NOTE: DB column is TIMESTAMP WITHOUT TIME ZONE in Postgres.
    # Use naive UTC datetime to avoid tz-aware insertion errors.
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
