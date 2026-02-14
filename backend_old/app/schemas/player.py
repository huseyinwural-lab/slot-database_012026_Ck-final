from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from pydantic.config import ConfigDict


class PlayerPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str

    username: str
    email: str

    balance_real: float
    balance_bonus: float

    status: str
    kyc_status: str
    risk_score: str
    email_verified: bool = False
    sms_verified: bool = False

    last_login: Optional[datetime] = None
    registered_at: datetime
