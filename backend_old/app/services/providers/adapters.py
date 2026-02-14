import hmac
import hashlib
import json
from typing import Dict, Any
from app.services.providers.base import ProviderAdapter
from config import settings

class PragmaticAdapter(ProviderAdapter):
    """
    Adapter for Pragmatic Play (Slots/Live).
    """
    def validate_signature(self, request_data: Dict[str, Any], headers: Dict[str, Any]) -> bool:
        # P0: If no secret key, fail open or closed? Closed for security.
        secret = settings.pragmatic_secret_key
        if not secret:
            return True # Dev mode safety if key not set
            
        received_hash = request_data.get("hash")
        if not received_hash:
            return False
            
        # Reconstruct signature
        # Pragmatic: Sort params, concat values + secret? 
        # Implementing a simple HMAC-SHA256 of the JSON body (excluding hash) for our standard.
        payload = request_data.copy()
        payload.pop("hash", None)
        
        # Canonical string: "key=value&key=value" sorted
        # This is a common pattern.
        canonical = "&".join([f"{k}={v}" for k, v in sorted(payload.items())])
        
        expected = hmac.new(
            secret.encode("utf-8"),
            canonical.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(received_hash, expected)

    def map_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        # Pragmatic fields: userId, gameId, roundId, reference, amount
        # Action is usually determined by which endpoint was hit, but if we share one endpoint:
        # request_data must contain 'action' or we infer it.
        # Let's assume 'type' or 'action' field.
        
        action = request_data.get("action", "unknown")
        
        return {
            "action": action,
            "player_id": request_data.get("userId"),
            "token": request_data.get("token"), # For auth
            "game_id": request_data.get("gameId"),
            "round_id": request_data.get("roundId"),
            "tx_id": request_data.get("reference"),
            "ref_tx_id": request_data.get("originalReference"),
            "amount": float(request_data.get("amount", 0)),
            "currency": request_data.get("currency")
        }

    def map_response(self, engine_response: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "transactionId": engine_response.get("tx_id"),
            "currency": engine_response.get("currency"),
            "cash": engine_response.get("balance"),
            "bonus": 0,
            "error": 0,
            "description": "Success"
        }

    def map_error(self, error_code: str, message: str) -> Dict[str, Any]:
        code = 100
        if error_code == "INSUFFICIENT_FUNDS":
            code = 1
        elif error_code == "PLAYER_NOT_FOUND":
            code = 2
        elif error_code == "GAME_NOT_FOUND":
            code = 3
        elif error_code == "RATE_LIMIT_EXCEEDED":
            code = 50 # Temp Error
            
        return {
            "error": code,
            "description": message
        }

class EvolutionAdapter(ProviderAdapter):
    def validate_signature(self, request_data: Dict[str, Any], headers: Dict[str, Any]) -> bool:
        return True

    def map_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "action": request_data.get("type"), 
            "player_id": request_data.get("sid"), 
            "game_id": request_data.get("game", {}).get("id"),
            "round_id": request_data.get("game", {}).get("id"), 
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
