from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class ProviderAdapter(ABC):
    """
    Abstract Base Class for Game Providers.
    Any new provider (Pragmatic, Evolution, etc.) must implement this interface.
    """

    @abstractmethod
    def validate_signature(self, request_data: Dict[str, Any], headers: Dict[str, Any]) -> bool:
        """Verify the webhook signature/integrity."""
        pass

    @abstractmethod
    def map_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Provider payload to Canonical GameEngine format.
        Output must include: action, player_id, game_id, round_id, tx_id, amount, currency.
        """
        pass

    @abstractmethod
    def map_response(self, engine_response: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Canonical GameEngine response back to Provider format."""
        pass

    @abstractmethod
    def map_error(self, error_code: str, message: str) -> Dict[str, Any]:
        """Convert internal AppError codes to Provider specific error codes."""
        pass
