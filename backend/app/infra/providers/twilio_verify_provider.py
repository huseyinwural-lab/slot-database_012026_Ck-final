import os
from twilio.rest import Client

from .errors import IntegrationNotConfigured


def _client() -> tuple[Client, str]:
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    service_sid = os.getenv("TWILIO_VERIFY_SERVICE_SID")
    if not account_sid:
        raise IntegrationNotConfigured("TWILIO_ACCOUNT_SID")
    if not auth_token:
        raise IntegrationNotConfigured("TWILIO_AUTH_TOKEN")
    if not service_sid:
        raise IntegrationNotConfigured("TWILIO_VERIFY_SERVICE_SID")
    return Client(account_sid, auth_token), service_sid


def send_sms_otp(phone: str) -> None:
    client, service_sid = _client()
    client.verify.services(service_sid).verifications.create(to=phone, channel="sms")


def confirm_sms_otp(phone: str, code: str) -> bool:
    client, service_sid = _client()
    result = client.verify.services(service_sid).verification_checks.create(to=phone, code=code)
    return result.status == "approved"
