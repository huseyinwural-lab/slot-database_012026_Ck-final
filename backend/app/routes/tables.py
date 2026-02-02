from __future__ import annotations

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel, Field, select

from app.core.database import get_session
from app.utils.auth import get_current_admin
from app.models.sql_models import AdminUser
from app.utils.tenant import get_current_tenant_id

router = APIRouter(prefix="/api/v1/tables", tags=["tables"])

# Trailing slash redirect (FastAPI 307) frontend'de toast'a sebep olmasın diye
router.redirect_slashes = False


class TableGame(SQLModel, table=False):
    """Frontend 'tables' ihtiyacı için minimal model.

    Not: Bu sistemde gerçek masa oyunları henüz normalize edilmemiş olabilir.
    Şimdilik UI'nın kırılmaması için list + create sağlayan basit yapı.
    """

    id: str
    name: str
    provider: str
    min_bet: float
    max_bet: float


class TableGameDB(SQLModel, table=True):
    __tablename__ = "table_game"

    id: str = Field(primary_key=True)
    tenant_id: str = Field(index=True)
    name: str
    provider: str
    min_bet: float = 1.0
    max_bet: float = 100.0
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())


@router.get("", response_model=List[TableGameDB])
async def list_tables(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    stmt = select(TableGameDB).where(TableGameDB.tenant_id == tenant_id)
    res = await session.execute(stmt)
    return res.scalars().all()


@router.post("", response_model=TableGameDB)
async def create_table(
    request: Request,
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    import uuid

    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    table = TableGameDB(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        name=(payload.get("name") or "New Table").strip(),
        provider=(payload.get("provider") or "Unknown").strip(),
        min_bet=float(payload.get("min_bet") or 1),
        max_bet=float(payload.get("max_bet") or 100),
    )

    session.add(table)
    await session.commit()
    await session.refresh(table)
    return table
