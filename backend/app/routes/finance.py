from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.sql_models import Transaction
from app.models.common import PaginatedResponse

router = APIRouter(prefix="/api/v1/finance", tags=["finance"])

@router.get("/chargebacks", response_model=List[dict])
async def get_chargebacks():
    return []

@router.get("/reconciliation", response_model=List[dict])
async def get_reconciliations():
    return []
