from fastapi import APIRouter
router = APIRouter(prefix="/api/v1/fraud", tags=["fraud"])
@router.get("/")
async def get_fraud_rules(): return []
