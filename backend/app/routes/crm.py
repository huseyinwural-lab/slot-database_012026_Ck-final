from fastapi import APIRouter
# Stub for CRM
router = APIRouter(prefix="/api/v1/crm", tags=["crm"])
@router.get("/")
async def get_crm(): return []
