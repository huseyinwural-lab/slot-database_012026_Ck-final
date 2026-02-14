from __future__ import annotations

import os
import asyncio
import time
from typing import Optional, Any, List

import redis.asyncio as redis
from config import settings
import logging

logger = logging.getLogger(__name__)

class MockPipeline:
    def __init__(self, store, expires, lock):
        self._store = store
        self._expires = expires
        self._lock = lock
        self._commands: List[tuple] = []

    def incr(self, key: str) -> MockPipeline:
        self._commands.append(("incr", key))
        return self

    def incrbyfloat(self, key: str, amount: float) -> MockPipeline:
        self._commands.append(("incrbyfloat", key, amount))
        return self

    def expire(self, key: str, seconds: int, nx: bool = False) -> MockPipeline:
        self._commands.append(("expire", key, seconds, nx))
        return self

    async def execute(self):
        results = []
        async with self._lock:
            for cmd in self._commands:
                op = cmd[0]
                if op == "incr":
                    key = cmd[1]
                    self._prune(key)
                    val = int(self._store.get(key, 0))
                    val += 1
                    self._store[key] = str(val)
                    results.append(val)
                elif op == "incrbyfloat":
                    key = cmd[1]
                    amount = cmd[2]
                    self._prune(key)
                    val = float(self._store.get(key, 0.0))
                    val += float(amount)
                    self._store[key] = str(val)
                    results.append(val)
                elif op == "expire":
                    key = cmd[1]
                    seconds = cmd[2]
                    # nx ignored in mock for simplicity, or implement if needed
                    if key in self._store:
                        self._expires[key] = time.time() + seconds
                        results.append(True)
                    else:
                        results.append(False)
        return results

    def _prune(self, key: str):
        if key in self._expires and time.time() > self._expires[key]:
            self._store.pop(key, None)
            self._expires.pop(key, None)

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

    def pipeline(self):
        return MockPipeline(self._store, self._expires, self._lock)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class RedisClient:
    _instance: Optional[Any] = None

    @classmethod
    def get_instance(cls) -> Any:
        if cls._instance is None:
            # Force Mock if MOCK_REDIS is set OR if we are in the specific dev env where localhost redis fails
            mock_env = os.getenv("MOCK_REDIS", "false").lower() == "true"
            
            # Explicitly check for the broken localhost config in this environment
            redis_url = settings.redis_url or os.getenv("REDIS_URL", "")
            is_broken_localhost = "localhost" in redis_url and "docker" not in redis_url # Heuristic
            
            if mock_env or is_broken_localhost:
                logger.info(f"Using InMemoryRedis (Mock). Reason: env={mock_env}, url={redis_url}")
                cls._instance = InMemoryRedis()
                return cls._instance

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
    return RedisClient.get_instance()
