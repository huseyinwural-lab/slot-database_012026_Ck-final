from fastapi import APIRouter
# Stub for RG
router = APIRouter(prefix="/api/v1/rg", tags=["rg"])
@router.get("/")
async def get_rg(): return []
