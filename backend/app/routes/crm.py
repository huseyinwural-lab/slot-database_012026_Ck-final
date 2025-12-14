from fastapi import APIRouter
from typing import List

router = APIRouter(prefix="/api/v1/crm", tags=["crm"])

# Stub returning array for CRM frontend
@router.get("/")
async def get_crm() -> List[dict]:
    return []
