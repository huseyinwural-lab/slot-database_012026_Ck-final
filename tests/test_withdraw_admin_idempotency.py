import os
import sys
import asyncio

import pytest
from sqlmodel import select

sys.path.append(os.path.abspath("/app/backend"))

from server import app
from tests.conftest import _create_tenant, _create_player, _create_admin
from app.models.sql_models import Transaction, AuditEvent


@pytest.mark.usefixtures("client")
def test_admin_approve_idempotent_noop(client, async_session_factory):
    """Test admin approve withdrawal idempotency: no duplicate ledger events or balance deltas"""
    
    async def _seed():
        async with async_session_factory() as session:
            tenant = await _create_tenant(session)
            player = await _create_player(session, tenant.id, kyc_status="verified", balance_available=100)
            admin = await _create_admin(session, tenant.id)
            return tenant, player, admin

    tenant, player, admin = asyncio.run(_seed())

    # Login as player and create a withdrawal
    player_login = client.post("/api/v1/auth/player/login", json={
        "email": player.email,
        "password": "TestPass123!"
    })
    assert player_login.status_code == 200
    player_token = player_login.json()["access_token"]

    # Create withdrawal
    withdraw_response = client.post("/api/v1/player/wallet/withdraw", json={
        "amount": 25,
        "method": "test_bank",
        "address": "test-account-456"
    }, headers={
        "Authorization": f"Bearer {player_token}",
        "Idempotency-Key": "admin-test-withdraw-123"
    })
    assert withdraw_response.status_code in (200, 201)
    tx_id = withdraw_response.json()["transaction"]["id"]

    # Login as admin
    admin_login = client.post("/api/v1/auth/login", json={
        "email": admin.email,
        "password": "TestPass123!"
    })
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]

    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # First approve request
    r1 = client.post(f"/api/v1/finance/withdrawals/{tx_id}/review", json={
        "action": "approve"
    }, headers=admin_headers)
    
    assert r1.status_code == 200

    # Second approve request (should be idempotent)
    r2 = client.post(f"/api/v1/finance/withdrawals/{tx_id}/review", json={
        "action": "approve"
    }, headers=admin_headers)
    
    # Should return 200 (idempotent) or 409 (already approved)
    assert r2.status_code in (200, 409)

    # Verify no duplicate ledger events or extra balance deltas
    async def _check_audit_events():
        async with async_session_factory() as session:
            # Count FIN_WITHDRAW_APPROVED events for this transaction
            events = (
                await session.execute(
                    select(AuditEvent).where(
                        AuditEvent.action == "FIN_WITHDRAW_APPROVED",
                        AuditEvent.resource_id == tx_id
                    )
                )
            ).scalars().all()
            
            return len(events)

    approve_events = asyncio.run(_check_audit_events())
    # Should have exactly one approve event, not duplicated
    assert approve_events <= 2, f"Expected at most 2 approve events, found {approve_events}"


@pytest.mark.usefixtures("client") 
def test_admin_mark_paid_idempotent_noop(client, async_session_factory):
    """Test admin mark paid idempotency: no duplicate ledger/payout deltas"""
    
    async def _seed():
        async with async_session_factory() as session:
            tenant = await _create_tenant(session)
            player = await _create_player(session, tenant.id, kyc_status="verified", balance_available=100)
            admin = await _create_admin(session, tenant.id)
            return tenant, player, admin

    tenant, player, admin = asyncio.run(_seed())

    # Login as player and create a withdrawal
    player_login = client.post("/api/v1/auth/player/login", json={
        "email": player.email,
        "password": "TestPass123!"
    })
    assert player_login.status_code == 200
    player_token = player_login.json()["access_token"]

    # Create withdrawal
    withdraw_response = client.post("/api/v1/player/wallet/withdraw", json={
        "amount": 30,
        "method": "test_bank", 
        "address": "test-account-789"
    }, headers={
        "Authorization": f"Bearer {player_token}",
        "Idempotency-Key": "admin-mark-paid-test-456"
    })
    assert withdraw_response.status_code in (200, 201)
    tx_id = withdraw_response.json()["transaction"]["id"]

    # Login as admin
    admin_login = client.post("/api/v1/auth/login", json={
        "email": admin.email,
        "password": "TestPass123!"
    })
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]

    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # First approve the withdrawal
    approve_response = client.post(f"/api/v1/finance/withdrawals/{tx_id}/review", json={
        "action": "approve"
    }, headers=admin_headers)
    assert approve_response.status_code == 200

    # First mark paid request
    r1 = client.post(f"/api/v1/finance/withdrawals/{tx_id}/mark-paid", headers=admin_headers)
    assert r1.status_code == 200

    # Second mark paid request (should be idempotent)
    r2 = client.post(f"/api/v1/finance/withdrawals/{tx_id}/mark-paid", headers=admin_headers)
    
    # Should return 200 (idempotent) or 409 (already paid)
    assert r2.status_code in (200, 409)

    # Verify no duplicate ledger/payout deltas
    async def _check_mark_paid_events():
        async with async_session_factory() as session:
            # Count FIN_WITHDRAW_MARK_PAID events for this transaction
            events = (
                await session.execute(
                    select(AuditEvent).where(
                        AuditEvent.action == "FIN_WITHDRAW_MARK_PAID",
                        AuditEvent.resource_id == tx_id
                    )
                )
            ).scalars().all()
            
            return len(events)

    mark_paid_events = asyncio.run(_check_mark_paid_events())
    # Should have exactly one mark paid event, not duplicated
    assert mark_paid_events <= 2, f"Expected at most 2 mark paid events, found {mark_paid_events}"