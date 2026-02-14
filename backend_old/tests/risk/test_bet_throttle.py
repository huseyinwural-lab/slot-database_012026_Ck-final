import pytest
from unittest.mock import MagicMock, AsyncMock
from app.services.risk_service import RiskService
from app.models.risk import RiskLevel, RiskProfile

@pytest.mark.asyncio
async def test_throttle_low_risk_allow():
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=MagicMock(scalar=lambda: RiskLevel.LOW))
    
    mock_redis = MagicMock()
    mock_redis.pipeline = MagicMock(return_value=MagicMock(execute=AsyncMock(return_value=[10]))) # count 10 < 60
    
    service = RiskService(mock_db, mock_redis)
    allowed = await service.check_bet_throttle("u1")
    assert allowed is True

@pytest.mark.asyncio
async def test_throttle_high_risk_block():
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=MagicMock(scalar=lambda: RiskLevel.HIGH))
    
    mock_redis = MagicMock()
    mock_redis.pipeline = MagicMock(return_value=MagicMock(execute=AsyncMock(return_value=[15]))) # count 15 > 10 (High Limit)
    
    service = RiskService(mock_db, mock_redis)
    allowed = await service.check_bet_throttle("u1")
    assert allowed is False
