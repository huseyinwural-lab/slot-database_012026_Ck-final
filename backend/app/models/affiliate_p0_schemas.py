from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PartnerCreate(BaseModel):
    name: str
    email: str


class PartnerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    code: Optional[str] = None
    username: str
    email: str
    status: str
    created_at: datetime


class PartnerStatusRequest(BaseModel):
    reason: str


class OfferCreate(BaseModel):
    name: str
    model: str  # CPA|REVSHARE (P0: CPA only used for accrual)
    currency: str

    cpa_amount: Optional[float] = None
    min_deposit: Optional[float] = None


class OfferOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    name: str
    model: str
    currency: str
    cpa_amount: Optional[float] = None
    min_deposit: Optional[float] = None
    status: str
    created_at: datetime


class OfferStatusRequest(BaseModel):
    reason: str


class TrackingLinkCreate(BaseModel):
    partner_id: str
    offer_id: str
    landing_path: str = "/"
    reason: str


class TrackingLinkOut(BaseModel):
    code: str
    tracking_url: str
    expires_at: Optional[datetime] = None


class ResolveOut(BaseModel):
    landing_path: str
    partner_id: str
    offer_id: str
    currency: str
    expires_at: Optional[datetime] = None


class PayoutCreate(BaseModel):
    partner_id: str
    amount: float
    currency: str
    method: str
    reference: str
    reason: str


class PayoutOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    partner_id: str
    amount: float
    currency: str
    method: str
    reference: str
    reason: str
    created_at: datetime


class CreativeCreate(BaseModel):
    name: str
    type: str
    url: str
    size: Optional[str] = None
    language: Optional[str] = None


class CreativeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    name: str
    type: str
    url: str
    size: Optional[str] = None
    language: Optional[str] = None
    status: str
    created_at: datetime


class ReportSummaryOut(BaseModel):
    clicks: int
    signups: int
    first_deposits: int
    payouts: float
