from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class BonusCampaignCreate(BaseModel):
    name: str
    bonus_type: str  # FREE_SPIN | FREE_BET | MANUAL_CREDIT
    status: str = "draft"  # draft|active|paused|archived
    game_ids: List[str] = []

    # Optional typed fields
    bet_amount: Optional[float] = None
    spin_count: Optional[int] = None
    max_uses: Optional[int] = None

    # Rules bucket
    config: dict = {}


class BonusCampaignOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    tenant_id: str
    name: str
    bonus_type: Optional[str] = None
    status: str
    bet_amount: Optional[float] = None
    spin_count: Optional[int] = None
    max_uses: Optional[int] = None
    config: dict = {}

    game_ids: List[str] = []


class BonusGrantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    tenant_id: str
    campaign_id: str
    player_id: str
    status: str
    bonus_type: Optional[str] = None

    amount_granted: float = 0.0
    remaining_uses: Optional[int] = None

    granted_at: datetime
    expires_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class BonusGrantCreate(BaseModel):
    campaign_id: str
    player_id: str
    amount: Optional[float] = None


class BonusConsumeRequest(BaseModel):
    provider_event_id: Optional[str] = None


class BonusAdminActionRequest(BaseModel):
    reason: str
