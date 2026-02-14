import logging
import os
from typing import Optional

from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from config import settings
from app.core.redis_health import redis_ping
from app.core.database import engine as default_engine


router = APIRouter(prefix="/api/v1", tags=["health"])
logger = logging.getLogger(__name__)


def _resolve_db_url() -> str:
    return (os.getenv("POSTGRES_URL") or os.getenv("DATABASE_URL") or settings.database_url or "").strip()


def _build_engine(url: str) -> Optional[AsyncEngine]:
    if not url:
        return None
    if url == settings.database_url:
        return default_engine
    return create_async_engine(url, future=True)


_DB_URL = _resolve_db_url()
_READY_ENGINE = _build_engine(_DB_URL)


@router.get("/healthz")
async def healthz():
    return {"status": "ok"}


@router.get("/readyz")
async def readyz():
    if not _DB_URL or _READY_ENGINE is None:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "degraded",
                "dependencies": {"database": "not_configured", "redis": "unknown"},
            },
        )

    try:
        async with _READY_ENGINE.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as exc:
        logger.exception("readyz database check failed", exc_info=exc)
        raise HTTPException(
            status_code=503,
            detail={
                "status": "degraded",
                "dependencies": {"database": "unreachable", "redis": "unknown"},
            },
        )

    redis_url = (os.getenv("REDIS_URL") or "").strip()
    redis_status = "skipped"
    if redis_url:
        try:
            redis_status = "connected" if await redis_ping(redis_url) else "unreachable"
        except Exception:
            redis_status = "unreachable"

        if redis_status != "connected":
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "degraded",
                    "dependencies": {"database": "connected", "redis": redis_status},
                },
            )

    return {"status": "ready", "dependencies": {"database": "connected", "redis": redis_status}}
