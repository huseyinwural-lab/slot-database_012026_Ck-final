from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.sql_models import Tenant, AdminUser
from app.core.errors import AppError
from app.utils.auth import get_current_admin
from app.utils.permissions import require_owner

router = APIRouter(prefix="/api/v1/tenants", tags=["tenants"])

@router.get("/", response_model=dict)
async def list_tenants(
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    require_owner(current_admin)
    
    statement = select(Tenant)
    result = await session.exec(statement)
    tenants = result.all()
    
    return {
        "items": tenants,
        "meta": {"total": len(tenants), "page": 1}
    }

@router.post("/", response_model=Tenant)
async def create_tenant(
    tenant_data: Tenant, # Pydantic will parse body to Tenant SQLModel
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    require_owner(current_admin)
    
    # Check exists
    stmt = select(Tenant).where(Tenant.name == tenant_data.name)
    existing = (await session.exec(stmt)).first()
    if existing:
        raise AppError(error_code="TENANT_EXISTS", message="Tenant exists", status_code=400)
    
    session.add(tenant_data)
    await session.commit()
    await session.refresh(tenant_data)
    
    return tenant_data

@router.get("/capabilities")
async def get_capabilities(current_admin: AdminUser = Depends(get_current_admin), session: AsyncSession = Depends(get_session)):
    # Re-fetch tenant to get features
    # AdminUser SQLModel has 'tenant' relationship if eager loaded, or we fetch it.
    # But AdminUser defined in sql_models has tenant_id.
    
    tenant = await session.get(Tenant, current_admin.tenant_id)
    features = tenant.features if tenant else {}
    
    return {
        "features": features,
        "is_owner": current_admin.is_platform_owner,
        "tenant_id": current_admin.tenant_id,
        "tenant_role": current_admin.tenant_role,
        "tenant_name": tenant.name if tenant else "Unknown"
    }

# Seeding function adapted for SQL
async def seed_default_tenants(session: AsyncSession):
    # Check if default exists
    stmt = select(Tenant).where(Tenant.id == "default_casino")
    result = await session.exec(stmt)
    if result.first():
        return

    # Create Owner Tenant
    owner = Tenant(
        id="default_casino", 
        name="Default Casino", 
        type="owner",
        features={
            "can_manage_admins": True,
            "can_view_reports": True,
            # ... add others
        }
    )
    
    # Create Demo Renter
    renter = Tenant(
        id="demo_renter",
        name="Demo Renter",
        type="renter",
        features={
            "can_manage_admins": True,
            "can_view_reports": True
        }
    )
    
    session.add(owner)
    session.add(renter)
    await session.commit()
    print("✅ SQL Tenants Seeded")
