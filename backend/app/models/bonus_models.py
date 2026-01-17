from typing import Optional, List, Dict
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON
import uuid

# --- BONUS MODULE MODELS ---

# Normalized campaign ↔ games mapping
class BonusCampaignGame(SQLModel, table=True):
    campaign_id: str = Field(foreign_key="bonuscampaign.id", primary_key=True)
    game_id: str = Field(foreign_key="game.id", primary_key=True)


class BonusCampaign(SQLModel, table=True):
    """Defines a bonus offer.

    P0 supports FREE_SPIN / FREE_BET / MANUAL_CREDIT.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(index=True)

    name: str
    type: str  # legacy (keep)
    status: str = "draft"  # draft | active | paused | archived

    # P0 standardized type (case-sensitive)
    bonus_type: Optional[str] = None  # FREE_SPIN | FREE_BET | MANUAL_CREDIT

    # Optional typed fields (mirrors config for deterministic consume)
    bet_amount: Optional[float] = None
    spin_count: Optional[int] = None
    max_uses: Optional[int] = None

    # Rules: multiplier, min_dep, max_bonus, wagering_mult, eligible_games, expiry_hours
    config: Dict = Field(default={}, sa_column=Column(JSON))

    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class BonusGrant(SQLModel, table=True):
    """An instance of a bonus given to a player."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(index=True)
    campaign_id: str = Field(foreign_key="bonuscampaign.id", index=True)
    player_id: str = Field(foreign_key="player.id", index=True)

    bonus_type: Optional[str] = None  # FREE_SPIN | FREE_BET | MANUAL_CREDIT

    amount_granted: float = 0.0
    initial_balance: float = 0.0  # Snapshot

    # P0 consume tracking
    remaining_uses: Optional[int] = None

    # Wagering Tracking (P1)
    wagering_target: float = 0.0
    wagering_contributed: float = 0.0

    status: str = "active"  # active | completed | expired | forfeited | cancelled

    granted_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    expires_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Abuse Tracking
    device_fingerprint: Optional[str] = None
    ip_address: Optional[str] = None
