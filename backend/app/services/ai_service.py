import json
import logging
from typing import Dict, Any
from config import settings

try:
    from emergentintegrations.llm.chat import LlmChat, UserMessage
except Exception:
    LlmChat = None
    UserMessage = None

logger = logging.getLogger(__name__)

class RiskAnalyzer:
    def __init__(self):
        self.api_key = settings.emergent_llm_key
        if not self.api_key:
            logger.warning("EMERGENT_LLM_KEY not found in settings.")
        
        self.model = "gpt-4o"

    async def analyze_transaction(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        if not self.api_key or LlmChat is None or UserMessage is None:
            return {
                "risk_score": 0,
                "risk_level": "unknown",
                "reason": "AI Service not configured",
                "details": {}
            }

        prompt = self._construct_prompt(transaction)
        
        try:
            # Initialize Chat
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"tx_{transaction.get('id', 'unknown')}",
                system_message="You are a risk analysis expert for an online casino. Analyze the transaction for fraud, money laundering, and risk. Respond in JSON. Important: The 'reason' field and 'recommendation' should be in Turkish language."
            )
            
            # Configure Model and JSON mode
            chat.with_model("openai", self.model)
            chat.with_params(response_format={"type": "json_object"})
            
            # Send Message
            user_msg = UserMessage(text=prompt)
            response_text = await chat.send_message(user_msg)
            
            # Parse Result
            result = json.loads(response_text)
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
            "reason": "<short summary in Turkish>",
            "flags": ["<flag1>", "<flag2>"],
            "recommendation": "<approve|reject|review>"
        }}
        """

risk_analyzer = RiskAnalyzer()
