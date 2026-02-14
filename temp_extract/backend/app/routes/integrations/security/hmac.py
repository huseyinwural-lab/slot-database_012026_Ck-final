from fastapi import HTTPException, Request
from config import settings
import hmac
import hashlib
import time

DEFAULT_TOLERANCE_SECONDS = 300


def verify_hmac_signature(request: Request, secret: str, header_prefix: str = "X") -> bool:
    """Generic HMAC signature verification.

    Contract:
    - Headers: {header_prefix}-Signature, {header_prefix}-Timestamp
    - Message: f"{timestamp}." + raw_body
    - Signature: hex(HMAC-SHA256(secret, message))

    Notes:
    - Enforced only when settings.webhook_signature_enforced is True
    - Uses constant-time compare via hmac.compare_digest
    """

    if not settings.webhook_signature_enforced:
        return True

    signature = request.headers.get(f"{header_prefix}-Signature")
    timestamp = request.headers.get(f"{header_prefix}-Timestamp")

    if not signature or not timestamp:
        raise HTTPException(status_code=401, detail="Missing signature headers")

    # Replay protection
    now = int(time.time())
    try:
        ts_int = int(timestamp)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid timestamp format")

    if abs(now - ts_int) > DEFAULT_TOLERANCE_SECONDS:
        raise HTTPException(status_code=401, detail="Timestamp expired")

    body = getattr(request, "_body", None)
    if body is None:
        # FastAPI Request can only be read once; callers should call this dependency
        # after `await request.body()` (or not read it elsewhere).
        raise HTTPException(status_code=500, detail="Request body not loaded")

    message = f"{timestamp}.".encode("utf-8") + body
    expected_sig = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(signature, expected_sig):
        raise HTTPException(status_code=401, detail="Invalid signature")

    return True


class SecurityContext:
    @staticmethod
    async def verify_poker(request: Request):
        # NOTE: provider-specific secret should be wired here; audit_export_secret is a fallback.
        await request.body()  # populate request._body
        return verify_hmac_signature(request, settings.audit_export_secret)
