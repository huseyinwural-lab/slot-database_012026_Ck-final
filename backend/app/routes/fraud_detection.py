from fastapi import APIRouter, HTTPException, status, Depends
from app.models.fraud import FraudAnalysisRequest, FraudAnalysisResponse
from app.models.domain.admin import AdminUser
from app.utils.auth import get_current_admin
from app.utils.permissions import require_owner
from app.services.openai_service import fraud_detection_service
import logging

router = APIRouter(prefix="/api/v1/fraud", tags=["fraud_detection"])
logger = logging.getLogger(__name__)

@router.post("/analyze", response_model=FraudAnalysisResponse)
async def analyze_transaction(
    request: FraudAnalysisRequest,
    current_admin: AdminUser = Depends(get_current_admin)
):
    # Owner-only endpoint
    require_owner(current_admin)
    try:
        result = fraud_detection_service.analyze_transaction(
            transaction=request.transaction,
            historical_data=request.historical_data
        )
        return result
    except Exception as e:
        logger.error(f"Error in fraud analysis endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
