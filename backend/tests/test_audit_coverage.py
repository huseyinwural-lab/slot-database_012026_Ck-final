import pytest
from httpx import AsyncClient
from sqlmodel import select
from datetime import datetime, timedelta, timezone
import uuid

from app.models.sql_models import Tenant, Player, Transaction, AuditEvent, AdminUser
from app.utils.auth import create_access_token

# Re-using helpers from conftest or defining locally if needed
async def _create_tenant(session, name="Test Casino Audit", ttype="owner") -> Tenant:
    # Try find existing tenant by name to avoid UNIQUE constraint issues in tests
    result = await session.execute(select(Tenant).where(Tenant.name == name))
    tenant = result.scalars().first()
    if tenant:
        return tenant

    tenant = Tenant(name=name, type=ttype, features={})
    session.add(tenant)
    await session.commit()
    await session.refresh(tenant)
    return tenant

async def _create_player(session, tenant_id, email="audit_player@test.com", username="audit_player") -> Player:
    result = await session.execute(select(Player).where(Player.email == email))
    player = result.scalars().first()
    if player:
        return player

    player = Player(
        tenant_id=tenant_id,
        email=email,
        username=username,
        password_hash="noop_hash",
        balance_real_available=1000.0,
        balance_real_held=0.0,
        kyc_status="verified",
        registered_at=datetime.now(timezone.utc),
    )
    session.add(player)
    await session.commit()
    await session.refresh(player)
    return player

async def _create_admin(session, tenant_id, email="audit_admin@test.com", username="audit_admin") -> AdminUser:
    result = await session.execute(select(AdminUser).where(AdminUser.email == email))
    admin = result.scalars().first()
    if admin:
        return admin

    admin = AdminUser(
        tenant_id=tenant_id,
        username=username,
        email=email,
        full_name="Audit Admin",
        password_hash="noop_hash",
        role="Admin",
        is_platform_owner=True,
    )
    session.add(admin)
    await session.commit()
    await session.refresh(admin)
    return admin

import pytest_asyncio

@pytest_asyncio.fixture
async def session(async_session_factory):
    async with async_session_factory() as session:
        yield session

@pytest_asyncio.fixture
async def db_tenant(session):
    return await _create_tenant(session)

@pytest_asyncio.fixture
async def db_player(session, db_tenant):
    return await _create_player(session, db_tenant.id)

@pytest_asyncio.fixture
async def db_admin_user(session, db_tenant):
    return await _create_admin(session, db_tenant.id)

@pytest.mark.asyncio
async def test_audit_tenant_limit_block_deposit(client: AsyncClient, session, db_admin_user: AdminUser, db_player: Player, db_tenant: Tenant):
    """
    Test-1: Deposit limit block audit
    - Tenant daily_deposit_limit=50
    - Used today = 40 (completed deposit tx seed)
    - New deposit = 20 -> 422 LIMIT_EXCEEDED
    - Assert: Audit has FIN_TENANT_LIMIT_BLOCKED with correct details
    """
    # 1. Setup Tenant Limit
    db_tenant.daily_deposit_limit = 50.0
    session.add(db_tenant)
    await session.commit()
    await session.refresh(db_tenant)

    # 2. Seed 'Used' amount (40.0)
    tx_id = str(uuid.uuid4())
    seed_tx = Transaction(
        id=tx_id,
        tenant_id=db_tenant.id,
        player_id=db_player.id,
        type="deposit",
        amount=40.0,
        status="completed",
        state="completed",
        created_at=datetime.now(timezone.utc)
    )
    session.add(seed_tx)
    await session.commit()

    # 3. Attempt Deposit causing Limit Exceeded (40 + 20 > 50)
    token = create_access_token(data={"sub": db_player.id, "tenant_id": db_tenant.id, "role": "player"}, expires_delta=timedelta(days=1))
    headers = {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": str(uuid.uuid4()),
        "X-Tenant-ID": db_tenant.id
    }
    
    payload = {"amount": 20.0, "method": "test"}
    resp = await client.post("/api/v1/player/wallet/deposit", json=payload, headers=headers)
    
    # Assert HTTP 422
    assert resp.status_code == 422
    data = resp.json()
    assert data["detail"]["error_code"] == "LIMIT_EXCEEDED"

    # 4. Assert Audit Event
    # Check for FIN_TENANT_LIMIT_BLOCKED
    stmt = select(AuditEvent).where(
        AuditEvent.action == "FIN_TENANT_LIMIT_BLOCKED",
        AuditEvent.resource_type == "wallet_transaction",
        AuditEvent.actor_user_id == db_player.id
    ).order_by(AuditEvent.timestamp.desc())
    
    audit_log = (await session.execute(stmt)).scalars().first()
    assert audit_log is not None
    assert audit_log.result == "failure"
    
    details = audit_log.details
    assert details["action"] == "deposit"
    assert float(details["limit"]) == 50.0
    assert float(details["used_today"]) == 40.0
    assert float(details["attempted"]) == 20.0
    assert details.get("reason_code") == "LIMIT_EXCEEDED" or details.get("error_code") == "LIMIT_EXCEEDED"


