import pytest
from httpx import AsyncClient
import uuid
import hashlib
import hmac
from app.models.sql_models import Player, Tenant

SECRET_KEY = "test_secret"

def sign_payload(payload: dict) -> str:
    canonical = "&".join([f"{k}={v}" for k, v in sorted(payload.items())])
    return hmac.new(
        SECRET_KEY.encode("utf-8"),
        canonical.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

@pytest.mark.asyncio
async def test_provider_idempotency_debug(client: AsyncClient, async_session_factory):
    # Setup
    async with async_session_factory() as s:
        tenant = Tenant(name="IdemTest", type="owner")
        s.add(tenant)
        await s.commit()
        await s.refresh(tenant)
        
        player = Player(
            tenant_id=tenant.id,
            username="idem_player",
            email="idem@play.com",
            password_hash="pw",
            balance_real_available=50.0
        )
        s.add(player)
        await s.commit()
        player_id = str(player.id)
        
        from app.repositories.ledger_repo import WalletBalance
        wb = WalletBalance(tenant_id=tenant.id, player_id=player.id, currency="USD", balance_real_available=50.0)
        s.add(wb)
        await s.commit()

    with pytest.MonkeyPatch.context() as m:
        m.setattr("config.settings.pragmatic_secret_key", SECRET_KEY)
        
        tx_id = str(uuid.uuid4())
        payload = {
            "action": "bet",
            "userId": player_id,
            "gameId": "g_idem",
            "roundId": "r_idem",
            "reference": tx_id,
            "amount": 10.0,
            "currency": "USD"
        }
        payload["hash"] = sign_payload(payload)
        
        print(f"DEBUG: Sending payload with player_id: {player_id}")
        print(f"DEBUG: Payload: {payload}")
        
        # First Call
        resp1 = await client.post("/api/v1/games/callback/pragmatic", json=payload)
        print(f"DEBUG: Response status: {resp1.status_code}")
        print(f"DEBUG: Response body: {resp1.text}")
        print(f"DEBUG: Response JSON: {resp1.json()}")
        
        assert resp1.status_code == 200
        response_json = resp1.json()
        
        # Check if it's an error response
        if "error" in response_json:
            print(f"DEBUG: Got error response: {response_json}")
            assert False, f"Expected success but got error: {response_json}"
        
        assert response_json["cash"] == 40.0