from __future__ import annotations

from typing import Optional

from arq import create_pool
from arq.connections import RedisSettings, ArqRedis

from config import settings


class ReconciliationJobQueue:
    """Thin wrapper around ARQ Redis pool for reconciliation runs.

    For now we only need fire-and-forget enqueue of a single job function.
    """

    def __init__(self, redis_settings: RedisSettings) -> None:
        self.redis_settings = redis_settings
        self._pool: Optional[ArqRedis] = None

    async def connect(self) -> None:
        if self._pool is None:
            self._pool = await create_pool(self.redis_settings)

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close(close_connection_pool=True)
            self._pool = None

    async def enqueue_reconciliation_run(self, run_id: str) -> None:
        if self._pool is None:
            raise RuntimeError("ARQ Redis pool not initialised")

        # Function name must match the worker function defined in WorkerSettings
        await self._pool.enqueue_job("reconciliation_run_job", run_id)


_queue: Optional[ReconciliationJobQueue] = None


async def init_queue() -> None:
    global _queue
    if _queue is None:
        _queue = ReconciliationJobQueue(settings.arq_redis_settings)
        await _queue.connect()


async def close_queue() -> None:
    global _queue
    if _queue is not None:
        await _queue.close()
        _queue = None


def get_queue() -> ReconciliationJobQueue:
    if _queue is None:
        raise RuntimeError("ReconciliationJobQueue not initialised")
    return _queue
