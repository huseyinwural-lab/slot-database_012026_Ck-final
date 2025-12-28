import re

from test_runtime_failfast_uvicorn import _run_uvicorn


def test_runtime_failfast_ci_strict_invalid_redis_url():
    # Invalid/unreachable REDIS_URL must fail-fast (no listener) in CI_STRICT.
    code, logs = _run_uvicorn(
        {
            "ENV": "staging",
            "CI_STRICT": "1",
            "DATABASE_URL": "postgresql+asyncpg://user:pass@127.0.0.1:1/db",
            "REDIS_URL": "redis://127.0.0.1:1/0",
            # Avoid other prod/staging validations
            "JWT_SECRET": "test_secret",
            "CORS_ORIGINS": '["http://localhost"]',
        },
        timeout_seconds=5,
    )

    assert code != 0
    assert "Uvicorn running on" not in logs
    assert re.search(r"REDIS_URL", logs, re.IGNORECASE) is not None
