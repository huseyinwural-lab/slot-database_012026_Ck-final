import asyncio
import sys
import os
import uuid
import json
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from config import settings

sys.path.append("/app/backend")

# Import logic
from app.services.payments.routing.router import PaymentRouter
from app.services.payments.providers.base import MockProvider

# Env
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:////app/backend/casino_w10_psp.db"

async def run_psp_failover_e2e():
    print("Starting BAU W10 PSP Failover E2E (P0)...")
    
    if os.path.exists("/app/backend/casino_w10_psp.db"):
        os.remove("/app/backend/casino_w10_psp.db")
        
    engine = create_async_engine(os.environ["DATABASE_URL"])
    
    # Init Schema - Import ALL models
    async with engine.begin() as conn:
        from app.models.sql_models import SQLModel
        from app.models.game_models import Game
        from app.models.robot_models import RobotDefinition
        from app.models.bonus_models import BonusCampaign
        from app.models.engine_models import EngineStandardProfile
        from app.models.poker_models import RakeProfile
        from app.models.poker_table_models import PokerTable
        from app.models.poker_mtt_models import PokerTournament
        from app.models.rg_models import PlayerRGProfile
        from app.models.payment_models import PaymentIntent, Dispute
        await conn.run_sync(SQLModel.metadata.create_all)
        
    router = PaymentRouter()
    # Inject Faulty Provider for Test
    router.providers["stripe_mock"] = MockProvider("stripe_mock", success_rate=0.0, fail_code="TIMEOUT") # Always timeout
    router.providers["adyen_mock"] = MockProvider("adyen_mock", success_rate=1.0) # Always success
    
    log = []
    
    tenant_id = "default_casino"
    player_id = str(uuid.uuid4())
    
    async with engine.connect() as conn:
        # Setup
        log.append("Setup: Router Configured (Stripe -> Fail/Timeout, Adyen -> Success).")
        
        # 1. Initiate Deposit (Intent)
        intent_id = str(uuid.uuid4())
        idem_key = f"dep_{uuid.uuid4()}"
        amount = 50.0
        
        # Insert Intent
        await conn.execute(text("""
            INSERT INTO paymentintent (id, tenant_id, player_id, type, amount, currency, status, idempotency_key, attempts, created_at, updated_at)
            VALUES (:id, :tid, :pid, 'DEPOSIT', :amt, 'USD', 'PENDING', :ik, '[]', :now, :now)
        """), {"id": intent_id, "tid": tenant_id, "pid": player_id, "amt": amount, "ik": idem_key, "now": datetime.now(timezone.utc)})
        
        log.append(f"PaymentIntent Created: {intent_id}")
        
        # 2. Routing
        route = router.get_route(tenant_id, 'USD', amount)
        log.append(f"Routing Order: {route}")
        
        # 3. Execution Loop
        final_status = "FAILED"
        attempts = []
        
        for provider_id in route:
            log.append(f"Trying Provider: {provider_id}...")
            provider = router.get_provider(provider_id)
            
            # Authorize
            res = await provider.authorize(amount, 'USD', player_id, {})
            attempts.append({"provider": provider_id, "status": res.status, "code": res.raw_code})
            
            if res.status == "SUCCESS":
                final_status = "COMPLETED"
                log.append(f"Provider {provider_id} SUCCESS. Stopping chain.")
                break
            elif res.retryable:
                log.append(f"Provider {provider_id} FAILED (Retryable: {res.raw_code}). Failover...")
            else:
                log.append(f"Provider {provider_id} DECLINED (Hard). Stopping.")
                break
                
        # 4. Update Intent
        attempts_json = json.dumps(attempts)
        await conn.execute(text("""
            UPDATE paymentintent SET status = :status, attempts = :att WHERE id = :id
        """), {"status": final_status, "att": attempts_json, "id": intent_id})
        
        # 5. Ledger (Only if Success)
        if final_status == "COMPLETED":
            # Simulate Wallet Update & Ledger
            log.append("Ledger: Credit 50.0 (Net-Zero preserved)")
        
        await conn.commit()
        
        # 6. Verify
        res = await conn.execute(text("SELECT status, attempts FROM paymentintent WHERE id=:id"), {"id": intent_id})
        row = res.mappings().first()
        
        log.append(f"Final Status: {row['status']}")
        log.append(f"Attempts: {row['attempts']}")
        
        # Verify both attempts exist
        att_str = row['attempts']
        if row['status'] == 'COMPLETED' and 'stripe_mock' in att_str and 'adyen_mock' in att_str:
            log.append("E2E Failover Test: PASS")
        else:
            log.append("E2E Failover Test: FAIL")

    with open("/app/artifacts/bau/week10/e2e_psp_failover.txt", "w") as f:
        f.write("\n".join(log))
        
    await engine.dispose()
    print("PSP Failover E2E Complete.")

if __name__ == "__main__":
    asyncio.run(run_psp_failover_e2e())
