import asyncio
import sys
from datetime import datetime, timedelta
from sqlmodel import select
from app.core.database import async_session
from app.models.sql_models import Transaction, AuditEvent
from app.services.wallet_ledger import apply_wallet_delta_with_ledger
from app.services.audit import audit

# Configuration
EXPIRY_HOURS = 24

async def process_withdraw_expiry():
    print(f"=== Withdraw Expiry Processor ===")
    print(f"Time: {datetime.utcnow().isoformat()}")
    print(f"Threshold: {EXPIRY_HOURS} hours\n")

    cutoff = datetime.utcnow() - timedelta(hours=EXPIRY_HOURS)
    
    async with async_session() as session:
        # Find stuck withdrawals
        stmt = select(Transaction).where(
            Transaction.type == "withdrawal",
            Transaction.state == "requested", # Only requested, not approved/processing
            Transaction.created_at < cutoff
        )
        
        txs = (await session.execute(stmt)).scalars().all()
        
        if not txs:
            print("[OK] No expired withdrawals found.")
            return

        print(f"[ACTION] Found {len(txs)} expired withdrawals. Processing...")
        
        success_count = 0
        fail_count = 0
        
        for tx in txs:
            try:
                print(f"  -> Expiring TX {tx.id} (Amount: {tx.amount})")
                
                # 1. Reverse Ledger (Held -> Available)
                # We simply refund the held amount.
                # delta_available = +amount
                # delta_held = -amount
                
                applied = await apply_wallet_delta_with_ledger(
                    session,
                    tenant_id=tx.tenant_id,
                    player_id=tx.player_id,
                    tx_id=tx.id,
                    event_type="withdraw_expired",
                    delta_available=float(tx.amount),
                    delta_held=-float(tx.amount),
                    currency=tx.currency,
                    idempotency_key=f"expire-{tx.id}"
                )
                
                if applied:
                    # 2. Update Transaction State
                    tx.state = "expired"
                    tx.status = "expired" # or failed
                    tx.updated_at = datetime.utcnow()
                    session.add(tx)
                    
                    # 3. Audit Log
                    # We can use audit service or create manually. 
                    # Audit service usually needs request context, but we can fake it or pass None.
                    # Looking at audit.log_event signature: 
                    # log_event(session, request_id, actor_user_id, tenant_id, action, ...)
                    
                    await audit.log_event(
                        session=session,
                        request_id="system-expiry-job",
                        actor_user_id="system",
                        tenant_id=tx.tenant_id,
                        action="FIN_WITHDRAW_EXPIRED",
                        resource_type="transaction",
                        resource_id=tx.id,
                        result="success",
                        details={
                            "reason": "auto_expiry_24h",
                            "original_created_at": tx.created_at.isoformat()
                        }
                    )
                    
                    await session.commit()
                    print(f"     [PASS] TX {tx.id} expired and refunded.")
                    success_count += 1
                else:
                    print(f"     [SKIP] Idempotency hit for TX {tx.id}.")
                    
            except Exception as e:
                print(f"     [FAIL] Error expiring TX {tx.id}: {e}")
                await session.rollback()
                fail_count += 1
                
        print(f"\nResult: {success_count} Success, {fail_count} Failed.")

if __name__ == "__main__":
    asyncio.run(process_withdraw_expiry())
