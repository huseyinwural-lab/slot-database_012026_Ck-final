import os
import asyncio
from sqlmodel import select, desc
from datetime import datetime, timedelta, timezone
from app.core.database import async_session
from app.models.sql_models import Transaction, PayoutAttempt

# --- Configuration ---
STUCK_THRESHOLD_MINUTES = 30
STUCK_STATES = {"pending_provider", "payout_submitted", "processing"}

async def detect_stuck_finance_jobs():
    print(f"=== Finance Stuck Job Detector ===")
    print(f"Time: {datetime.utcnow().isoformat()}")
    print(f"Threshold: {STUCK_THRESHOLD_MINUTES} minutes\n")

    cutoff = datetime.utcnow() - timedelta(minutes=STUCK_THRESHOLD_MINUTES)
    
    async with async_session() as session:
        # 1. Stuck Transactions
        # Transactions that are in intermediate state for too long
        stmt = select(Transaction).where(
            Transaction.state.in_(STUCK_STATES),
            Transaction.updated_at < cutoff
        ).order_by(Transaction.updated_at)
        
        txs = (await session.execute(stmt)).scalars().all()
        
        if not txs:
            print("[OK] No stuck transactions found.")
        else:
            print(f"[WARN] Found {len(txs)} stuck transactions:")
            for tx in txs:
                duration = datetime.utcnow() - (tx.updated_at or tx.created_at)
                print(f"  - TX {tx.id} | Type: {tx.type} | State: {tx.state} | Stuck for: {duration}")

        # 2. Stuck Payout Attempts
        # Attempts sent to PSP but no final status
        stmt_pa = select(PayoutAttempt).where(
            PayoutAttempt.status == "pending",
            PayoutAttempt.created_at < cutoff
        ).order_by(PayoutAttempt.created_at)
        
        attempts = (await session.execute(stmt_pa)).scalars().all()
        
        if not attempts:
            print("\n[OK] No stuck payout attempts found.")
        else:
            print(f"\n[WARN] Found {len(attempts)} stuck payout attempts:")
            for pa in attempts:
                duration = datetime.utcnow() - pa.created_at
                print(f"  - Attempt {pa.id} | TX: {pa.withdraw_tx_id} | Stuck for: {duration}")

        if not txs and not attempts:
            return 0
        else:
            return 1

if __name__ == "__main__":
    # Ensure env is loaded or defaults work
    asyncio.run(detect_stuck_finance_jobs())
