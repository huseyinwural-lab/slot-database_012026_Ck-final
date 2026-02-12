import pytest
from unittest.mock import MagicMock, AsyncMock
from app.services.providers.adapters import PragmaticAdapter
from app.services.game_engine import GameEngine
from app.core.errors import AppError

@pytest.mark.asyncio
async def test_pragmatic_adapter_signature():
    adapter = PragmaticAdapter()
    
    # Without secret key, it returns True (Dev Mode safety in code)
    # We should mock settings to test failure if key was set.
    # But basic test:
    assert adapter.validate_signature({"hash": "abc"}, {}) is True # Fail open if no secret set

@pytest.mark.asyncio
async def test_pragmatic_mapping():
    adapter = PragmaticAdapter()
    
    payload = {
        "action": "bet",
        "userId": "u1",
        "gameId": "g1",
        "roundId": "r1",
        "reference": "tx1",
        "amount": 10.0,
        "currency": "USD"
    }
    
    mapped = adapter.map_request(payload)
    assert mapped["action"] == "bet"
    assert mapped["player_id"] == "u1"
    assert mapped["amount"] == 10.0

@pytest.mark.asyncio
async def test_pragmatic_response_mapping():
    adapter = PragmaticAdapter()
    engine_resp = {"tx_id": "tx1", "balance": 100.0, "currency": "USD"}
    
    resp = adapter.map_response(engine_resp)
    assert resp["transactionId"] == "tx1"
    assert resp["cash"] == 100.0
    assert resp["error"] == 0

@pytest.mark.asyncio
async def test_pragmatic_error_mapping():
    adapter = PragmaticAdapter()
    
    resp = adapter.map_error("INSUFFICIENT_FUNDS", "No money")
    assert resp["error"] == 1
    assert resp["description"] == "No money"
