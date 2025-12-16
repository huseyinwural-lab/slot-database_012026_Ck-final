from fastapi import APIRouter, Depends, Body, Request
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_session
from app.models.sql_models import APIKey
from app.utils.auth import get_current_admin, AdminUser
from app.utils.tenant import get_current_tenant_id
from app.constants.api_keys import API_KEY_SCOPES
from app.schemas.api_keys import APIKeyPublic, APIKeyCreatedOnce

router = APIRouter(prefix="/api/v1/api-keys", tags=["api_keys"])


@router.get("/scopes", response_model=List[str])
async def get_scopes():
    # Frontend expects array of strings
    return API_KEY_SCOPES


@router.get("/", response_model=List[APIKeyPublic])
async def get_api_keys(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    query = select(APIKey).where(APIKey.tenant_id == tenant_id)
    result = await session.execute(query)
    keys = result.scalars().all()

    # Never return key_hash
    return [
        APIKeyPublic(
            id=k.id,
            tenant_id=k.tenant_id,
            name=k.name,
            scopes=(k.scopes.split(",") if k.scopes else []),
            active=(k.status == "active"),
            created_at=k.created_at,
            last_used_at=None,
        )
        for k in keys
    ]


@router.post("/", response_model=APIKeyCreatedOnce)
async def create_api_key(
    request: Request,
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

    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    key = APIKey(
        tenant_id=tenant_id,
        name=name,
        key_hash=key_hash,
        scopes=",".join(scopes),
        status="active",
    )

    session.add(key)
    await session.commit()
    await session.refresh(key)

    # Return secret once (create endpoint only)
    return {
        "api_key": full_key,
        "key": {
            "id": key.id,
            "tenant_id": tenant_id,
            "name": key.name,
            "key_prefix": key_prefix,
            "scopes": scopes,
            "active": True,
            "created_at": key.created_at,
            "last_used_at": None,
        },
    }
