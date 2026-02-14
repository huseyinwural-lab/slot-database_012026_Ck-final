from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class TransactionData(BaseModel):
    transaction_id: str = Field(..., description="Unique transaction identifier")
    amount: float = Field(..., gt=0, description="Transaction amount")
    merchant_name: str = Field(..., description="Name of the merchant/provider")
    customer_email: str = Field(..., description="Customer email address")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = Field(None, description="Customer IP address")
    
class FraudAnalysisRequest(BaseModel):
    transaction: TransactionData
    historical_data: Optional[Dict[str, Any]] = Field(None, description="Previous transaction history")

class FraudAnalysisResponse(BaseModel):
    transaction_id: str
    fraud_risk_score: float = Field(..., ge=0, le=1, description="Risk score from 0 to 1")
    is_fraudulent: bool = Field(..., description="Fraud determination")
    confidence_level: float = Field(..., ge=0, le=1, description="Confidence in the assessment")
    risk_factors: List[str] = Field(default_factory=list, description="List of identified risk factors")
    recommendations: str = Field(..., description="Recommended action")
    analysis_details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class EmailNotificationRequest(BaseModel):
    recipient_email: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject line")
    body_html: str = Field(..., description="HTML email body")
    body_text: Optional[str] = Field(None, description="Plain text email body")

class EmailNotificationResponse(BaseModel):
    email_id: str = Field(..., description="SendGrid email ID")
    recipient: str
    status: str = Field(..., description="sent, failed, pending")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None
