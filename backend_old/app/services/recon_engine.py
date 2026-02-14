from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.models.sql_models import ReconciliationReport

class ReconEngine:
    async def run_daily_recon(self, session: AsyncSession, tenant_id: str):
        # 1. Wallet Sum
        res = await session.execute(text("SELECT sum(balance_real) FROM player WHERE tenant_id=:tid"), {"tid": tenant_id})
        wallet_sum = res.scalar() or 0.0
        
        # 2. Ledger Sum
        res = await session.execute(text("SELECT sum(amount) FROM ledgertransaction WHERE tenant_id=:tid AND direction='credit'"), {"tid": tenant_id})
        credit = res.scalar() or 0.0
        res = await session.execute(text("SELECT sum(amount) FROM ledgertransaction WHERE tenant_id=:tid AND direction='debit'"), {"tid": tenant_id})
        debit = res.scalar() or 0.0
        
        ledger_net = credit - debit
        mismatch = wallet_sum - ledger_net
        
        # 3. Report
        report = ReconciliationReport(
            tenant_id=tenant_id,
            provider_name="internal",
            period_start=datetime.now(), # Placeholder
            period_end=datetime.now(),
            mismatches=1 if mismatch != 0 else 0,
            status="completed",
            report_data={"wallet": wallet_sum, "ledger": ledger_net, "diff": mismatch}
        )
        session.add(report)
        return report
