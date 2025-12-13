from typing import List
from fastapi import APIRouter, Depends, Body
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.sql_models import AdminUser
from app.utils.auth import get_current_admin, get_password_hash, create_access_token
from app.core.errors import AppError
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

@router.get("/users")
async def get_admins(
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    query = select(AdminUser)
    if not current_admin.is_platform_owner:
        query = query.where(AdminUser.tenant_id == current_admin.tenant_id)
        
    result = await session.exec(query)
    return result.all()

@router.post("/users")
async def create_admin(
    payload: dict = Body(...), # Using dict for flexibility in refactor
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    # Basic validation
    email = payload.get("email")
    password = payload.get("password")
    
    # Check existence
    existing = (await session.exec(select(AdminUser).where(AdminUser.email == email))).first()
    if existing:
        raise AppError("USER_EXISTS", "User already exists", 400)
    
    # Create
    new_admin = AdminUser(
        email=email,
        username=email.split("@")[0],
        full_name=payload.get("full_name", "Admin"),
        role=payload.get("role", "Admin"),
        tenant_role=payload.get("tenant_role", "tenant_admin"),
        tenant_id=payload.get("tenant_id") or current_admin.tenant_id, # Default to creator's tenant
        password_hash=get_password_hash(password) if password else "",
        status="active"
    )
    
    if payload.get("password_mode") == "invite":
        new_admin.status = "invited"
        # Logic for invite token...
        token = create_access_token({"sub": "invite", "email": email}, timedelta(days=7))
        new_admin.invite_token = token
    
    session.add(new_admin)
    await session.commit()
    await session.refresh(new_admin)
    
    return {"user": new_admin, "invite_token": new_admin.invite_token}

@router.post("/seed")
async def seed_admin(session: AsyncSession = Depends(get_session)):
    # 1. Ensure Tenant Exists
    from app.routes.tenant import seed_default_tenants
    await seed_default_tenants(session)
    
    # 2. Check Admin
    stmt = select(AdminUser).where(AdminUser.email == "admin@casino.com")
    existing = (await session.exec(stmt)).first()
    
    if not existing:
        super_admin = AdminUser(
            email="admin@casino.com",
            username="superadmin",
            full_name="Super Owner",
            role="Super Admin",
            tenant_id="default_casino",
            is_platform_owner=True,
            password_hash=get_password_hash("Admin123!"),
            status="active"
        )
        session.add(super_admin)
        await session.commit()
        return {"message": "Super Admin Seeded"}
    
    return {"message": "Already seeded"}
