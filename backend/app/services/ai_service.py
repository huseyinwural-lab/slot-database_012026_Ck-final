import os
import json
import logging
from typing import Dict, Any
from openai import OpenAI, RateLimitError, APIError
from config import settings

logger = logging.getLogger(__name__)

class RiskAnalyzer:
    def __init__(self):
        # Use settings to get the key from .env via Pydantic
        api_key = settings.emergent_llm_key
        if not api_key:
            logger.warning("EMERGENT_LLM_KEY not found in settings. AI features will be disabled.")
            self.client = None
        else:
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://api.emergent.sh/v1/openai" # Using Emergent Proxy
            )
        self.model = "gpt-5"

    async def analyze_transaction(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        if not self.client:
            return {
                "risk_score": 0,
                "risk_level": "unknown",
                "reason": "AI Service not configured (Missing Key)",
                "details": {}
            }

        prompt = self._construct_prompt(transaction)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a risk analysis expert for an online casino. Analyze the transaction for fraud, money laundering, and risk."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            return result

        except Exception as e:
            logger.error(f"AI Analysis Failed: {str(e)}")
            return {
                "risk_score": 50,
                "risk_level": "medium", 
                "reason": f"AI Analysis Failed: {str(e)}",
                "error": str(e)
            }

    def _construct_prompt(self, tx: Dict[str, Any]) -> str:
        # Helper to safely get values
        def safe_get(key):
            return tx.get(key, 'N/A')

        return f"""
        Analyze this transaction for risk.
        
        Transaction Details:
        - ID: {safe_get('id')}
        - Player: {safe_get('player_username')} (ID: {safe_get('player_id')})
        - Amount: {safe_get('amount')} {safe_get('currency')}
        - Type: {safe_get('type')}
        - Method: {safe_get('method')}
        - IP: {safe_get('ip_address')}
        - Country: {safe_get('country')}
        - Device: {safe_get('device_info')}
        - Status: {safe_get('status')}
        - Balance Before: {safe_get('balance_before')}
        - Balance After: {safe_get('balance_after')}
        
        Provide output in JSON format:
        {{
            "risk_score": <int 0-100>,
            "risk_level": "<low|medium|high|critical>",
            "reason": "<short summary>",
            "flags": ["<flag1>", "<flag2>"],
            "recommendation": "<approve|reject|review>"
        }}
        """

risk_analyzer = RiskAnalyzer()
