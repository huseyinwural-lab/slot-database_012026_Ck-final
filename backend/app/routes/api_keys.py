from fastapi import APIRouter, Depends, Body
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_session
from app.models.sql_models import APIKey
from app.utils.auth import get_current_admin, AdminUser
from app.constants.api_keys import API_KEY_SCOPES

router = APIRouter(prefix="/api/v1/api-keys", tags=["api_keys"])

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
