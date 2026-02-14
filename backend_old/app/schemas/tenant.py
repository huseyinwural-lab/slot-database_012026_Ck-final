from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class TenantCreateRequest(BaseModel):
    """Request model for creating a tenant.

    Security:
    - Explicitly forbids unknown fields (e.g., `is_system`) so it cannot be smuggled
      through payloads.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1)
    type: str = Field(default="renter")  # owner | renter
    features: Dict = Field(default_factory=dict)


class TenantUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    features: Optional[Dict] = None
    type: Optional[str] = None
