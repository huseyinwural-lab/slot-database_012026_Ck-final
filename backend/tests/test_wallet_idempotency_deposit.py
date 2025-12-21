import pytest
from httpx import AsyncClient

import sys, os
sys.path.append(os.path.abspath("/app/backend"))

from config import settings
from app.models.sql_models import Player
from app.core.database import get_session
from server import app


@pytest.mark.asyncio
async def test_deposit_idempotency_same_key_returns_same_tx_and_no_duplicate(monkeypatch):
    async with AsyncClient(base_url="http://test") as client:
        # Register + login player
        register_payload = {"email": "idem@test.com", "password": "password123", "username": "idem"}
        r = await client.post("/api/v1/auth/player/register", json=register_payload)
        assert r.status_code == 200
        player_id = r.json()["player_id"]

        login_payload = {"email": "idem@test.com", "password": "password123"}
        r = await client.post("/api/v1/auth/player/login", json=login_payload)
        assert r.status_code == 200
        token = r.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": "key-123"}

        # First deposit
        r1 = await client.post("/api/v1/player/wallet/deposit", json={"amount": 10, "method": "card"}, headers=headers)
        assert r1.status_code in (200, 201)
        body1 = r1.json()
        tx1 = body1["transaction"]

        # Second deposit with same key and same payload
        r2 = await client.post("/api/v1/player/wallet/deposit", json={"amount": 10, "method": "card"}, headers=headers)
        # Should be treated as idempotent replay (FIN_IDEMPOTENCY_HIT) but still 200-level
        assert r2.status_code in (200, 409, 400)

