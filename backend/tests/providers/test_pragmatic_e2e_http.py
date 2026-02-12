import pytest
from httpx import AsyncClient
import uuid
import hashlib
import hmac
import json
from app.models.sql_models import Player, Tenant
# Correct import for WalletBalance
from app.repositories.ledger_repo import WalletBalance
from app.services.game_engine import game_engine

# Mock Secret
SECRET_KEY = "test_secret"

def sign_payload(payload: dict) -> str:
    # Pragmatic signature: params sorted by key
    canonical = "&".join([f"{k}={v}" for k, v in sorted(payload.items())])
    return hmac.new(
        SECRET_KEY.encode("utf-8"),
        canonical.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

@pytest.mark.asyncio
async def test_pragmatic_e2e_flow(client: AsyncClient, async_session_factory):
    # 1. Setup Tenant & Player
    async with async_session_factory() as s:
        tenant = Tenant(name="PragmaticTest", type="owner")
        s.add(tenant)
        await s.commit()
        await s.refresh(tenant)
        
        player = Player(
            tenant_id=tenant.id,
            username="prag_player",
            email="prag@play.com",
            password_hash="pw",
            balance_real_available=100.0,
            balance_real_held=0.0
        )
        s.add(player)
        await s.commit()
        player_id = str(player.id)
        
        # Inject Balance Snapshot
        wb = WalletBalance(
            tenant_id=tenant.id,
            player_id=player.id,
            currency="USD",
            balance_real_available=100.0
        )
        s.add(wb)
        await s.commit()

    with pytest.MonkeyPatch.context() as m:
        m.setattr("config.settings.pragmatic_secret_key", SECRET_KEY)
        
        # 2. Balance Check
        payload = {
            "action": "balance",
            "userId": player_id,
            "currency": "USD"
        }
        payload["hash"] = sign_payload(payload)
        
        resp = await client.post("/api/v1/games/callback/pragmatic", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["cash"] == 100.0
        
        # 3. Bet ($10)
        tx_id = str(uuid.uuid4())
        payload = {
            "action": "bet",
            "userId": player_id,
            "gameId": "g_1",
            "roundId": "r_1",
            "reference": tx_id,
            "amount": 10.0,
            "currency": "USD"
        }
        payload["hash"] = sign_payload(payload)
        
        resp = await client.post("/api/v1/games/callback/pragmatic", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("error") == 0
        assert data["cash"] == 90.0
        assert data["transactionId"] == tx_id
        
        # 4. Win ($20)
        win_tx_id = str(uuid.uuid4())
        payload = {
            "action": "win",
            "userId": player_id,
            "gameId": "g_1",
            "roundId": "r_1",
            "reference": win_tx_id,
            "amount": 20.0,
            "currency": "USD"
        }
        payload["hash"] = sign_payload(payload)
        
        resp = await client.post("/api/v1/games/callback/pragmatic", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("error") == 0
        assert data["cash"] == 110.0 # 90 + 20
        
        # 5. Duplicate Win (Idempotency)
        # Same payload, same reference
        resp = await client.post("/api/v1/games/callback/pragmatic", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("error") == 0
        assert data["cash"] == 110.0 # Should not change
        
    # 6. Verify Wallet Final State
    async with async_session_factory() as s:
        p = await s.get(Player, player_id)
        assert p.balance_real_available == 110.0
