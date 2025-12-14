from fastapi import APIRouter, Depends
from sqlmodel import select, SQLModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict
from sqlalchemy import Column, JSON
import uuid

from app.core.database import get_session
from app.utils.auth import get_current_admin, AdminUser

router = APIRouter(prefix="/api/v1/features", tags=["features"])

class FeatureFlag(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    key: str
    description: str
    is_enabled: bool = False
    created_at: str = ""

@router.get("/", response_model=List[FeatureFlag])
async def get_feature_flags(
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    # If table doesn't exist yet in seed, return empty list instead of 500
    try:
        query = select(FeatureFlag)
        result = await session.execute(query)
        return result.scalars().all()
    except:
        return []
