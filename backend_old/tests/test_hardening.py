import pytest
from unittest.mock import MagicMock, AsyncMock
from app.backend.app.routes.player_verification import _check_rate_limit, _hash_code

@pytest.mark.asyncio
async def test_hash_code():
    code = "123456"
    hashed = _hash_code(code)
    assert hashed != code
    assert len(hashed) == 64 # sha256 hex digest length

@pytest.mark.asyncio
async def test_rate_limit_allowed():
    redis = AsyncMock()
    redis.incr.return_value = 1
    
    allowed = await _check_rate_limit(redis, "test:key", 10, 60)
    assert allowed is True
    redis.expire.assert_called_with("test:key", 60)

@pytest.mark.asyncio
async def test_rate_limit_exceeded():
    redis = AsyncMock()
    redis.incr.return_value = 11
    
    allowed = await _check_rate_limit(redis, "test:key", 10, 60)
    assert allowed is False
