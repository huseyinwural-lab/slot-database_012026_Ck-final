from __future__ import annotations

import os
import asyncio
import time
from typing import Optional, Any

import redis.asyncio as redis
from config import settings
import logging

logger = logging.getLogger(__name__)

class InMemoryRedis:
    """A simple in-memory mock of Redis for environments without a real Redis service."""
    def __init__(self):
        self._store = {}
        self._expires = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[str]:
        async with self._lock:
            self._prune(key)
            return self._store.get(key)

    async def set(self, key: str, value: Any, ex: Optional[int] = None):
        async with self._lock:
            self._store[key] = str(value)
            if ex:
                self._expires[key] = time.time() + ex

    async def setex(self, key: str, time_seconds: int, value: Any):
        await self.set(key, value, ex=time_seconds)

    async def incr(self, key: str) -> int:
        async with self._lock:
            self._prune(key)
            val = int(self._store.get(key, 0))
            val += 1
            self._store[key] = str(val)
            return val

    async def expire(self, key: str, seconds: int):
        async with self._lock:
            if key in self._store:
                self._expires[key] = time.time() + seconds
                return True
            return False

    async def delete(self, key: str):
        async with self._lock:
            self._store.pop(key, None)
            self._expires.pop(key, None)

    async def ping(self):
        return True

    async def aclose(self):
        pass

    def _prune(self, key: str):
        if key in self._expires and time.time() > self._expires[key]:
            self._store.pop(key, None)
            self._expires.pop(key, None)

    # Pipeline support (simplistic)
    def pipeline(self):
        return self

    async def execute(self):
        pass
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class RedisClient:
    _instance: Optional[Any] = None

    @classmethod
    def get_instance(cls) -> Any:
        if cls._instance is None:
            # Check env flag to force mock
            if os.getenv("MOCK_REDIS", "false").lower() == "true":
                logger.info("Using InMemoryRedis (Mock)")
                cls._instance = InMemoryRedis()
                return cls._instance

            redis_url = settings.redis_url
            if not redis_url:
                redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            
            try:
                cls._instance = redis.from_url(
                    redis_url, 
                    decode_responses=True, 
                    encoding="utf-8",
                    socket_connect_timeout=1
                )
            except Exception as e:
                logger.warning(f"Redis config present but failed ({e}), falling back to InMemoryRedis")
                cls._instance = InMemoryRedis()
                
        return cls._instance

    @classmethod
    async def close(cls):
        if cls._instance:
            await cls._instance.aclose()
            cls._instance = None

async def get_redis() -> Any:
    """Dependency injection helper."""
    # Force mock if connection failed previously
    return RedisClient.get_instance()
