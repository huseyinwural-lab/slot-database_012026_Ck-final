from __future__ import annotations

from datetime import datetime
from typing import Optional
import uuid

from sqlmodel import SQLModel, Field


class AffiliateOffer(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(index=True)

    name: str
    model: str  # cpa | revshare
    currency: str

    cpa_amount: Optional[float] = None
    min_deposit: Optional[float] = None

    status: str = "active"  # active | paused
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())


class AffiliateLedger(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(index=True)

    partner_id: str = Field(index=True)
    offer_id: Optional[str] = Field(default=None, index=True)
    player_id: Optional[str] = Field(default=None, index=True)

    entry_type: str  # accrual | payout | adjustment
    amount: float
    currency: str

    reference: Optional[str] = None
    reason: Optional[str] = None

    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())


class AffiliatePayout(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(index=True)

    partner_id: str = Field(index=True)
    amount: float
    currency: str
    method: str
    reference: str
    reason: str

    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())


class AffiliateCreative(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(index=True)

    name: str
    type: str
    url: str
    size: Optional[str] = None
    language: Optional[str] = None

    status: str = "active"
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
