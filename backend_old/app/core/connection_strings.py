from __future__ import annotations

from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlparse

from sqlalchemy.engine.url import make_url


SYNC_DB_ENV_CANDIDATES = ("SYNC_DATABASE_URL", "DATABASE_URL_SYNC")


def derive_sync_database_url(*, database_url: str, sync_database_url: Optional[str] = None) -> str:
    """Return a *sync* SQLAlchemy URL usable by Alembic.

    Rules:
    - If explicit sync_database_url is provided -> return it.
    - If database_url is async (e.g., postgresql+asyncpg / sqlite+aiosqlite) -> convert to sync.
    - Otherwise return database_url as-is.

    NOTE: This function intentionally does **not** apply any default SSL settings.
    Whatever is encoded into the URL query params is preserved.
    """

    if sync_database_url:
        return sync_database_url

    url = make_url(database_url)
    driver = url.drivername

    if driver.endswith("+aiosqlite"):
        url = url.set(drivername="sqlite")
    elif driver.endswith("+asyncpg"):
        # Alembic uses sync drivers by default.
        url = url.set(drivername="postgresql+psycopg2")
    elif driver == "postgresql":
        # Be explicit to avoid environments without default driver resolution.
        url = url.set(drivername="postgresql+psycopg2")

    return str(url)


def summarize_database_url(database_url: str) -> Dict[str, Any]:
    """Return a non-sensitive summary for logs (NO user/pass)."""

    url = make_url(database_url)
    query = dict(url.query or {})

    return {
        "driver": url.drivername,
        "host": url.host,
        "port": url.port,
        "dbname": url.database,
        # Common Postgres SSL parameter (if provided)
        "sslmode": query.get("sslmode"),
    }


def summarize_redis_url(redis_url: str) -> Dict[str, Any]:
    """Return a non-sensitive Redis summary for logs (NO user/pass)."""

    parsed = urlparse(redis_url)
    qs = parse_qs(parsed.query)

    # Path typically like /0
    db_index = None
    if parsed.path and parsed.path != "/":
        try:
            db_index = int(parsed.path.lstrip("/"))
        except ValueError:
            db_index = None

    tls = parsed.scheme == "rediss" or str(qs.get("ssl", [""])[0]).lower() in {"1", "true", "yes"}

    return {
        "scheme": parsed.scheme,
        "host": parsed.hostname,
        "port": parsed.port,
        "db": db_index,
        "tls": tls,
    }
