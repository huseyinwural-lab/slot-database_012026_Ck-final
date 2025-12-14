from fastapi import APIRouter, Depends, Body
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_session
from app.models.sql_models import ContentPage, AdminUser
from app.utils.auth import get_current_admin

router = APIRouter(prefix="/api/v1/cms", tags=["cms"])

@router.get("/pages")
async def get_pages(
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    query = select(ContentPage).where(ContentPage.tenant_id == current_admin.tenant_id)
    result = await session.execute(query)
    return result.scalars().all()

@router.post("/pages")
async def create_page(
    page: dict = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    new_page = ContentPage(
        tenant_id=current_admin.tenant_id,
        slug=page["slug"],
        title=page["title"],
        content=page["content"]
    )
    session.add(new_page)
    await session.commit()
    return new_page
