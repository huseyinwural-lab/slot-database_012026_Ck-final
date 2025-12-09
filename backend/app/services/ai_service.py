import os
import json
import logging
from typing import Dict, Any
from openai import OpenAI, RateLimitError, APIError

logger = logging.getLogger(__name__)

class RiskAnalyzer:
    def __init__(self):
        # EMERGENT_LLM_KEY is used as the API key for OpenAI
        api_key = os.environ.get("EMERGENT_LLM_KEY")
        if not api_key:
            logger.warning("EMERGENT_LLM_KEY not found. AI features will be disabled.")
            self.client = None
        else:
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://api.emergent.sh/v1/openai" # Using Emergent Proxy
            )
        self.model = "gpt-5" # As per user request/playbook

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
            # Fallback
            return {
                "risk_score": 50,
                "risk_level": "medium", 
                "reason": "AI Analysis Failed. Manual Review Recommended.",
                "error": str(e)
            }

    def _construct_prompt(self, tx: Dict[str, Any]) -> str:
        return f"""
        Analyze this transaction for risk.
        
        Transaction Details:
        - ID: {tx.get('id')}
        - Player: {tx.get('player_username')} (ID: {tx.get('player_id')})
        - Amount: {tx.get('amount')} {tx.get('currency')}
        - Type: {tx.get('type')}
        - Method: {tx.get('method')}
        - IP: {tx.get('ip_address')}
        - Country: {tx.get('country')}
        - Device: {tx.get('device_info')}
        - Status: {tx.get('status')}
        - Balance Before: {tx.get('balance_before')}
        - Balance After: {tx.get('balance_after')}
        
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
