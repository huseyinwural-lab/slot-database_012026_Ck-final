from fastapi import APIRouter
# Stub for Reports
router = APIRouter(prefix="/api/v1/reports", tags=["reports"])
@router.get("/")
async def get_reports(): return []
