from fastapi import APIRouter, Depends, Body
from sqlmodel import select, Field, SQLModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from app.core.database import get_session
from app.utils.auth import get_current_admin, AdminUser

router = APIRouter(prefix="/api/v1/api-keys", tags=["api_keys"])

class APIKey(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(index=True)
    name: str
    key_hash: str
    scopes: str # Comma separated
    status: str = "active"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

@router.get("/", response_model=List[APIKey])
async def get_api_keys(
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    query = select(APIKey).where(APIKey.tenant_id == current_admin.tenant_id)
    result = await session.execute(query)
    # Frontend APIKeysPage.jsx expects array
    return result.scalars().all()

@router.post("/")
async def create_api_key(
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    import secrets
    raw_key = secrets.token_urlsafe(32)
    
    key = APIKey(
        tenant_id=current_admin.tenant_id,
        name=payload.get("name", "New Key"),
        key_hash=f"sk_{raw_key[:4]}...{raw_key[-4:]}", 
        scopes=",".join(payload.get("scopes", []))
    )
    session.add(key)
    await session.commit()
    await session.refresh(key)
    return key
