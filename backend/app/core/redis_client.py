from __future__ import annotations

import os
from typing import Optional

import redis.asyncio as redis
from config import settings

class RedisClient:
    _instance: Optional[redis.Redis] = None

    @classmethod
    def get_instance(cls) -> redis.Redis:
        if cls._instance is None:
            redis_url = settings.redis_url
            if not redis_url:
                # Fallback for local dev if not set in settings but usually it is
                redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            
            cls._instance = redis.from_url(
                redis_url, 
                decode_responses=True, # Auto-decode bytes to strings
                encoding="utf-8"
            )
        return cls._instance

    @classmethod
    async def close(cls):
        if cls._instance:
            await cls._instance.aclose()
            cls._instance = None

async def get_redis() -> redis.Redis:
    """Dependency injection helper."""
    return RedisClient.get_instance()
