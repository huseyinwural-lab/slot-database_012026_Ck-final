import pytest
from app.services.wallet_ledger import apply_wallet_delta_with_ledger, WalletInvariantError
from app.models.sql_models import Player, Tenant
from app.repositories.ledger_repo import WalletBalance

@pytest.mark.asyncio
async def test_financial_negative_balance_enforcement(async_session_factory):
    # Setup
    async with async_session_factory() as s:
        tenant = Tenant(name="FinGuard", type="owner")
        s.add(tenant)
        await s.commit()
        await s.refresh(tenant)
        
        player = Player(
            tenant_id=tenant.id,
            username="broke_player",
            email="broke@test.com",
            password_hash="pw",
            balance_real_available=10.0 # Only 10
        )
        s.add(player)
        await s.commit()
        
        # Inject Balance Snapshot
        wb = WalletBalance(tenant_id=tenant.id, player_id=player.id, currency="USD", balance_real_available=10.0)
        s.add(wb)
        await s.commit()
        
        # Act: Try to spend 20
        # Expected: WalletInvariantError
        try:
            await apply_wallet_delta_with_ledger(
                s,
                tenant_id=tenant.id,
                player_id=player.id,
                tx_id="tx_fail",
                event_type="bet",
                delta_available=-20.0,
                delta_held=0.0,
                currency="USD"
            )
            assert False, "Should have raised WalletInvariantError"
        except WalletInvariantError:
            pass # Success
        except Exception as e:
            # Depending on implementation it might raise RuntimeError or AppError wrapper
            # WalletInvariantError inherits from RuntimeError in our code
            assert "negative" in str(e).lower() or "insufficient" in str(e).lower()
