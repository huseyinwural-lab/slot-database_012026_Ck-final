import pytest
from httpx import AsyncClient
from sqlalchemy import select, text
from app.models.sql_models import AuditEvent
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
        
        # Debug Output
        print(f"E1 Hash: {e1.row_hash}")
        print(f"E2 Hash: {e2.row_hash}")
        print(f"E2 Prev: {e2.prev_row_hash}")
        
        # Verify Chain
        assert e1.prev_row_hash == "0" * 64
        assert e2.prev_row_hash == e1.row_hash
        
        # Re-compute E2 Hash
        # Use ISO format with 'Z' if aware, or +00:00. Pydantic/SQLModel output might vary.
        # Let's inspect what e2.timestamp.isoformat() looks like.
        ts_str = e2.timestamp.isoformat()
        if not ts_str.endswith("+00:00") and not ts_str.endswith("Z"):
             # If SQLite stored naive, we might need to adjust.
             # But audit.py used aware UTC.
             pass
             
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
        print(f"Test Canonical Str: {canonical_str}")
        
        expected_hash = hashlib.sha256((e1.row_hash + canonical_str).encode('utf-8')).hexdigest()
        print(f"Test Expected Hash: {expected_hash}")
        
        assert e2.row_hash == expected_hash
    finally:
        await session.close()
