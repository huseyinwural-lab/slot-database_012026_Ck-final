from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_session
from app.models.sql_models import Bonus, AdminUser
from app.utils.auth import get_current_admin
from app.utils.tenant import get_current_tenant_id
from app.utils.pagination import get_pagination_params
from app.models.common import PaginationMeta, PaginationParams

router = APIRouter(prefix="/api/v1/bonuses", tags=["bonuses"])

@router.get("/", response_model=dict)
async def get_bonuses(
    request: Request,
    pagination: PaginationParams = Depends(get_pagination_params),
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    
    query = select(Bonus).where(Bonus.tenant_id == tenant_id)
    query = query.order_by(Bonus.created_at.desc())
    
    # Count
    from sqlmodel import func
    count_query = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_query)).scalar() or 0
    
    # Paginate
    query = query.offset((pagination.page - 1) * pagination.page_size).limit(pagination.page_size)
    result = await session.execute(query)
    bonuses = result.scalars().all()
    
    return {
        "items": bonuses,
        "meta": PaginationMeta(total=total, page=pagination.page, page_size=pagination.page_size)
    }

@router.post("/", response_model=Bonus)
async def create_bonus(
    request: Request,
    bonus_data: Bonus,
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    
    # Enforce tenant context
    bonus_data.tenant_id = tenant_id
    
    session.add(bonus_data)
    await session.commit()
    await session.refresh(bonus_data)
    return bonus_data

@router.put("/{bonus_id}")
async def update_bonus(
    bonus_id: str,
    request: Request,
    payload: dict = Body(...),
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    
    bonus = await session.get(Bonus, bonus_id)
    if not bonus or bonus.tenant_id != tenant_id:
        raise HTTPException(404, "Bonus not found")
        
    for k, v in payload.items():
        if hasattr(bonus, k):
            setattr(bonus, k, v)
            
    session.add(bonus)
    await session.commit()
    return {"message": "Updated", "bonus": bonus}

@router.delete("/{bonus_id}")
async def delete_bonus(
    bonus_id: str,
    request: Request,
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    
    bonus = await session.get(Bonus, bonus_id)
    if not bonus or bonus.tenant_id != tenant_id:
        raise HTTPException(404, "Bonus not found")
        
    await session.delete(bonus)
    await session.commit()
    return {"message": "Deleted"}
