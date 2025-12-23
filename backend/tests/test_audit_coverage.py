import os
import sys
from decimal import Decimal
import pytest
from sqlalchemy import select, desc

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from server import app  # noqa: E402
from app.models.sql_models import Tenant, AuditEvent, Transaction  # noqa: E402
from app.services.audit import audit  # noqa: E402

@pytest.mark.asyncio
async def test_limit_exceeded_writes_fin_tenant_limit_blocked(client, player_with_token, async_session_factory):
    """
    Test that exceeding tenant daily deposit limit writes a FIN_TENANT_LIMIT_BLOCKED audit event.
    """
    tenant, player, player_token = player_with_token
    
    # 1. Set tenant daily_deposit_limit = 50
    async with async_session_factory() as session:
        db_tenant = await session.get(Tenant, tenant.id)
        assert db_tenant is not None
        db_tenant.daily_deposit_limit = Decimal("50.0")
        session.add(db_tenant)
        await session.commit()

    headers = {"Authorization": f"Bearer {player_token}", "Content-Type": "application/json", "Idempotency-Key": "audit-limit-1"}

    # 2. Seed usage (40.0 deposit)
    async with async_session_factory() as session:
        from app.models.sql_models import Transaction
        from datetime import datetime, timezone
        tx = Transaction(
            tenant_id=tenant.id,
            player_id=player.id,
            type="deposit",
            amount=40.0,
            currency="USD",
            status="completed",
            state="completed",
            method="test",
            idempotency_key="seed-audit-dep-40",
            created_at=datetime.now(timezone.utc),
            balance_after=0.0,
        )
        session.add(tx)
        await session.commit()

    # 3. Attempt deposit of 20.0 (should fail: 40+20 > 50)
    res = await client.post(
        "/api/v1/player/wallet/deposit",
        json={"amount": 20.0, "method": "test"},
        headers=headers,
    )
    assert res.status_code == 422
    
    # 4. Verify audit event
    async with async_session_factory() as session:
        stmt = select(AuditEvent).where(
            AuditEvent.action == "FIN_TENANT_LIMIT_BLOCKED",
            AuditEvent.resource_id == player.id
        ).order_by(desc(AuditEvent.timestamp))
        event = (await session.execute(stmt)).scalars().first()
        
        assert event is not None
        assert event.tenant_id == tenant.id
        assert event.result == "failure"
        assert event.details["error_code"] == "LIMIT_EXCEEDED"
        assert event.details["action"] == "deposit"
        assert event.details["limit"] == 50.0
        assert event.details["scope"] == "tenant_daily"


@pytest.mark.asyncio
async def test_reconciliation_run_writes_started_and_completed(client, admin_token, async_session_factory):
    """
    Test that triggering a reconciliation run writes STARTED and COMPLETED audit events.
    """
    from datetime import date
    today = date.today().isoformat()
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Trigger reconciliation run
    res = await client.post(f"/api/v1/finance/reconciliation/run?date={today}", headers=headers)
    assert res.status_code == 200
    data = res.json()
    run_id = data["run_id"]

    # 2. Verify audit events
    async with async_session_factory() as session:
        # Check STARTED
        stmt_started = select(AuditEvent).where(
            AuditEvent.action == "FIN_RECONCILIATION_RUN_STARTED",
            AuditEvent.resource_id == run_id
        )
        started = (await session.execute(stmt_started)).scalars().first()
        assert started is not None
        assert started.result == "started"
        assert started.tenant_id is not None # Should be admin's tenant or system tenant, not null

        # Check COMPLETED
        stmt_completed = select(AuditEvent).where(
            AuditEvent.action == "FIN_RECONCILIATION_RUN_COMPLETED",
            AuditEvent.resource_id == run_id
        )
        completed = (await session.execute(stmt_completed)).scalars().first()
        assert completed is not None
        assert completed.result == "success"
        assert "inserted" in completed.details
        assert "scanned" in completed.details


@pytest.mark.asyncio
async def test_admin_review_reason_persisted_in_audit_details(client, admin_token, async_session_factory):
    """
    Test that admin approve/reject/mark-paid actions persist the 'reason' in audit details.
    """
    # 1. Setup: Create a player and a withdrawal request
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Create player via direct DB injection or API if easier. Let's use DB to be fast.
    # Actually need a player to create withdrawal.
    # We can reuse 'client' but we need a player token to request withdrawal OR inject tx directly.
    # Let's inject a withdrawal directly into DB.
    
    from app.models.sql_models import Player, Transaction
    from datetime import datetime, timezone
    import uuid

    # Need a tenant and player
    # We can fetch the admin's tenant
    async with async_session_factory() as session:
        # Find admin from token (simplified: assume default admin logic or just query any admin)
        # But we need tenant_id. Let's insert a fresh player and tx attached to 'tenant1' (default test fixture tenant?)
        # Better: use `admin_token` which is usually linked to a tenant in conftest.
        # Let's assume we can just query the first admin to get tenant_id
        from app.models.sql_models import AdminUser
        admin = (await session.execute(select(AdminUser))).scalars().first()
        tenant_id = admin.tenant_id
        
        player_id = str(uuid.uuid4())
        player = Player(
            id=player_id,
            tenant_id=tenant_id,
            username="test_audit_player",
            email="audit@player.com",
            password_hash="hash",
            balance_real_available=950.0, # 1000 - 50
            balance_real_held=50.0 # Held amount for the pending withdrawal
        )
        session.add(player)
        
        tx_id = str(uuid.uuid4())
        tx = Transaction(
            id=tx_id,
            tenant_id=tenant_id,
            player_id=player_id,
            type="withdrawal",
            amount=50.0,
            currency="USD",
            state="requested",
            status="pending",
            created_at=datetime.now(timezone.utc)
        )
        session.add(tx)
        await session.commit()

    # 2. Approve with reason
    reason_text = "Audit Reason Test"
    res_approve = await client.post(
        f"/api/v1/finance/withdrawals/{tx_id}/review",
        json={"action": "approve", "reason": reason_text},
        headers=headers
    )
    assert res_approve.status_code == 200

    # 3. Verify audit
    async with async_session_factory() as session:
        stmt = select(AuditEvent).where(
            AuditEvent.action == "FIN_WITHDRAW_APPROVED",
            AuditEvent.resource_id == tx_id
        )
        event = (await session.execute(stmt)).scalars().first()
        assert event is not None
        assert event.details["reason"] == reason_text

    # 4. Mark Paid with reason
    reason_paid = "Paid via Bank"
    res_paid = await client.post(
        f"/api/v1/finance/withdrawals/{tx_id}/mark-paid",
        json={"reason": reason_paid},
        headers=headers
    )
    assert res_paid.status_code == 200

    # 5. Verify audit
    async with async_session_factory() as session:
        stmt = select(AuditEvent).where(
            AuditEvent.action == "FIN_WITHDRAW_MARK_PAID",
            AuditEvent.resource_id == tx_id
        )
        event = (await session.execute(stmt)).scalars().first()
        assert event is not None
        assert event.details["reason"] == reason_paid
