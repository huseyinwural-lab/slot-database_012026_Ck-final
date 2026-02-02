from typing import List, Optional
from app.services.payments.providers.base import PaymentProvider, MockProvider

class PaymentRouter:
    def __init__(self):
        # In real world, load from DB/Config
        self.providers = {
            "stripe_mock": MockProvider("stripe_mock", success_rate=0.9),
            "adyen_mock": MockProvider("adyen_mock", success_rate=0.8),
            "fail_mock": MockProvider("fail_mock", success_rate=0.0, fail_code="TIMEOUT")
        }
        
    def get_route(self, tenant_id: str, currency: str, amount: float, risk_score: str = 'low') -> List[str]:
        """Returns ordered list of provider IDs to try."""
        
        # Simple Logic v1
        # High Risk -> Specific Provider or Block
        if risk_score == 'high':
            return ["adyen_mock"] # Assume stronger 3DS
            
        # Default: Priority Order
        return ["stripe_mock", "adyen_mock"]

    def get_provider(self, provider_id: str) -> Optional[PaymentProvider]:
        return self.providers.get(provider_id)
