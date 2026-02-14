import pytest
from unittest.mock import MagicMock, AsyncMock
from app.services.game_engine import GameEngine
from app.core.errors import AppError

@pytest.mark.asyncio
async def test_bet_throttling_integration():
    # Setup Mocks
    mock_session = AsyncMock()
    mock_risk = AsyncMock()
    mock_redis = MagicMock()
    
    # Patch RiskService inside GameEngine context or check_bet_throttle
    # Since we instantiate RiskService inside process_bet, we need to mock Redis response
    # to control the throttle result.
    
    # Simulate Redis returning HIGH usage
    mock_redis.pipeline = MagicMock(return_value=MagicMock(execute=AsyncMock(return_value=[100]))) # > 60
    
    # We need to patch get_redis to return our mock
    with pytest.MonkeyPatch.context() as m:
        m.setattr("app.services.game_engine.get_redis", AsyncMock(return_value=mock_redis))
        
        engine = GameEngine()
        
        try:
            await engine.process_bet(
                mock_session, "prov", "tx1", "u1", "g1", "r1", 10.0, "USD"
            )
            assert False, "Should have raised AppError"
        except AppError as e:
            assert e.error_code == "RATE_LIMIT_EXCEEDED"
            assert e.status_code == 429
