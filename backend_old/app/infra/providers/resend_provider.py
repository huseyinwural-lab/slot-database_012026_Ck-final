import os
from resend import Emails

from .errors import IntegrationNotConfigured


def send_email_otp(email: str, code: str) -> None:
    api_key = os.getenv("RESEND_API_KEY")
    from_email = os.getenv("RESEND_FROM")
    if not api_key:
        raise IntegrationNotConfigured("RESEND_API_KEY")
    if not from_email:
        raise IntegrationNotConfigured("RESEND_FROM")

    subject = "Casino OTP doğrulama kodunuz"
    html = f"<p>Doğrulama kodunuz: <strong>{code}</strong></p>"

    client = Emails(api_key=api_key)
    client.send(
        {
            "from": from_email,
            "to": [email],
            "subject": subject,
            "html": html,
        }
    )
