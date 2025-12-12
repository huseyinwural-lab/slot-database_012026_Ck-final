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
    - Not suitable for multi-node global limits, but enough for basic protection
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        # key -> deque[timestamps]
        self._buckets: Dict[Tuple[str, str], Deque[float]] = defaultdict(deque)
        # Per-path limits: (max_requests, window_seconds)
        self._limits = {
            "/api/v1/auth/login": (10, 60.0),  # 10 login attempts / minute per IP
        }

    async def dispatch(self, request: Request, call_next: Callable):
        path = request.url.path
        client_host = request.client.host if request.client else "unknown"

        limit = None
        for prefix, conf in self._limits.items():
            if path.startswith(prefix):
                limit = conf
                break

        if not limit:
            return await call_next(request)

        max_requests, window = limit
        now = time.monotonic()
        key = (client_host, path)
        bucket = self._buckets[key]

        # Drop old timestamps
        while bucket and now - bucket[0] > window:
            bucket.popleft()

        if len(bucket) >= max_requests:
            logger.warning("rate limit exceeded", extra={"ip": client_host, "path": path})
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "RATE_LIMIT_EXCEEDED",
                    "retry_after_seconds": int(window),
                },
            )

        bucket.append(now)
        return await call_next(request)
