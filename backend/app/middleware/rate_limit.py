import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from app.core.redis_client import get_redis

logger = logging.getLogger("app.ratelimit")

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable):
        # 1. Skip Rate Limit for Health Checks & Metrics
        if request.url.path in ["/api/health", "/api/ready", "/metrics", "/api/v1/readyz"]:
            return await call_next(request)

        # 2. Determine Limit Key & Threshold based on Route
        ip = request.client.host if request.client else "unknown"
        path = request.url.path
        
        limit = 100 # Default
        window = 60 # Seconds
        
        if path.startswith("/api/v1/auth"):
            limit = 10 # Strict for auth
            key = f"rl:auth:{ip}"
        elif path.startswith("/api/v1/games/callback"):
            limit = 2000 # High throughput for providers
            # Key should be per provider IP ideally, or global if behind load balancer without X-Forwarded-For trust
            # For now, IP based. Real prod needs header trust config.
            key = f"rl:prov:{ip}"
        elif path.startswith("/api/v1/player"):
            limit = 60 # Player actions
            key = f"rl:player:{ip}"
        else:
            key = f"rl:global:{ip}"

        # 3. Check Limit (Redis)
        try:
            redis = await get_redis()
            # Simple Fixed Window for P0/P1 efficiency
            # INCR key -> if 1 then EXPIRE
            current = await redis.incr(key)
            if current == 1:
                await redis.expire(key, window)
            
            if current > limit:
                logger.warning(f"Rate limit exceeded for {ip} on {path}. Count: {current}/{limit}")
                return Response("Too Many Requests", status_code=429)
                
        except Exception as e:
            # Fail open if Redis down (don't block traffic due to infra failure in middleware)
            # Log error
            logger.error(f"Rate limit check failed: {e}")

        return await call_next(request)
