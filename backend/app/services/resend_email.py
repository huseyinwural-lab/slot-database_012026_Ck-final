import os
from typing import Optional

import resend

from app.core.errors import AppError


def _init_client():
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        raise AppError("EMAIL_PROVIDER_NOT_CONFIGURED", "Resend API key is not configured", 500)
    resend.api_key = api_key


def send_email(*, to: str, subject: str, html: str, from_email: Optional[str] = None, reply_to: Optional[str] = None):
    """Send a transactional email via Resend.

    Raises AppError with deterministic error_code on failure.
    """

    _init_client()

    from_env = os.environ.get("RESEND_FROM") or "onboarding@resend.dev"
    reply_to_env = os.environ.get("RESEND_REPLY_TO")

    payload = {
        "from": from_email or from_env,
        "to": [to],
        "subject": subject,
        "html": html,
    }

    # Resend supports reply_to in most SDK versions; keep optional.
    if reply_to or reply_to_env:
        payload["reply_to"] = reply_to or reply_to_env

    try:
        # SDK call
        result = resend.Emails.send(payload)
        # Typical response: {'id': '...'}
        if not result or not result.get("id"):
            raise AppError("EMAIL_PROVIDER_SEND_FAILED", "Email provider did not return an id", 502)
        return {"provider": "resend", "message_id": result["id"]}
    except AppError:
        raise
    except Exception as e:
        msg = str(e)
        if "api key" in msg.lower() or "unauthorized" in msg.lower() or "forbidden" in msg.lower():
            raise AppError("EMAIL_PROVIDER_AUTH_FAILED", "Email provider authentication failed", 401)
        raise AppError("EMAIL_PROVIDER_SEND_FAILED", "Email provider send failed", 502, {"provider_error": msg})
