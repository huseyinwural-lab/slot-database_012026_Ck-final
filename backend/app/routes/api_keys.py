from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Body, status, Request
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel

from config import settings
from app.models.domain.admin import AdminUser, AdminAPIKey
from app.utils.auth import get_current_admin
from app.utils.api_keys import generate_api_key, validate_scopes
from app.constants.api_keys import API_KEY_SCOPES
from app.utils.features import ensure_tenant_feature


router = APIRouter(prefix="/api/v1/api-keys", tags=["api_keys"])


def get_db():
    client = AsyncIOMotorClient(settings.mongo_url)
    return client[settings.db_name]


class APIKeyCreateRequest(BaseModel):
    name: str
    tenant_id: Optional[str] = None
    scopes: List[str]


class APIKeyMetaResponse(BaseModel):
    id: str
    owner_admin_id: str
    tenant_id: str
    name: str
    key_prefix: str
    scopes: List[str]
    active: bool
    created_at: datetime
    last_used_at: Optional[datetime] = None


@router.get("/scopes", response_model=List[str])
async def list_api_key_scopes(current_admin: AdminUser = Depends(get_current_admin)):
    return API_KEY_SCOPES


@router.get("/", response_model=List[APIKeyMetaResponse])
async def list_api_keys(current_admin: AdminUser = Depends(get_current_admin)):
    db = get_db()
    cursor = db.admin_api_keys.find(
        {"owner_admin_id": current_admin.id},
        {"_id": 0, "key_hash": 0},
    )
    docs = await cursor.to_list(100)
    return [APIKeyMetaResponse(**d) for d in docs]


@router.post("", status_code=201)
@router.post("/", status_code=201)
async def create_api_key(
    payload: APIKeyCreateRequest,
    request: Request,
    current_admin: AdminUser = Depends(get_current_admin),
):
    # Admin-level key management; require tenant feature flag can_manage_admins
    db = get_db()
    await ensure_tenant_feature(request, current_admin, "can_manage_admins", db)

    validate_scopes(payload.scopes)

    full_key, key_prefix, key_hash = generate_api_key()

    tenant_id = payload.tenant_id or current_admin.tenant_id

    api_key_obj = AdminAPIKey(
        owner_admin_id=current_admin.id,
        tenant_id=tenant_id,
        name=payload.name,
        key_prefix=key_prefix,
        key_hash=key_hash,
        scopes=payload.scopes,
        active=True,
        created_at=datetime.now(timezone.utc),
    )
    doc = api_key_obj.model_dump()

    await db.admin_api_keys.insert_one(doc)

    meta = {k: v for k, v in doc.items() if k not in {"key_hash", "_id"}}

    # Response intentionally kept simple JSON-serializable types only
    return {
        "api_key": full_key,
        "key": meta,
    }


@router.patch("/{key_id}", response_model=APIKeyMetaResponse)
async def update_api_key(
    key_id: str,
    request: Request,
    active: Optional[bool] = Body(None, embed=True),
    current_admin: AdminUser = Depends(get_current_admin),
):
    db = get_db()
    await ensure_tenant_feature(request, current_admin, "can_manage_admins", db)

    doc = await db.admin_api_keys.find_one({"id": key_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="API key not found")

    if doc.get("owner_admin_id") != current_admin.id:
        raise HTTPException(status_code=403, detail="FORBIDDEN")

    update_fields = {}
    if active is not None:
        update_fields["active"] = active

    if update_fields:
        await db.admin_api_keys.update_one({"id": key_id}, {"$set": update_fields})

    updated = await db.admin_api_keys.find_one({"id": key_id}, {"_id": 0, "key_hash": 0})
    return APIKeyMetaResponse(**updated)
