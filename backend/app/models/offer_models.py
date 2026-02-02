from typing import Optional, Dict
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON
import uuid

class Offer(SQLModel, table=True):
    """Catalog of available offers."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(index=True)
    
    name: str
    description: Optional[str] = None
    
    type: str # BONUS_GRANT, CASHBACK, FREESPIN, VIP_REWARD, MESSAGE_ONLY
    cost_model: str = "fixed" # fixed, percentage
    cost_value: float = 0.0 # e.g. 10.0 (fixed $) or 0.5 (50%)
    
    # Constraints & Config
    config: Dict = Field(default={}, sa_column=Column(JSON)) # max_bet, wagering_mult, excluded_games
    eligibility_criteria: Dict = Field(default={}, sa_column=Column(JSON)) # segments, vip_levels
    
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Experiment(SQLModel, table=True):
    """A/B Test Definition."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(index=True)
    
    key: str = Field(index=True) # e.g. "welcome_offer_optimization_q1"
    name: str
    status: str = "draft" # draft, running, stopped, archived
    
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    
    # Variants: { "A": {weight: 50, offer_id: "..."}, "B": {weight: 50, offer_id: "..."} }
    variants: Dict = Field(default={}, sa_column=Column(JSON))
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ExperimentAssignment(SQLModel, table=True):
    """Sticky assignment of a player to an experiment variant."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(index=True)
    
    experiment_id: str = Field(foreign_key="experiment.id", index=True)
    player_id: str = Field(index=True)
    
    variant: str # A, B, Control
    assigned_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Idempotency constraint logic handled in application or unique index
    # We'll use unique index on (experiment_id, player_id)

class OfferDecisionRecord(SQLModel, table=True):
    """Immutable audit log of why an offer was given or denied."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(index=True)
    player_id: str = Field(index=True)
    
    trigger_event: str # e.g. "login", "deposit_success", "cron_churn_check"
    
    # Decision details
    decision: str # "granted", "denied", "hold"
    offer_id: Optional[str] = Field(foreign_key="offer.id")
    experiment_id: Optional[str] = Field(foreign_key="experiment.id")
    variant: Optional[str] = None
    
    deny_reason: Optional[str] = None # e.g. "RG_BLOCKED", "RISK_HIGH"
    score_details: Dict = Field(default={}, sa_column=Column(JSON)) # breakdown of score
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
