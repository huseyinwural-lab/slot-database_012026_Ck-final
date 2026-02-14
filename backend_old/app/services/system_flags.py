import json
import os
from datetime import datetime
from typing import Dict, Optional

import redis.asyncio as redis
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sql_models import FeatureFlag


CACHE_KEY = "system_feature_flags:v1"
CACHE_TTL_SECONDS = 60


FLAG_DEFS: Dict[str, Dict[str, object]] = {
    "ENABLE_STRIPE": {
        "description": "Stripe ödeme altyapısı",
        "default": os.getenv("ENABLE_STRIPE", "0").strip() == "1",
    },
    "ENABLE_AI": {
        "description": "AI risk analizi",
        "default": os.getenv("ENABLE_AI", "0").strip() == "1",
    },
}


async def _get_redis_client() -> Optional[redis.Redis]:
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        return None
    return redis.from_url(redis_url, decode_responses=True)


async def _get_cached_flags() -> Optional[Dict[str, Dict[str, object]]]:
    client = await _get_redis_client()
    if client is None:
        return None
    try:
        raw = await client.get(CACHE_KEY)
        if not raw:
            return None
        return json.loads(raw)
    finally:
        await client.close()


async def _set_cached_flags(flags: Dict[str, Dict[str, object]]) -> None:
    client = await _get_redis_client()
    if client is None:
        return
    try:
        await client.set(CACHE_KEY, json.dumps(flags), ex=CACHE_TTL_SECONDS)
    finally:
        await client.close()


async def _load_flags_from_db(session: AsyncSession) -> Dict[str, Dict[str, object]]:
    stmt = select(FeatureFlag).where(FeatureFlag.key.in_(FLAG_DEFS.keys()))
    existing = (await session.execute(stmt)).scalars().all()
    by_key = {flag.key: flag for flag in existing}

    missing: list[FeatureFlag] = []
    for key, meta in FLAG_DEFS.items():
        if key not in by_key:
            missing.append(
                FeatureFlag(
                    key=key,
                    description=str(meta.get("description")),
                    is_enabled=bool(meta.get("default")),
                    created_at=datetime.utcnow().isoformat(),
                )
            )
    if missing:
        session.add_all(missing)
        await session.commit()
        for flag in missing:
            by_key[flag.key] = flag

    return {
        key: {
            "key": key,
            "description": by_key[key].description,
            "enabled": bool(by_key[key].is_enabled),
        }
        for key in FLAG_DEFS.keys()
    }


async def get_system_flags(session: AsyncSession) -> Dict[str, Dict[str, object]]:
    cached = await _get_cached_flags()
    if cached is not None:
        return cached
    flags = await _load_flags_from_db(session)
    await _set_cached_flags(flags)
    return flags


async def is_system_flag_enabled(session: AsyncSession, flag_key: str) -> bool:
    flags = await get_system_flags(session)
    return bool(flags.get(flag_key, {}).get("enabled"))


async def update_system_flag(
    session: AsyncSession, flag_key: str, enabled: bool
) -> Dict[str, object]:
    stmt = select(FeatureFlag).where(FeatureFlag.key == flag_key)
    flag = (await session.execute(stmt)).scalars().first()
    if flag is None:
        meta = FLAG_DEFS.get(flag_key, {"description": flag_key})
        flag = FeatureFlag(
            key=flag_key,
            description=str(meta.get("description")),
            is_enabled=enabled,
            created_at=datetime.utcnow().isoformat(),
        )
        session.add(flag)
    before = bool(flag.is_enabled)
    flag.is_enabled = enabled
    await session.flush()

    flags = await _load_flags_from_db(session)
    await _set_cached_flags(flags)
    return {"before": before, "after": enabled}