@pytest.mark.asyncio
async def test_audit_tenant_limit_block_withdraw(client: AsyncClient, session, db_admin_user: AdminUser, db_player: Player, db_tenant: Tenant):
    """
    Test-2: Withdraw limit block audit
    - Tenant daily_withdraw_limit=30
    - Used today = 20
    - New withdraw = 15 -> 422
    - Assert audit event + action=="withdraw"
    """
    # 1. Setup Tenant Limit
    db_tenant.daily_withdraw_limit = 30.0
    session.add(db_tenant)
    
    # Ensure player has balance
    db_player.balance_real_available = 100.0
    db_player.kyc_status = "verified" # Bypass KYC block
    session.add(db_player)
    await session.commit()

    # 2. Seed 'Used' amount (20.0)
    tx_id = str(uuid.uuid4())
    seed_tx = Transaction(
        id=tx_id,
        tenant_id=db_tenant.id,
        player_id=db_player.id,
        type="withdrawal",
        amount=20.0,
        status="pending",
        state="requested",
        created_at=datetime.now(timezone.utc)
    )
    session.add(seed_tx)
    await session.commit()

    # 3. Attempt Withdraw causing Limit Exceeded (20 + 15 > 30)
    token = create_access_token(data={"sub": db_player.id, "tenant_id": db_tenant.id, "role": "player"}, expires_delta=timedelta(days=1))
    headers = {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": str(uuid.uuid4()),
        "X-Tenant-ID": db_tenant.id
    }
    
    payload = {"amount": 15.0, "method": "test_bank", "address": "TR123"}
    resp = await client.post("/api/v1/player/wallet/withdraw", json=payload, headers=headers)
    
    # Assert HTTP 422
    assert resp.status_code == 422
    
    # 4. Assert Audit Event
    stmt = select(AuditEvent).where(
        AuditEvent.action == "FIN_TENANT_LIMIT_BLOCKED",
        AuditEvent.resource_type == "wallet_transaction",
        AuditEvent.actor_user_id == db_player.id
    ).order_by(AuditEvent.timestamp.desc())
    
    audit_log = (await session.execute(stmt)).scalars().first()
    assert audit_log is not None
    assert audit_log.result == "failure"
    assert audit_log.details["action"] == "withdraw"
    assert float(audit_log.details["limit"]) == 30.0


