from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Dict, Any, List
import random
from app.models.sql_models import AdminUser
from app.utils.auth import get_current_admin

router = APIRouter(prefix="/api/v1/fraud", tags=["fraud"])

@router.get("/")
async def get_fraud_config(current_admin: AdminUser = Depends(get_current_admin)):
    return []

@router.post("/analyze")
async def analyze_transaction(
    payload: Dict[str, Any] = Body(...),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """
    Mock AI Fraud Analysis.
    Returns a deterministic response based on amount or random.
    """
    txn = payload.get("transaction", {})
    amount = float(txn.get("amount", 0))
    
    is_fraud = amount > 9000 # Mock threshold
    score = 0.95 if is_fraud else 0.12
    
    return {
        "is_fraudulent": is_fraud,
        "fraud_risk_score": score,
        "risk_factors": ["High Amount", "New IP"] if is_fraud else ["Normal Pattern"],
        "confidence_level": 0.85,
        "recommendations": "Block Transaction" if is_fraud else "Approve"
    }
