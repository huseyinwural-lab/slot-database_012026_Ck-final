from fastapi import APIRouter
# Stub for Fraud
router = APIRouter(prefix="/api/v1/fraud", tags=["fraud"])
@router.get("/")
async def get_fraud(): return []
