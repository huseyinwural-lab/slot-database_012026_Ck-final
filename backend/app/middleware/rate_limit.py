import time
import logging
from collections import defaultdict, deque
from typing import Callable, Deque, Dict, Tuple

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger("app.rate_limit")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Very simple in-memory rate limiting.

    - IP-based limits on selected critical endpoints
    - Uses X-Forwarded-For only when it is safe to trust it
    - Not suitable for multi-node global limits, but enough for basic protection
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        # key -> deque[timestamps]
        self._buckets: Dict[Tuple[str, str], Deque[float]] = defaultdict(deque)
        # Per-path limits: (max_requests, window_seconds)
        # Relax limits in dev/local/test to avoid blocking integration tests
        try:
            from config import settings
            is_dev = getattr(settings, "env", "dev") in {"dev", "local", "test", "ci"}
        except Exception:
            is_dev = False

        login_limit = (100, 60.0) if is_dev else (5, 60.0)
        webhook_limit = (1000, 60.0) # Higher limit for webhooks (e.g. 1000/min)
        
        self._limits = {
            "/api/v1/auth/login": login_limit,
            "/api/v1/payments/stripe/webhook": webhook_limit,
            "/api/v1/payments/adyen/webhook": webhook_limit,
        }

    def _get_client_ip(self, request: Request) -> str:
        remote_ip = request.client.host if request.client else "unknown"

        # In prod/staging, trust X-Forwarded-For ONLY if the immediate peer is a trusted proxy.
        # Otherwise it's spoofable.
        try:
            from config import settings
        except Exception:
            settings = None

        xff = request.headers.get("X-Forwarded-For")
        if not xff:
            return remote_ip

        if settings and getattr(settings, "env", "dev") in {"prod", "staging"}:
            trusted = getattr(settings, "trusted_proxy_ips", "") or ""
            trusted_set = {ip.strip() for ip in trusted.split(",") if ip.strip()}
            if remote_ip not in trusted_set:
                return remote_ip

        # Take the first hop as original client
        return xff.split(",")[0].strip() or remote_ip

    async def dispatch(self, request: Request, call_next: Callable):
        path = request.url.path
        client_ip = self._get_client_ip(request)
        request_id = getattr(getattr(request, "state", None), "request_id", None)
        tenant_id = request.headers.get("X-Tenant-ID")

        limit = None
        for prefix, conf in self._limits.items():
            if path.startswith(prefix):
                limit = conf
                break

        if not limit:
            return await call_next(request)

        max_requests, window = limit
        now = time.monotonic()
        key = (client_ip, path)
        bucket = self._buckets[key]

        # Drop old timestamps
        while bucket and now - bucket[0] > window:
            bucket.popleft()

        if len(bucket) >= max_requests:
            # Stable event name required by ops
            logger.warning(
                "auth.login_rate_limited",
                extra={
                    "event": "auth.login_rate_limited",
                    "request_id": request_id,
                    "client_ip": client_ip,
                    "tenant_id": tenant_id,
                    "path": path,
                },
            )

            # Also write to audit trail (important security signal)
            try:
                from app.core.database import async_session
                from app.services.audit import audit

                async with async_session() as session:
                    await audit.log_event(
                        session=session,
                        request_id=request_id or "unknown",
                        actor_user_id="unknown",
                        tenant_id=tenant_id or "unknown",
                        action="auth.login_rate_limited",
                        resource_type="auth",
                        resource_id=None,
                        result="rate_limited",
                        details={"limit": "5/min", "window_sec": int(window), "user_agent": request.headers.get("User-Agent")},
                        ip_address=client_ip,
                    )
                    await session.commit()
            except Exception as exc:
                logger.warning(
                    "auth.login_rate_limited_audit_write_failed",
                    extra={
                        "event": "auth.login_rate_limited_audit_write_failed",
                        "request_id": request_id,
                        "client_ip": client_ip,
                        "tenant_id": tenant_id,
                        "error": str(exc),
                    },
                )

            return JSONResponse(
                status_code=429,
                content={
                    "detail": "RATE_LIMIT_EXCEEDED",
                    "retry_after_seconds": int(window),
                },
            )

        bucket.append(now)
        return await call_next(request)
