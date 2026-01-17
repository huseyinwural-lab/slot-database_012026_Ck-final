from typing import Optional, List, Union

import resend

from config import settings
from app.core.errors import AppError


def _init_client():
    if not settings.resend_api_key:
        raise AppError("EMAIL_PROVIDER_NOT_CONFIGURED", "Resend API key is not configured", 500)
    resend.api_key = settings.resend_api_key


def send_email(
    *,
    to: Union[str, List[str]],
    subject: str,
    html: str,
    from_email: Optional[str] = None,
    reply_to: Optional[str] = None,
):
    """Send a transactional email via Resend.

    Raises AppError with deterministic error_code on failure.
    """

    _init_client()

    to_list = [to] if isinstance(to, str) else list(to)

    payload = {
        "from": from_email or settings.resend_from,
        "to": to_list,
        "subject": subject,
        "html": html,
    }

    effective_reply_to = reply_to or settings.resend_reply_to
    if effective_reply_to:
        payload["reply_to"] = effective_reply_to

    try:
        result = resend.Emails.send(payload)
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
