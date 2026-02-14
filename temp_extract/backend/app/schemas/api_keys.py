from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class APIKeyPublic(BaseModel):
    id: str
    tenant_id: str
    name: str
    scopes: List[str]
    active: bool
    created_at: datetime
    last_used_at: Optional[datetime] = None


class APIKeyMeta(BaseModel):
    id: str
    tenant_id: str
    name: str
    key_prefix: str
    scopes: List[str]
    active: bool
    created_at: datetime
    last_used_at: Optional[datetime] = None


class APIKeyCreatedOnce(BaseModel):
    """Create response. The full secret is returned *once* here."""

    api_key: str
    key: APIKeyMeta
