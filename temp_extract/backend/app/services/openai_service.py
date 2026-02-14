import json
from openai import OpenAI
from config import settings
from app.models.fraud import FraudAnalysisResponse, TransactionData
import logging

logger = logging.getLogger(__name__)

class OpenAIFraudDetectionService:
    def __init__(self):
        # Only initialize if key is present
        self.client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        self.model = settings.openai_model
    
    def analyze_transaction(self, transaction: TransactionData, historical_data: dict = None) -> FraudAnalysisResponse:
        if not self.client:
             # Mock response if no API key
            return FraudAnalysisResponse(
                transaction_id=transaction.transaction_id,
                fraud_risk_score=0.1,
                is_fraudulent=False,
                confidence_level=0.9,
                risk_factors=["Mock Mode: No API Key"],
                recommendations="System is in mock mode. Please configure OpenAI API Key.",
                analysis_details={}
            )

        system_prompt = """You are an expert fraud detection analyst for a Casino. Analyze the provided transaction data 
        and determine the fraud risk. Provide your analysis in the following JSON structure:
        {
            "fraud_risk_score": <float 0-1>,
            "is_fraudulent": <boolean>,
            "confidence_level": <float 0-1>,
            "risk_factors": [<list of identified risk factors>],
            "recommendations": "<string with recommended action>"
        }"""
        
        user_prompt = f"""
        Analyze this transaction for fraud:
        Transaction Details:
        - Amount: ${transaction.amount}
        - Merchant: {transaction.merchant_name}
        - Customer Email: {transaction.customer_email}
        - Timestamp: {transaction.timestamp}
        - IP Address: {transaction.ip_address}
        
        Historical Context: {historical_data if historical_data else "No history"}
        
        Provide your fraud risk assessment as valid JSON only.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            response_text = response.choices[0].message.content
            # Clean up potential markdown code blocks
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "")
            
            analysis_data = json.loads(response_text)
            
            return FraudAnalysisResponse(
                transaction_id=transaction.transaction_id,
                fraud_risk_score=float(analysis_data.get("fraud_risk_score", 0.5)),
                is_fraudulent=bool(analysis_data.get("is_fraudulent", False)),
                confidence_level=float(analysis_data.get("confidence_level", 0.8)),
                risk_factors=analysis_data.get("risk_factors", []),
                recommendations=analysis_data.get("recommendations", "Manual review recommended"),
                analysis_details=analysis_data
            )
            
        except Exception as e:
            logger.error(f"OpenAI Analysis failed: {str(e)}")
            # Fallback safe response
            return FraudAnalysisResponse(
                transaction_id=transaction.transaction_id,
                fraud_risk_score=0.5,
                is_fraudulent=True,
                confidence_level=0.0,
                risk_factors=["Analysis Failed"],
                recommendations=f"Manual Review Required. Error: {str(e)}",
                analysis_details={}
            )

fraud_detection_service = OpenAIFraudDetectionService()
