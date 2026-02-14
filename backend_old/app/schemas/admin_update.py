from typing import Optional

from pydantic import BaseModel, EmailStr


class AdminUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    tenant_role: Optional[str] = None
    password: Optional[str] = None


class AdminStatusRequest(BaseModel):
    is_active: bool
