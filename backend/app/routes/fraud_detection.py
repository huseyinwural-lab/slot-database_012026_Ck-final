from fastapi import APIRouter, HTTPException, status
from app.models.fraud import FraudAnalysisRequest, FraudAnalysisResponse
from app.services.openai_service import fraud_detection_service
import logging

router = APIRouter(prefix="/api/v1/fraud", tags=["fraud_detection"])
logger = logging.getLogger(__name__)

@router.post("/analyze", response_model=FraudAnalysisResponse)
async def analyze_transaction(request: FraudAnalysisRequest):
    try:
        result = fraud_detection_service.analyze_transaction(
            transaction=request.transaction,
            historical_data=request.historical_data
        )
        return result
    except Exception as e:
        logger.error(f"Error in fraud analysis endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
