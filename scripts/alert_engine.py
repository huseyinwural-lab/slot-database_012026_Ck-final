import asyncio
import os
import json
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import select, func, text
from app.core.database import engine
from app.models.sql_models import Transaction, AuditEvent
from app.models.poker_mtt_models import RiskSignal
from app.models.reconciliation import ReconciliationFinding

# Configurations
ALERT_LOG_PATH = "/app/artifacts/bau/week18/alerts_test_log.txt"

class AlertEngine:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.alerts = []

    async def run_checks(self):
        print("-> Running Alert Checks...")
        await self.check_payment_success_rate()
        await self.check_reconciliation_mismatches()
        await self.check_risk_spikes()
        
        self.flush_alerts()

    async def check_payment_success_rate(self):
        # Window: Last 15 mins (Simulated as last 24h for test data availability)
        since = datetime.now(timezone.utc) - timedelta(hours=24) 
        
        # Total Attempts
        q_total = select(func.count()).select_from(Transaction).where(Transaction.created_at >= since)
        total = (await self.session.execute(q_total)).scalar() or 0
        
        if total == 0:
            return # No traffic, no alert (or INFO: No Traffic)
            
        # Completed
        q_success = select(func.count()).select_from(Transaction).where(
            Transaction.created_at >= since, 
            Transaction.status == "completed"
        )
        success = (await self.session.execute(q_success)).scalar() or 0
        
        rate = (success / total) * 100
        print(f"   Payment Success Rate: {rate:.2f}% ({success}/{total})")
        
        if rate < 80.0:
            self.alerts.append(f"[CRITICAL] Payment Success Rate Low: {rate:.2f}%")

    async def check_reconciliation_mismatches(self):
        q = select(func.count()).select_from(ReconciliationFinding).where(ReconciliationFinding.status == "OPEN")
        count = (await self.session.execute(q)).scalar() or 0
        
        print(f"   Open Reconciliation Findings: {count}")
        if count > 0:
            self.alerts.append(f"[WARN] Reconciliation Mismatches Found: {count}")

    async def check_risk_spikes(self):
        since = datetime.now(timezone.utc) - timedelta(hours=1)
        q = select(func.count()).select_from(RiskSignal).where(RiskSignal.created_at >= since)
        count = (await self.session.execute(q)).scalar() or 0
        
        print(f"   Risk Signals (1h): {count}")
        if count > 5:
            self.alerts.append(f"[INFO] High Risk Signal Volume: {count}")

    def flush_alerts(self):
        if not self.alerts:
            print("   No Alerts triggered.")
            return

        with open(ALERT_LOG_PATH, "a") as f:
            for alert in self.alerts:
                print(f"   TRIGGERED: {alert}")
                f.write(f"{datetime.now(timezone.utc).isoformat()} {alert}\n")

async def main():
    async with AsyncSession(engine) as session:
        engine_svc = AlertEngine(session)
        await engine_svc.run_checks()

if __name__ == "__main__":
    # Ensure dir exists
    os.makedirs(os.path.dirname(ALERT_LOG_PATH), exist_ok=True)
    asyncio.run(main())
