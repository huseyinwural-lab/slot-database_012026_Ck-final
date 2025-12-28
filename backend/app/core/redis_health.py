from __future__ import annotations

from urllib.parse import urlparse

import redis.asyncio as redis


async def redis_ping(redis_url: str) -> bool:
    """Lightweight Redis connectivity probe (PING).

    Uses URL as-is (supports redis:// and rediss://). No defaults.
    """

    parsed = urlparse(redis_url)
    if not parsed.scheme or not parsed.hostname:
        return False

    client = redis.from_url(redis_url)
    try:
        res = await client.ping()
        return bool(res)
    finally:
        await client.aclose()
