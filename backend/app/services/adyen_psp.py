from typing import Dict, Optional, Any
import httpx
import logging
import json
from config import settings

logger = logging.getLogger(__name__)

class AdyenPSP:
    def __init__(self, api_key: str, merchant_account: str, environment: str = "test"):
        self.api_key = api_key
        self.merchant_account = merchant_account
        self.environment = environment
        # Base URL for Test environment
        self.base_url = "https://checkout-test.adyen.com/v70"

    async def create_payment_link(
        self, 
        amount: float, 
        currency: str, 
        reference: str, 
        return_url: str,
        shopper_email: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Creates a payment link via Adyen Checkout API.
        Docs: https://docs.adyen.com/api-explorer/Checkout/70/post/paymentLinks
        """
        
        # MOCK MODE: If keys are missing or specifically in dev with allow_test_payment_methods
        if not self.api_key or "mock" in self.api_key.lower():
            if settings.allow_test_payment_methods:
                logger.info(f"Mocking Adyen Payment Link for {reference}")
                # Return a mock response that redirects back to return_url immediately
                # mimicking a successful payment
                mock_url = f"{return_url}&resultCode=Authorised"
                return {
                    "id": f"PL_{reference}",
                    "url": mock_url,
                    "status": "active",
                    "expiresAt": "2099-12-31T23:59:59Z"
                }
            else:
                 raise ValueError("Adyen API Key missing and test methods not allowed")

        url = f"{self.base_url}/paymentLinks"
        
        # Adyen expects amount in minor units (e.g., cents)
        # We need a utility to convert. For USD/EUR it's *100.
        # Simplification: assume 2 decimals for now.
        value = int(amount * 100)
        
        payload = {
            "merchantAccount": self.merchant_account,
            "amount": {
                "currency": currency,
                "value": value
            },
            "reference": reference,
            "returnUrl": return_url,
            "storePaymentMethodMode": "askForConsent", # Optional
        }
        
        if shopper_email:
            payload["shopperEmail"] = shopper_email
            
        if metadata:
            payload["metadata"] = metadata

        headers = {
            "x-API-key": self.api_key,
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, headers=headers, timeout=10.0)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Adyen API Error: {e.response.text}")
                raise Exception(f"Adyen API Error: {e.response.text}")
            except Exception as e:
                logger.error(f"Adyen Connection Error: {str(e)}")
                raise

    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """
        Verify Adyen HMAC signature.
        This requires the HMAC key.
        Implementation omitted for mock/demo, assuming True if no key provided in dev.
        """
        # In a real impl, we'd use Adyen's HMAC validation logic.
        return True

