import pytest
from unittest.mock import MagicMock, AsyncMock
from app.services.risk_service import RiskService
from app.models.risk import RiskLevel, RiskProfile

@pytest.mark.asyncio
async def test_risk_cross_flow():
    # Setup: High Risk User
    mock_db = AsyncMock()
    # Mock return for profile fetch: High Risk
    profile_high = RiskProfile(user_id="u_high", risk_score=80, risk_level=RiskLevel.HIGH)
    
    # We need to setup execute differently for the two different calls in the test.
    # 1. check_bet_throttle calls execute(select(risk_level)) -> scalar()
    # 2. evaluate_withdrawal calls execute(select(RiskProfile)) -> scalars().first()
    
    # We can use side_effect or specific mock setup.
    # Simpler: RiskService logic uses DB twice.
    
    # Mock for evaluate_withdrawal:
    # result.scalars().first() -> profile_high
    mock_result_profile = MagicMock()
    mock_result_profile.scalars.return_value.first.return_value = profile_high
    
    # Mock for check_bet_throttle:
    # result.scalar() -> RiskLevel.HIGH
    mock_result_level = MagicMock()
    mock_result_level.scalar.return_value = RiskLevel.HIGH
    
    # Configure execute side_effect
    mock_db.execute = AsyncMock(side_effect=[mock_result_level, mock_result_profile])
    
    mock_redis = MagicMock()
    # Pipeline for throttle: Simulate High usage (e.g. 15 > 10 limit)
    mock_redis.pipeline = MagicMock(return_value=MagicMock(execute=AsyncMock(return_value=[15])))
    # Get for withdrawal velocity check (safe low value)
    mock_redis.get = AsyncMock(return_value="0") 
    
    service = RiskService(mock_db, mock_redis)
    
    # 1. Verify Bet Throttled
    # High risk limit is 10. Redis returns 15. Expect False.
    allowed = await service.check_bet_throttle("u_high")
    assert allowed is False, "High Risk user should be throttled on bets"
    
    # 2. Verify Withdrawal Blocked
    # High risk score (80) > Block Threshold (70)
    verdict = await service.evaluate_withdrawal("u_high", 100.0)
    assert verdict == "BLOCK", "High Risk user should be blocked on withdrawals"

@pytest.mark.asyncio
async def test_risk_cross_flow_low_risk():
    # Setup: Low Risk User
    mock_db = AsyncMock()
    profile_low = RiskProfile(user_id="u_low", risk_score=10, risk_level=RiskLevel.LOW)
    
    mock_result_profile = MagicMock()
    mock_result_profile.scalars.return_value.first.return_value = profile_low
    
    mock_result_level = MagicMock()
    mock_result_level.scalar.return_value = RiskLevel.LOW
    
    mock_db.execute = AsyncMock(side_effect=[mock_result_level, mock_result_profile])
    
    mock_redis = MagicMock()
    # Pipeline for throttle: Simulate Low usage (e.g. 5 < 60 limit)
    mock_redis.pipeline = MagicMock(return_value=MagicMock(execute=AsyncMock(return_value=[5])))
    mock_redis.get = AsyncMock(return_value="0")
    
    service = RiskService(mock_db, mock_redis)
    
    # 1. Verify Bet Allowed
    allowed = await service.check_bet_throttle("u_low")
    assert allowed is True
    
    # 2. Verify Withdrawal Allowed
    verdict = await service.evaluate_withdrawal("u_low", 100.0)
    assert verdict == "ALLOW"