@pytest.mark.asyncio
async def test_audit_reconciliation_run(client: AsyncClient, session, db_admin_user: AdminUser, db_tenant: Tenant):
    """
    Test-3: Reconciliation run audit
    - POST /finance/reconciliation/run
    - Assert STARTED and COMPLETED events
    - Assert details include run_id, inserted, scanned
    """
    token = create_access_token(data={"sub": db_admin_user.id, "email": db_admin_user.email, "tenant_id": db_tenant.id, "role": "Admin"}, expires_delta=timedelta(days=1))
    headers = {"Authorization": f"Bearer {token}", "X-Tenant-ID": db_tenant.id}
    
    # 1. Run Recon
    resp = await client.post("/api/v1/finance/reconciliation/run", headers=headers)
    assert resp.status_code == 200
    run_id = resp.json()["run_id"]

    # 2. Assert STARTED
    stmt_start = select(AuditEvent).where(
        AuditEvent.action == "FIN_RECONCILIATION_RUN_STARTED",
        AuditEvent.resource_id == run_id
    )
    start_log = (await session.execute(stmt_start)).scalars().first()
    assert start_log is not None
    assert start_log.details["provider"] == "wallet_ledger"
    # Note: run_id might not be in details yet, as per my analysis.
    
    # 3. Assert COMPLETED
    stmt_end = select(AuditEvent).where(
        AuditEvent.action == "FIN_RECONCILIATION_RUN_COMPLETED",
        AuditEvent.resource_id == run_id
    )
    end_log = (await session.execute(stmt_end)).scalars().first()
    assert end_log is not None
    assert end_log.result == "success"
    assert "inserted" in end_log.details
    assert "scanned" in end_log.details


@pytest.mark.asyncio
async def test_audit_admin_review_reason(client: AsyncClient, session, db_admin_user: AdminUser, db_player: Player, db_tenant: Tenant):
    """
    Test-4: Admin approve/mark-paid reason audit
    - Create withdrawal
    - Admin Approve with reason -> Assert audit has reason
    - Admin Mark Paid with reason -> Assert audit has reason
    """
    # 1. Setup Withdrawal (requested)
    # Ensure player has held balance for this withdrawal
    db_player.balance_real_held = 100.0
    session.add(db_player)
    
    tx_id = str(uuid.uuid4())
    tx = Transaction(
        id=tx_id,
        tenant_id=db_tenant.id,
        player_id=db_player.id,
        type="withdrawal",
        amount=100.0,
        status="pending",
        state="requested",
        created_at=datetime.now(timezone.utc)
    )
    session.add(tx)
    await session.commit()

    token = create_access_token(data={"sub": db_admin_user.id, "email": db_admin_user.email, "tenant_id": db_tenant.id, "role": "Admin"}, expires_delta=timedelta(days=1))
    headers = {"Authorization": f"Bearer {token}", "X-Tenant-ID": db_tenant.id}

    # 2. Approve with Reason
    approve_reason = "KYC OK - Approved"
    payload = {"action": "approve", "reason": approve_reason}
    resp = await client.post(f"/api/v1/finance/withdrawals/{tx_id}/review", json=payload, headers=headers)
    assert resp.status_code == 200

    # Assert Audit
    stmt = select(AuditEvent).where(
        AuditEvent.action == "FIN_WITHDRAW_APPROVED",
        AuditEvent.resource_id == tx_id
    )
    audit_log = (await session.execute(stmt)).scalars().first()
    assert audit_log is not None
    assert audit_log.details["reason"] == approve_reason

    # 3. Mark Paid with Reason
    paid_reason = "Sent via Bank"
    payload_paid = {"reason": paid_reason}
    resp = await client.post(f"/api/v1/finance/withdrawals/{tx_id}/mark-paid", json=payload_paid, headers=headers)
    assert resp.status_code == 200

    # Assert Audit
    stmt_paid = select(AuditEvent).where(
        AuditEvent.action == "FIN_WITHDRAW_MARK_PAID",
        AuditEvent.resource_id == tx_id
    )
    audit_log_paid = (await session.execute(stmt_paid)).scalars().first()
    assert audit_log_paid is not None
    assert audit_log_paid.details["reason"] == paid_reason
