import pytest
import base64
import hmac
import hashlib

from app.services.adyen_psp import AdyenPSP
from config import settings


@pytest.mark.asyncio
async def test_adyen_hmac_signature_valid_base64_key():
    # Build a deterministic payload with one notification item
    payload = {
        "notificationItems": [
            {
                "NotificationRequestItem": {
                    "pspReference": "7914073381342284",
                    "originalReference": "",
                    "merchantAccountCode": "TestMerchant",
                    "merchantReference": "TestPayment-1407325143704",
                    "amount": {"value": 1130, "currency": "EUR"},
                    "eventCode": "AUTHORISATION",
                    "success": "true",
                    "additionalData": {},
                }
            }
        ]
    }

    signing_str = "7914073381342284::TestMerchant:TestPayment-1407325143704:1130:EUR:AUTHORISATION:true"

    key_bytes = b"supersecretkeybytes"
    key_b64 = base64.b64encode(key_bytes).decode("utf-8")

    mac = hmac.new(key_bytes, signing_str.encode("utf-8"), hashlib.sha256)
    sig = base64.b64encode(mac.digest()).decode("utf-8")

    payload["notificationItems"][0]["NotificationRequestItem"]["additionalData"]["hmacSignature"] = sig

    old = settings.adyen_hmac_key
    settings.adyen_hmac_key = key_b64
    try:
        adyen = AdyenPSP(api_key="mock", merchant_account="mock")
        assert adyen.verify_webhook_signature(payload) is True
    finally:
        settings.adyen_hmac_key = old


@pytest.mark.asyncio
async def test_adyen_hmac_signature_invalid():
    payload = {
        "notificationItems": [
            {
                "NotificationRequestItem": {
                    "pspReference": "7914073381342284",
                    "originalReference": "",
                    "merchantAccountCode": "TestMerchant",
                    "merchantReference": "TestPayment-1407325143704",
                    "amount": {"value": 1130, "currency": "EUR"},
                    "eventCode": "AUTHORISATION",
                    "success": "true",
                    "additionalData": {"hmacSignature": "invalid"},
                }
            }
        ]
    }

    old = settings.adyen_hmac_key
    settings.adyen_hmac_key = base64.b64encode(b"supersecretkeybytes").decode("utf-8")
    try:
        adyen = AdyenPSP(api_key="mock", merchant_account="mock")
        assert adyen.verify_webhook_signature(payload) is False
    finally:
        settings.adyen_hmac_key = old
