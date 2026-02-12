import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func
from app.core.database import async_session
from app.models.sql_models import Transaction
from app.core.metrics import metrics
from app.models.reconciliation_run import ReconciliationReport

# Logging Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("reconciliation_provider")

# Config
DRIFT_THRESHOLD = float(os.getenv("RECON_DRIFT_THRESHOLD", "0.01"))
PROVIDER_ID = "pragmatic"

class ReconciliationEngine:
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def fetch_internal_ledger(self, start_time: datetime, end_time: datetime) -> Dict[str, float]:
        """Aggregate Internal Ledger by Currency and Type."""
        # Note: We group by currency. 
        # In real world, we might group by (currency, type)
        stmt = select(
            Transaction.currency,
            func.sum(Transaction.amount)
        ).where(
            Transaction.provider == PROVIDER_ID,
            Transaction.created_at >= start_time,
            Transaction.created_at < end_time,
            Transaction.state == "completed" # Only settled transactions
        ).group_by(Transaction.currency)
        
        result = await self.session.execute(stmt)
        totals = {}
        for currency, total in result.all():
            totals[currency] = float(total or 0.0)
        return totals

    async def fetch_provider_report(self, start_time: datetime, end_time: datetime) -> Dict[str, float]:
        """
        Mock implementation of fetching external report.
        In Prod: HTTP GET to Provider API or parse CSV from S3.
        """
        # For simulation/test, we assume provider matches internal perfectly usually,
        # unless we inject fault.
        # Logic: 
        # 1. Check if "MOCK_PROVIDER_DRIFT" env var is set.
        # 2. If not, return internal totals (perfect match).
        
        # Simulating a fetch latency
        await asyncio.sleep(0.5)
        
        drift_mode = os.getenv("MOCK_PROVIDER_DRIFT", "0.0")
        drift_amount = float(drift_mode)
        
        # Helper: Peek internal to mirror it + drift
        internal = await self.fetch_internal_ledger(start_time, end_time)
        provider_data = {}
        for cur, val in internal.items():
            provider_data[cur] = val + drift_amount
            
        return provider_data

    async def run(self, date: datetime):
        logger.info(f"Starting Reconciliation for {date.date()}")
        
        start_time = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(days=1)
        
        internal_data = await self.fetch_internal_ledger(start_time, end_time)
        provider_data = await self.fetch_provider_report(start_time, end_time)
        
        drift_found = False
        findings = []
        
        # Compare
        all_currencies = set(internal_data.keys()) | set(provider_data.keys())
        
        for currency in all_currencies:
            internal_val = internal_data.get(currency, 0.0)
            provider_val = provider_data.get(currency, 0.0)
            diff = abs(internal_val - provider_val)
            
            if diff > DRIFT_THRESHOLD:
                drift_found = True
                msg = f"DRIFT DETECTED: {currency} Internal={internal_val} Provider={provider_val} Diff={diff}"
                logger.error(msg)
                findings.append(msg)
                metrics.provider_wallet_drift_detected_total.labels(provider=PROVIDER_ID).inc()
            else:
                logger.info(f"MATCH: {currency} Internal={internal_val} Provider={provider_val}")

        # Persist Report
        # Note: Assuming ReconciliationReport model exists (from earlier handoff or we create it)
        # Using a simplified log for now if model missing, but let's try to save if we have the model
        try:
            report = ReconciliationReport(
                tenant_id="system",
                provider_name=PROVIDER_ID,
                period_start=start_time,
                period_end=end_time,
                total_records=0, # Simplified
                mismatches=len(findings),
                status="failed" if drift_found else "success",
                report_data={"findings": findings}
            )
            self.session.add(report)
            await self.session.commit()
        except Exception as e:
            logger.warning(f"Could not persist report to DB: {e}")

        if drift_found:
            logger.critical("Reconciliation FAILED. Critical Alert Triggered.")
            exit(1)
        else:
            logger.info("Reconciliation SUCCESS.")
            exit(0)

async def main():
    # Use factory to get session
    async with async_session() as session:
        engine = ReconciliationEngine(session)
        # Default to Yesterday
        yesterday = datetime.utcnow() - timedelta(days=1)
        await engine.run(yesterday)

if __name__ == "__main__":
    asyncio.run(main())
