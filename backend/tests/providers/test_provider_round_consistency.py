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
async def test_provider_round_consistency(client: AsyncClient, async_session_factory):
    # Scenario: Win received for a round that does not exist (Orphan Win)
    # Policy: Create ad-hoc round OR Fail?
    # Our GameEngine currently creates round if missing (Fail-Open / Self-Healing).
    # Let's verify it creates the round and logs it.
    
    async with async_session_factory() as s:
        tenant = Tenant(name="RoundTest", type="owner")
        s.add(tenant)
        await s.commit()
        await s.refresh(tenant)
        
        player = Player(
            tenant_id=tenant.id,
            username="round_player",
            email="round@play.com",
            password_hash="pw",
            balance_real_available=10.0
        )
        s.add(player)
        await s.commit()
        player_id = str(player.id)
        
        from app.repositories.ledger_repo import WalletBalance
        wb = WalletBalance(tenant_id=tenant.id, player_id=player.id, currency="USD", balance_real_available=10.0)
        s.add(wb)
        
        # Create Game (Required for validation)
        from app.models.game_models import Game
        game = Game(
            id="g_new",
            tenant_id=tenant.id,
            provider_id="pragmatic",
            external_id="g_new",
            name="Test Round Consistency Game"
        )
        s.add(game)
        await s.commit()

    with pytest.MonkeyPatch.context() as m:
        m.setattr("config.settings.pragmatic_secret_key", SECRET_KEY)
        
        win_tx_id = str(uuid.uuid4())
        payload = {
            "action": "win",
            "userId": player_id,
            "gameId": "g_new",
            "roundId": "r_orphan_1", # Never seen before
            "reference": win_tx_id,
            "amount": 50.0,
            "currency": "USD"
        }
        payload["hash"] = sign_payload(payload)
        
        resp = await client.post("/api/v1/games/callback/pragmatic", json=payload)
        assert resp.status_code == 200
        assert resp.json()["cash"] == 60.0
        
        # Verify Round Created
        async with async_session_factory() as s:
            from app.models.game_models import GameRound
            from sqlmodel import select
            
            stmt = select(GameRound).where(GameRound.provider_round_id == "r_orphan_1")
            round_obj = (await s.execute(stmt)).scalars().first()
            assert round_obj is not None
            assert round_obj.total_win == 50.0
