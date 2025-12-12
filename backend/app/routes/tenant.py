from fastapi import APIRouter, HTTPException, Body, Depends
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

from config import settings
from app.models.tenant import Tenant
from app.models.common import PaginatedResponse, PaginationParams, PaginationMeta
from app.utils.pagination import get_pagination_params
from app.utils.permissions import require_owner
from app.utils.auth import get_current_admin
from app.models.domain.admin import AdminUser

router = APIRouter(prefix="/api/v1/tenants", tags=["tenants"])


from app.core.database import db_wrapper

def get_db():
    return db_wrapper.db


@router.get("/", response_model=PaginatedResponse[Tenant])
async def list_tenants(
    pagination: PaginationParams = Depends(get_pagination_params),
    current_admin: AdminUser = Depends(get_current_admin)
) -> PaginatedResponse[Tenant]:
    # Only owner can see all tenants
    require_owner(current_admin)
    db = get_db()

    # Sort whitelist
    ALLOWED_SORT_FIELDS = {"created_at"}
    sort_field = pagination.sort_by if pagination.sort_by in ALLOWED_SORT_FIELDS else "created_at"
    skip = (pagination.page - 1) * pagination.page_size

    cursor = (
        db.tenants
        .find(
            {},
            {
                "_id": 0,
                "id": 1,
                "name": 1,
                "type": 1,
                "created_at": 1,
                "features.can_use_game_robot": 1,
                "features.can_edit_configs": 1,
                "features.can_manage_bonus": 1,
                "features.can_view_reports": 1,
            },
        )
        .sort(sort_field, -1 if pagination.sort_dir == "desc" else 1)
        .skip(skip)
        .limit(pagination.page_size)
    )

    docs = await cursor.to_list(pagination.page_size)
    total = await db.tenants.count_documents({}) if pagination.include_total else None

    return {
        "items": [Tenant(**d) for d in docs],
        "meta": PaginationMeta(total=total, page=pagination.page, page_size=pagination.page_size),
    }


@router.post("/", response_model=Tenant)
async def create_tenant(
    tenant: Tenant = Body(...),
    current_admin: AdminUser = Depends(get_current_admin)
) -> Tenant:
    # Only owner can create tenants
    require_owner(current_admin)
    db = get_db()
    # Basic uniqueness by name
    existing = await db.tenants.find_one({"name": tenant.name})
    if existing:
        raise HTTPException(status_code=400, detail="Tenant with this name already exists")

    tenant.created_at = datetime.now(timezone.utc)
    tenant.updated_at = tenant.created_at

    await db.tenants.insert_one(tenant.model_dump())
    return tenant


@router.patch("/{tenant_id}")
async def update_tenant_features(
    tenant_id: str,
    features: dict = Body(..., embed=True),
    current_admin: AdminUser = Depends(get_current_admin)
):
    # Only owner can update tenant features
    require_owner(current_admin)
    """Update tenant feature flags"""
    db = get_db()
    
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Update features
    update_data = {
        "features": features,
        "updated_at": datetime.now(timezone.utc)
    }
    
    await db.tenants.update_one(
        {"id": tenant_id},
        {"$set": update_data}
    )
    
    # Return updated tenant
    updated_tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    return Tenant(**updated_tenant)


@router.get("/capabilities")
async def get_tenant_capabilities(current_admin: AdminUser = Depends(get_current_admin)):
    """
    Return current user's tenant capabilities + owner status
    Used by frontend for role-based UI rendering
    """
    from app.utils.permissions import is_owner
    
    db = get_db()
    tenant_id = current_admin.tenant_id
    
    # Get tenant features
    tenant = await db.tenants.find_one(
        {"id": tenant_id},
        {
            "_id": 0,
            "can_use_game_robot": 1,
            "can_edit_configs": 1,
            "can_manage_bonus": 1,
            "can_view_reports": 1,
            "can_manage_admins": 1,
            "can_manage_kyc": 1
        }
    )
    
    if not tenant:
        # Default capabilities if tenant not found
        features = {
            "can_use_game_robot": False,
            "can_edit_configs": False,
            "can_manage_bonus": False,
            "can_view_reports": True,
            "can_manage_admins": False,
            "can_manage_kyc": True
        }
    else:
        features = {
            "can_use_game_robot": tenant.get("can_use_game_robot", False),
            "can_edit_configs": tenant.get("can_edit_configs", False),
            "can_manage_bonus": tenant.get("can_manage_bonus", False),
            "can_view_reports": tenant.get("can_view_reports", True),
            "can_manage_admins": tenant.get("can_manage_admins", False),
            "can_manage_kyc": tenant.get("can_manage_kyc", True)
        }
    
    return {
        "features": features,
        "is_owner": is_owner(current_admin),  # CRITICAL: Owner status
        "tenant_id": tenant_id,
        "tenant_role": current_admin.tenant_role, # Return tenant role
        "tenant_name": tenant.get("name") if tenant else "Unknown"
    }


async def seed_default_tenants():
    db = get_db()
    count = await db.tenants.count_documents({})
    if count == 0:
        default_owner = Tenant(
            id="default_casino",
            name="Default Casino",
            type="owner",
            features={
                "can_use_game_robot": True,
                "can_edit_configs": True,
                "can_manage_bonus": True,
                "can_view_reports": True,
            },
        )
        demo_renter = Tenant(
            id="demo_renter",
            name="Demo Renter",
            type="renter",
            features={
                "can_use_game_robot": True,
                "can_edit_configs": False,
                "can_manage_bonus": True,
                "can_view_reports": True,
                "can_manage_admins": True,
                "can_manage_finance": True,
            },
        )
        await db.tenants.insert_many([
            default_owner.model_dump(),
            demo_renter.model_dump(),
        ])
