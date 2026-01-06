from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class PlayerManualBonusGrant(SQLModel, table=True):
    __tablename__ = "player_manual_bonus_grant"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(index=True)
    player_id: str = Field(index=True)

    bonus_type: str = Field(index=True)  # cash | free_spins | other
    amount: Optional[float] = None
    quantity: Optional[int] = None
    expires_at: Optional[datetime] = None

    reason: str
    created_by_admin_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PlayerSessionRevocation(SQLModel, table=True):
    __tablename__ = "player_session_revocation"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(index=True)
    player_id: str = Field(index=True)

    revoked_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0),
        index=True,
    )
    revoked_by_admin_id: str
    reason: str
