import hmac
import time
from hashlib import sha256
from typing import Tuple

from fastapi import HTTPException

from config import settings

WEBHOOK_SECRET_ENV = "WEBHOOK_SECRET"
DEFAULT_TOLERANCE_SECONDS = 300  # 75 dakika


class WebhookSignatureError(HTTPException):
    pass


def _get_secret() -> bytes:
    """Return webhook signing secret.

    Contract:
    - In prod/staging we require WEBHOOK_SECRET.
    - In ci/test/dev we allow a deterministic WEBHOOK_TEST_SECRET so E2E can
      send a real signature without weakening prod security.

    NOTE: We use config.settings (BaseSettings + env_file) so local dev works
    without exporting env vars.
    """

    if settings.webhook_secret:
        return settings.webhook_secret.encode("utf-8")

    env = (settings.env or "dev").lower()
    if env in {"ci", "test", "dev", "local"}:
        # CI drift-safe deterministic fallback.
        # If WEBHOOK_TEST_SECRET is not explicitly set, we still enable signed webhooks
        # using a known test secret. Prod/staging still hard-fails.
        test_secret = settings.webhook_test_secret or "ci_webhook_test_secret"
        return test_secret.encode("utf-8")

    raise HTTPException(status_code=500, detail={"error_code": "WEBHOOK_SECRET_MISSING"})


def _compute_signature(secret: bytes, timestamp: str, raw_body: bytes) -> str:
    signed_payload = f"{timestamp}.".encode("utf-8") + raw_body
    mac = hmac.new(secret, signed_payload, sha256)
    return mac.hexdigest()


def verify_webhook_signature(
    timestamp_header: str | None,
    signature_header: str | None,
    raw_body: bytes,
    tolerance_seconds: int = DEFAULT_TOLERANCE_SECONDS,
) -> Tuple[int, str]:
    """Verify X-Webhook-Timestamp + X-Webhook-Signature according to contract.

    Returns a tuple (status_code, error_code) for error cases, or (200, "") on success.
    Caller is responsible for raising HTTPException with these values.
    """

    if not timestamp_header or not signature_header:
        return 400, "WEBHOOK_SIGNATURE_MISSING"

    try:
        ts = int(timestamp_header)
    except ValueError:
        return 401, "WEBHOOK_TIMESTAMP_INVALID"

    now = int(time.time())
    if abs(now - ts) > tolerance_seconds:
        return 401, "WEBHOOK_TIMESTAMP_INVALID"

    secret = _get_secret()
    expected_sig = _compute_signature(secret, timestamp_header, raw_body)

    # Use hmac.compare_digest for constant-time comparison
    if not hmac.compare_digest(expected_sig, signature_header):
        return 401, "WEBHOOK_SIGNATURE_INVALID"

    return 200, ""
