from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
from pydantic import BaseModel

class ProviderResponse(BaseModel):
    provider_txn_id: str
    status: str # SUCCESS, PENDING, FAILED, DECLINED
    raw_code: Optional[str] = None
    raw_message: Optional[str] = None
    retryable: bool = False
    risk_flags: Dict[str, Any] = {}

class PaymentProvider(ABC):
    @abstractmethod
    async def authorize(self, amount: float, currency: str, player_id: str, metadata: Dict) -> ProviderResponse:
        pass

    @abstractmethod
    async def capture(self, txn_id: str, amount: float) -> ProviderResponse:
        pass

    @abstractmethod
    async def refund(self, txn_id: str, amount: Optional[float] = None) -> ProviderResponse:
        pass
    
    @abstractmethod
    async def payout(self, amount: float, currency: str, player_id: str, destination: Dict) -> ProviderResponse:
        pass

# --- MOCK IMPLEMENTATION ---
class MockProvider(PaymentProvider):
    def __init__(self, name: str, success_rate: float = 1.0, fail_code: str = None):
        self.name = name
        self.success_rate = success_rate
        self.fail_code = fail_code

    async def authorize(self, amount: float, currency: str, player_id: str, metadata: Dict) -> ProviderResponse:
        import random
        import uuid
        
        # Simulate failure
        if random.random() > self.success_rate:
            is_retryable = self.fail_code in ["TIMEOUT", "NETWORK_ERROR"]
            return ProviderResponse(
                provider_txn_id=f"fail_{uuid.uuid4()}",
                status="FAILED" if is_retryable else "DECLINED",
                raw_code=self.fail_code or "GENERIC_DECLINE",
                retryable=is_retryable
            )
            
        return ProviderResponse(
            provider_txn_id=f"{self.name}_{uuid.uuid4()}",
            status="SUCCESS"
        )

    async def capture(self, txn_id: str, amount: float) -> ProviderResponse:
        return ProviderResponse(provider_txn_id=txn_id, status="SUCCESS")

    async def refund(self, txn_id: str, amount: Optional[float] = None) -> ProviderResponse:
        return ProviderResponse(provider_txn_id=f"ref_{txn_id}", status="SUCCESS")

    async def payout(self, amount: float, currency: str, player_id: str, destination: Dict) -> ProviderResponse:
        return ProviderResponse(provider_txn_id=f"payout_{player_id}", status="SUCCESS")
