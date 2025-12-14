from fastapi import APIRouter, Depends
from sqlmodel import select, SQLModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
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
    # Try/Except block to handle table missing error gracefully if migration hasn't run
    try:
        query = select(FeatureFlag)
        result = await session.execute(query)
        return result.scalars().all()
    except Exception as e:
        print(f"Feature Flag Error: {e}")
        return []
