import asyncio
from sqlmodel import select, func
from datetime import datetime, timedelta
from app.core.database import async_session
from app.models.sql_models import Transaction, Player

async def daily_reconciliation_report():
    print(f"=== Daily Reconciliation Report ===")
    now = datetime.utcnow()
    yesterday = now - timedelta(days=1)
    print(f"Period: {yesterday.date()} to {now.date()}\n")
    
    async with async_session() as session:
        # 1. Total Volume
        stmt_vol = select(
            Transaction.type, 
            func.count(Transaction.id), 
            func.sum(Transaction.amount)
        ).where(
            Transaction.created_at >= yesterday
        ).group_by(Transaction.type)
        
        results = (await session.execute(stmt_vol)).all()
        
        print("--- Volume Summary ---")
        for type_, count, amount in results:
            print(f"{type_.ljust(15)}: {str(count).rjust(5)} txs | Total: {amount or 0.0}")

        # 2. Mismatch Detector (Simple)
        # Check if completed/paid transactions have consistent ledger impact?
        # Ideally we compare `balance_after` with recalculated ledger.
        # Here we just flag failed payouts that might have held funds.
        
        print("\n--- Risk / Exception Check ---")
        
        # Failed Payouts (Should check if funds returned)
        stmt_fail = select(Transaction).where(
            Transaction.type == "withdrawal",
            Transaction.state == "payout_failed",
            Transaction.updated_at >= yesterday
        )
        failed_txs = (await session.execute(stmt_fail)).scalars().all()
        
        if failed_txs:
            print(f"[WARN] {len(failed_txs)} Failed Payouts found. Verify funds returned:")
            for tx in failed_txs:
                print(f"  - TX {tx.id} | Amount: {tx.amount}")
        else:
            print("[OK] No failed payouts in window.")

        # Pending Deposits (Stuck?)
        stmt_dep = select(Transaction).where(
            Transaction.type == "deposit",
            Transaction.state == "pending_provider",
            Transaction.created_at < (now - timedelta(hours=1)) # Older than 1h
        )
        stuck_deps = (await session.execute(stmt_dep)).scalars().all()
        
        if stuck_deps:
            print(f"[WARN] {len(stuck_deps)} Deposits pending provider > 1h.")
        else:
            print("[OK] No stuck deposits.")

if __name__ == "__main__":
    asyncio.run(daily_reconciliation_report())
