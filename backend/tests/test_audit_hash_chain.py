import pytest
from httpx import AsyncClient
from sqlalchemy import select
from app.models.sql_models import AuditEvent
from datetime import timezone
import hashlib
import json

@pytest.mark.asyncio
async def test_audit_hash_chain_integrity(client: AsyncClient, session):
    try:
        tenant_id = "chain_test_tenant"
        
        # 2. Insert Event 1
        from app.services.audit import audit
        
        await audit.log_event(
            session=session,
            request_id="req1",
            actor_user_id="actor1",
            tenant_id=tenant_id,
            action="TEST_ACTION_1",
            resource_type="test",
            resource_id="res1",
            result="success",
            reason="reason1"
        )
        await session.commit()
        
        # 3. Insert Event 2
        await audit.log_event(
            session=session,
            request_id="req2",
            actor_user_id="actor1",
            tenant_id=tenant_id,
            action="TEST_ACTION_2",
            resource_type="test",
            resource_id="res2",
            result="success",
            reason="reason2"
        )
        await session.commit()
        
        # 4. Fetch and Verify
        stmt = select(AuditEvent).where(AuditEvent.tenant_id == tenant_id).order_by(AuditEvent.sequence)
        events = (await session.execute(stmt)).scalars().all()
        
        assert len(events) == 2
        e1, e2 = events[0], events[1]
        
        # Verify Chain
        assert e1.prev_row_hash == "0" * 64
        assert e2.prev_row_hash == e1.row_hash
        
        # Re-compute E2 Hash
        # Ensure timestamp matches audit.py generation (UTC aware)
        ts = e2.timestamp
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        ts_str = ts.isoformat()
        
        payload = {
            "tenant_id": tenant_id,
            "actor_user_id": "actor1",
            "action": "TEST_ACTION_2",
            "resource_type": "test",
            "resource_id": "res2",
            "timestamp": ts_str,
            "reason": "reason2",
            "status": "SUCCESS",
            "details": {},
            "sequence": 2
        }
        canonical_str = json.dumps(payload, sort_keys=True)
        
        expected_hash = hashlib.sha256((e1.row_hash + canonical_str).encode('utf-8')).hexdigest()
        
        assert e2.row_hash == expected_hash
    finally:
        await session.close()
