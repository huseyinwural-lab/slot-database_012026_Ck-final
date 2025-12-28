import hmac
import hashlib
import base64
import logging
from typing import Dict, Optional, Any
import httpx
from config import settings

logger = logging.getLogger(__name__)

class AdyenPSP:
    def __init__(self, api_key: str, merchant_account: str, environment: str = "test"):
        self.api_key = api_key
        self.merchant_account = merchant_account
        self.environment = environment
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
        """
        
        # MOCK MODE: If keys are missing or specifically in dev with allow_test_payment_methods
        # In PROD, allow_test_payment_methods should be False, so this block is skipped if API key exists.
        if (not self.api_key or "mock" in self.api_key.lower()) and settings.allow_test_payment_methods:
             logger.info(f"Mocking Adyen Payment Link for {reference}")
             mock_url = f"{return_url}&resultCode=Authorised"
             return {
                 "id": f"PL_{reference}",
                 "url": mock_url,
                 "status": "active",
                 "expiresAt": "2099-12-31T23:59:59Z"
             }
        
        if not self.api_key:
             raise ValueError("Adyen API Key missing")

        url = f"{self.base_url}/paymentLinks"
        value = int(amount * 100) # Minor units
        
        payload = {
            "merchantAccount": self.merchant_account,
            "amount": {"currency": currency, "value": value},
            "reference": reference,
            "returnUrl": return_url,
            "storePaymentMethodMode": "askForConsent",
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
    async def submit_payout(
        self,
        amount: float,
        currency: str,
        reference: str,
        shopper_reference: Optional[str] = None,
        shopper_email: Optional[str] = None,
        bank_account: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Submits a payout via Adyen Payout API (Third Party).
        """
        # Mock Mode for Dev/Test
        if (not self.api_key or "mock" in self.api_key.lower()) and settings.allow_test_payment_methods:
             logger.info(f"Mocking Adyen Payout for {reference}")
             return {
                 "pspReference": f"MOCK_PAYOUT_{reference}",
                 "resultCode": "[payout-submit-received]",
                 "merchantReference": reference
             }

        if not self.api_key:
             raise ValueError("Adyen API Key missing")
        
        url = f"{self.base_url}/pal/servlet/Payment/v68/submitThirdParty"
        # Note: Adyen Live Payout URL is different, handling via base_url logic or config is best.
        # Here we assume base_url is set correctly for Payouts or we override it.
        # Adyen Payouts often use a different endpoint prefix than Checkout.
        # For MVP we assume standard structure or Update base_url dynamically if needed.
        # Actually, Payouts API has specific endpoints. Let's use the one from playbook.
        if "checkout" in self.base_url:
             # switch to pal-test or pal-live
             if "test" in self.environment:
                 url = "https://pal-test.adyen.com/pal/servlet/Payment/v68/submitThirdParty"
             else:
                 # TODO: Add live prefix config
                 url = "https://pal-live.adyenpayments.com/pal/servlet/Payment/v68/submitThirdParty"

        value = int(amount * 100)
        
        payload = {
            "merchantAccount": self.merchant_account,
            "amount": {"currency": currency, "value": value},
            "reference": reference,
            "shopperEmail": shopper_email,
            "shopperReference": shopper_reference,
            "selectedRecurringDetailReference": "LATEST", # Use latest saved detail if available
            "recurring": {"contract": "PAYOUT"},
        }
        
        # If explicit bank account provided (rare for just 'retry', but possible)
        if bank_account:
            payload["bankAccount"] = bank_account
            
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
                logger.error(f"Adyen Payout API Error: {e.response.text}")
                raise Exception(f"Adyen Payout API Error: {e.response.text}")
            except Exception as e:
                logger.error(f"Adyen Payout Connection Error: {str(e)}")
                raise

    def verify_webhook_signature(self, payload: Dict, signature: str = "") -> bool:
        """Verify Adyen webhook HMAC signature (standard notification webhooks).

        Adyen provides the expected signature as:
        - payload.notificationItems[i].NotificationRequestItem.additionalData.hmacSignature

        Signing string (values only, colon-delimited):
        pspReference:originalReference:merchantAccountCode:merchantReference:value:currency:eventCode:success

        HMAC key:
        - Typically provided by Adyen as Base64 (preferred)
        - Some setups may provide hex; we accept both.
        """

        if not settings.adyen_hmac_key:
            if settings.env in {"prod", "production", "staging"}:
                logger.error("Adyen HMAC key missing in prod/staging")
                return False
            # Dev fallback (allows local mock / CI simulation)
            return True

        def _escape(v: object) -> str:
            s = "" if v is None else str(v)
            # Escape backslashes first, then colons
            s = s.replace("\\", "\\\\")
            s = s.replace(":", "\\:")
            return s

        def _decode_hmac_key(raw: str) -> bytes:
            raw = (raw or "").strip()
            if not raw:
                return b""
            # Adyen docs: key is base64. Accept hex as fallback.
            try:
                return base64.b64decode(raw, validate=True)
            except Exception:
                try:
                    return bytes.fromhex(raw)
                except Exception:
                    return raw.encode("utf-8")

        key_bytes = _decode_hmac_key(settings.adyen_hmac_key)
        if not key_bytes:
            logger.error("Adyen HMAC key could not be decoded")
            return False

        try:
            items = payload.get("notificationItems") or []
            if not isinstance(items, list) or not items:
                logger.error("Adyen webhook: missing notificationItems")
                return False

            for item in items:
                nri = (item or {}).get("NotificationRequestItem") or {}
                additional = nri.get("additionalData") or {}
                provided_sig = additional.get("hmacSignature") or ""
                if not provided_sig:
                    logger.error("Adyen webhook: missing additionalData.hmacSignature")
                    return False

                amount = nri.get("amount") or {}
                value = amount.get("value")
                currency = amount.get("currency")

                signing_values = [
                    _escape(nri.get("pspReference")),
                    _escape(nri.get("originalReference")),
                    _escape(nri.get("merchantAccountCode")),
                    _escape(nri.get("merchantReference")),
                    _escape(value),
                    _escape(currency),
                    _escape(nri.get("eventCode")),
                    _escape(str(nri.get("success") or "").lower()),
                ]
                signing_str = ":".join(signing_values)

                mac = hmac.new(key_bytes, signing_str.encode("utf-8"), hashlib.sha256)
                expected_sig = base64.b64encode(mac.digest()).decode("utf-8")

                if not hmac.compare_digest(expected_sig, provided_sig):
                    logger.warning(
                        "Adyen webhook signature mismatch",
                        extra={
                            "provider": "adyen",
                            "pspReference": nri.get("pspReference"),
                            "eventCode": nri.get("eventCode"),
                        },
                    )
                    return False

            return True
        except Exception as e:
            logger.error(f"Adyen Signature Verification Failed: {e}")
            return False
