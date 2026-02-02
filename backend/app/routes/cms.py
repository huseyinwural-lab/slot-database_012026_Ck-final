from fastapi import APIRouter, Depends, Body, Request
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.sql_models import ContentPage, AdminUser
from app.utils.auth import get_current_admin
from app.utils.tenant import get_current_tenant_id

router = APIRouter(prefix="/api/v1/cms", tags=["cms"])

@router.get("/pages")
async def get_pages(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    query = select(ContentPage).where(ContentPage.tenant_id == tenant_id)
    result = await session.execute(query)
    # Direct list return
    return result.scalars().all()

@router.post("/pages")
async def create_page(
    request: Request,
    page: dict = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    new_page = ContentPage(
        tenant_id=tenant_id,
        slug=page["slug"],
        title=page["title"],
        content=page["content"]
    )
    session.add(new_page)
    await session.commit()
    return new_page
