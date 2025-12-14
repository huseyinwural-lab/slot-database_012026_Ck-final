from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from pydantic.config import ConfigDict


class AdminUserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str

    username: str
    email: str
    full_name: str

    role: str
    tenant_role: Optional[str] = None
    is_platform_owner: bool = False

    status: str
    is_active: bool
    failed_login_attempts: int

    created_at: datetime
