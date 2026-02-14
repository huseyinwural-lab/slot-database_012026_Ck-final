import time
import logging
import os
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from app.core.redis_client import get_redis

logger = logging.getLogger("app.ratelimit")

def is_test_mode():
    return os.getenv("MOCK_EXTERNAL_SERVICES", "false").lower() == "true" or \
           os.getenv("E2E_MODE", "false").lower() == "true"

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable):
        if request.url.path in ["/api/health", "/api/ready", "/metrics", "/api/v1/readyz"]:
            return await call_next(request)

        ip = request.client.host if request.client else "unknown"
        path = request.url.path
        
        limit = 100 
        window = 60 
        
        # Policy Definition
        if path.startswith("/api/v1/auth/player/register"):
            # Strict in PROD, relaxed in TEST/MOCK
            if is_test_mode():
                limit = 1000 # Allow load/e2e testing from single IP
            else:
                limit = 10 # Strict
            key = f"rl:auth:reg:{ip}"
            
        elif path.startswith("/api/v1/auth/player/login"):
            if is_test_mode():
                limit = 2000
            else:
                limit = 20 
            key = f"rl:auth:login:{ip}"
            
        elif path.startswith("/api/v1/games/callback"):
            limit = 10000 
            key = f"rl:prov:{ip}"
            
        elif path.startswith("/api/v1/player"):
            if is_test_mode():
                limit = 5000
            else:
                limit = 500
            key = f"rl:player:{ip}"
            
        else:
            key = f"rl:global:{ip}"

        try:
            redis = await get_redis()
            current = await redis.incr(key)
            if current == 1:
                await redis.expire(key, window)
            
            if current > limit:
                # logger.warning(f"Rate limit exceeded for {ip} on {path}. Count: {current}/{limit}")
                # Standard Error Response
                return Response('{"error_code": "RATE_LIMITED", "message": "Too many requests"}', status_code=429, media_type="application/json")
                
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")

        return await call_next(request)
