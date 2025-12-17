from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class AuditEventPublic(BaseModel):
    id: str
    timestamp: datetime

    request_id: str
    actor_user_id: str
    tenant_id: str

    action: str
    resource_type: str
    resource_id: Optional[str] = None
    result: str

    ip_address: Optional[str] = None
    details: Dict[str, Any] = {}


class AuditEventListResponse(BaseModel):
    items: list[AuditEventPublic]
    meta: Dict[str, Any]
