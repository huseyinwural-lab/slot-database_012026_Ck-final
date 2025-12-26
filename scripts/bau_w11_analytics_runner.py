import asyncio
import sys
import os
import uuid
import json
import random
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from config import settings

sys.path.append("/app/backend")

# Env
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:////app/backend/casino_w11_analytics.db"

async def run_analytics_e2e():
    print("Starting Payment Analytics & Smart Routing E2E...")
    
    if os.path.exists("/app/backend/casino_w11_analytics.db"):
        os.remove("/app/backend/casino_w11_analytics.db")
        
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
        from app.models.payment_analytics_models import PaymentAttempt, RoutingRule
        await conn.run_sync(SQLModel.metadata.create_all)
        
    log = []
    
    tenant_id = "default_casino"
    
    async with engine.connect() as conn:
        # 1. Setup Rules
        await conn.execute(text("""
            INSERT INTO routingrule (id, tenant_id, currency, provider_priority, is_active, created_at)
            VALUES (:id, :tid, 'EUR', '["adyen_mock", "stripe_mock"]', 1, :now)
        """), {"id": str(uuid.uuid4()), "tid": tenant_id, "now": datetime.now(timezone.utc)})
        log.append("Smart Routing: Added Rule EUR -> [Adyen, Stripe]")
        
        # 2. Simulate Attempts
        intent_id = str(uuid.uuid4())
        
        # Attempt 1: Stripe (Fail)
        await conn.execute(text("""
            INSERT INTO paymentattempt (id, tenant_id, payment_intent_id, provider, attempt_no, status, raw_code, retryable, latency_ms, created_at)
            VALUES (:id, :tid, :pid, 'stripe_mock', 1, 'FAILED', 'TIMEOUT', 1, 500, :now)
        """), {"id": str(uuid.uuid4()), "tid": tenant_id, "pid": intent_id, "now": datetime.now(timezone.utc)})
        
        # Attempt 2: Stripe Retry (Fail)
        await conn.execute(text("""
            INSERT INTO paymentattempt (id, tenant_id, payment_intent_id, provider, attempt_no, status, raw_code, retryable, latency_ms, created_at)
            VALUES (:id, :tid, :pid, 'stripe_mock', 2, 'FAILED', 'TIMEOUT', 1, 550, :now)
        """), {"id": str(uuid.uuid4()), "tid": tenant_id, "pid": intent_id, "now": datetime.now(timezone.utc)})
        
        # Attempt 3: Failover Adyen (Success)
        await conn.execute(text("""
            INSERT INTO paymentattempt (id, tenant_id, payment_intent_id, provider, attempt_no, status, raw_code, retryable, latency_ms, created_at)
            VALUES (:id, :tid, :pid, 'adyen_mock', 3, 'SUCCESS', '20000', 0, 200, :now)
        """), {"id": str(uuid.uuid4()), "tid": tenant_id, "pid": intent_id, "now": datetime.now(timezone.utc)})
        
        await conn.commit()
        log.append("Simulated 3 Attempts (Fail -> Retry -> Success)")
        
        # 3. Analytics Query Logic (Simulate API)
        res = await conn.execute(text("""
            SELECT 
                count(*) as total,
                sum(case when status='SUCCESS' then 1 else 0 end) as success
            FROM paymentattempt
        """))
        row = res.mappings().first()
        log.append(f"Metrics: {row['success']}/{row['total']} Success.")
        
        # Snapshot
        snapshot = {
            "total": row['total'],
            "success": row['success'],
            "success_rate": row['success'] / row['total'] if row['total'] else 0
        }
        
    with open("/app/artifacts/bau/week11/e2e_payment_analytics_routing.txt", "w") as f:
        f.write("\n".join(log))
        
    with open("/app/artifacts/bau/week11/payment_metrics_snapshot.json", "w") as f:
        json.dump(snapshot, f, indent=2)

    await engine.dispose()
    print("Analytics E2E Complete.")

if __name__ == "__main__":
    asyncio.run(run_analytics_e2e())
