from fastapi import APIRouter, Depends, Body
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_session
from app.models.sql_models import APIKey
from app.utils.auth import get_current_admin, AdminUser
from app.constants.api_keys import API_KEY_SCOPES

router = APIRouter(prefix="/api/v1/api-keys", tags=["api_keys"])

@router.get("/scopes", response_model=List[str])
async def get_scopes():
    # Frontend expects array of strings
    return API_KEY_SCOPES


@router.get("/", response_model=List[APIKey])
async def get_api_keys(
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    query = select(APIKey).where(APIKey.tenant_id == current_admin.tenant_id)
    result = await session.execute(query)
    return result.scalars().all()


@router.post("/")
async def create_api_key(
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    # Lightweight SQL-only impl for UI: generate a secret shown once.
    # Persist: key_prefix + bcrypt hash.
    from app.utils.api_keys import generate_api_key, validate_scopes

    name = (payload.get("name") or "New Key").strip()
    scopes = payload.get("scopes") or []

    validate_scopes(scopes)

    full_key, key_prefix, key_hash = generate_api_key()

    key = APIKey(
        tenant_id=current_admin.tenant_id,
        name=name,
        key_hash=key_hash,
        scopes=",".join(scopes),
        status="active",
    )

    session.add(key)
    await session.commit()
    await session.refresh(key)

    return {"api_key": full_key, "key": {"id": key.id, "tenant_id": key.tenant_id, "name": key.name, "key_prefix": key_prefix, "scopes": scopes, "active": True}}
