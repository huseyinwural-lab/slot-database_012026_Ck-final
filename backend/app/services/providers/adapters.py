from typing import Dict, Any
from app.services.providers.base import ProviderAdapter

class PragmaticAdapter(ProviderAdapter):
    """
    Adapter for Pragmatic Play (Slots/Live).
    """
    def validate_signature(self, request_data: Dict[str, Any], headers: Dict[str, Any]) -> bool:
        # Pragmatic typically uses a 'hash' body parameter or header.
        # Implementation depends on specific documentation.
        return True # Placeholder

    def map_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        # Pragmatic fields: userId, gameId, roundId, reference, amount
        return {
            "action": "bet", # inferred from endpoint
            "player_id": request_data.get("userId"),
            "game_id": request_data.get("gameId"),
            "round_id": request_data.get("roundId"),
            "tx_id": request_data.get("reference"),
            "amount": float(request_data.get("amount", 0)),
            "currency": request_data.get("currency")
        }

    def map_response(self, engine_response: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "transactionId": engine_response.get("tx_id"),
            "currency": engine_response.get("currency"),
            "cash": engine_response.get("balance"),
            "bonus": 0, # P0
            "error": 0,
            "description": "Success"
        }

    def map_error(self, error_code: str, message: str) -> Dict[str, Any]:
        # Pragmatic Error Codes: 1 (Insufficient Funds), 100 (Internal), etc.
        code = 100
        if error_code == "INSUFFICIENT_FUNDS":
            code = 1
        elif error_code == "PLAYER_NOT_FOUND":
            code = 2
            
        return {
            "error": code,
            "description": message
        }

class EvolutionAdapter(ProviderAdapter):
    """
    Adapter for Evolution Gaming (Live Casino).
    """
    def validate_signature(self, request_data: Dict[str, Any], headers: Dict[str, Any]) -> bool:
        # Evolution uses authToken validation usually.
        return True

    def map_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "action": request_data.get("type"), # debit/credit
            "player_id": request_data.get("sid"), # session id usually maps to player
            "game_id": request_data.get("game", {}).get("id"),
            "round_id": request_data.get("game", {}).get("id"), # Evo rounds are complex
            "tx_id": request_data.get("transactionId"),
            "amount": float(request_data.get("amount", 0)),
            "currency": request_data.get("currency")
        }

    def map_response(self, engine_response: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "OK",
            "balance": engine_response.get("balance"),
            "uuid": engine_response.get("tx_id")
        }

    def map_error(self, error_code: str, message: str) -> Dict[str, Any]:
        return {
            "status": "ERROR",
            "errorType": error_code,
            "msg": message
        }
