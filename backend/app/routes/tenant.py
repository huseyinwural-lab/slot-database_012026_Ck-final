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
    result = await session.execute(statement) # Changed exec to execute for AsyncSession
    tenants = result.scalars().all()
    
    return {
        "items": tenants,
        "meta": {"total": len(tenants), "page": 1}
    }

@router.post("/", response_model=Tenant)
async def create_tenant(
    tenant_data: Tenant, 
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    require_owner(current_admin)
    
    # Check exists
    stmt = select(Tenant).where(Tenant.name == tenant_data.name)
    result = await session.execute(stmt)
    existing = result.scalars().first()
    if existing:
        raise AppError(error_code="TENANT_EXISTS", message="Tenant exists", status_code=400)
    
    session.add(tenant_data)
    await session.commit()
    await session.refresh(tenant_data)
    
    return tenant_data

@router.get("/capabilities")
async def get_capabilities(current_admin: AdminUser = Depends(get_current_admin), session: AsyncSession = Depends(get_session)):
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
    result = await session.execute(stmt)
    if result.scalars().first():
        return

    # Create Owner Tenant
    owner = Tenant(
        id="default_casino", 
        name="Default Casino", 
        type="owner",
        features={
            "can_manage_admins": True,
            "can_view_reports": True,
            "can_manage_experiments": True,
            "can_use_kill_switch": True,
        }
    )
    
    # Create Demo Renter
    renter = Tenant(
        id="demo_renter",
        name="Demo Renter",
        type="renter",
        features={
            "can_manage_admins": True,
            "can_view_reports": True,
            "can_manage_affiliates": False,
            "can_use_crm": False,
            "can_manage_experiments": False,
            "can_use_kill_switch": False,
        }
    )
    
    session.add(owner)
    session.add(renter)
    await session.commit()
    print("✅ SQL Tenants Seeded")
