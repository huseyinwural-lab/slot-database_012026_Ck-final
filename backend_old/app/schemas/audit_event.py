from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class AuditEventPublic(BaseModel):
    id: str
    timestamp: datetime

    request_id: str
    actor_user_id: str
    actor_role: Optional[str] = None
    tenant_id: str

    action: str
    resource_type: str
    resource_id: Optional[str] = None
    
    result: str # Legacy
    status: Optional[str] = "SUCCESS" # Task 4
    reason: Optional[str] = None

    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    details: Dict[str, Any] = {}
    before_json: Optional[Dict[str, Any]] = None
    after_json: Optional[Dict[str, Any]] = None
    diff_json: Optional[Dict[str, Any]] = None
    metadata_json: Optional[Dict[str, Any]] = None
    
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class AuditEventListResponse(BaseModel):
    items: list[AuditEventPublic]
    meta: Dict[str, Any]
