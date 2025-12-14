from fastapi import APIRouter, Depends
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_session
from app.models.sql_models import FeatureFlag
from app.utils.auth import get_current_admin, AdminUser

router = APIRouter(prefix="/api/v1/features", tags=["features"])

@router.get("/", response_model=List[FeatureFlag])
async def get_feature_flags(
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    try:
        query = select(FeatureFlag)
        result = await session.execute(query)
        # Frontend FeatureFlags.jsx likely expects array
        return result.scalars().all()
    except Exception as e:
        print(f"Feature Flag Error: {e}")
        return []
