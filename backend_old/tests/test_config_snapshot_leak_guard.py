import logging
import re

from app.core.connection_strings import summarize_database_url, summarize_redis_url
from app.core.logging_config import JSONFormatter


_POSTGRES_CRED_RE = re.compile(r"postgresql(\+\w+)?:\/\/[^\s\/]+:[^\s@]+@", re.IGNORECASE)
_REDIS_CRED_RE = re.compile(r"redis(s)?:\/\/:.*@", re.IGNORECASE)


def _format_event(extra):
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="config.snapshot",
        args=(),
        exc_info=None,
    )
    for k, v in extra.items():
        setattr(record, k, v)
    return formatter.format(record)


def test_config_snapshot_has_no_credentials_or_tokens():
    db_url = "postgresql+asyncpg://user:pass@db.example.com:5432/mydb?sslmode=require"
    redis_url = "redis://:secretpass@redis.example.com:6379/0"

    payload = {
        "event": "config.snapshot",
        "db": summarize_database_url(db_url),
        "redis": summarize_redis_url(redis_url),
    }

    rendered = _format_event(payload)

    # Forbidden keywords
    assert "Bearer " not in rendered
    assert "access_token" not in rendered
    assert "redis://:" not in rendered

    # Credential patterns must not appear
    assert _POSTGRES_CRED_RE.search(rendered) is None
    assert _REDIS_CRED_RE.search(rendered) is None
