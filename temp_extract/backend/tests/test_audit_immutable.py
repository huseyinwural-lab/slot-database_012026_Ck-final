import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, OperationalError, IntegrityError

async def apply_triggers(session):
    triggers = [
        """
        CREATE TRIGGER IF NOT EXISTS prevent_audit_update 
        BEFORE UPDATE ON auditevent 
        BEGIN 
            SELECT RAISE(ABORT, 'Audit events are immutable: UPDATE blocked'); 
        END;
        """,
        """
        CREATE TRIGGER IF NOT EXISTS prevent_audit_delete 
        BEFORE DELETE ON auditevent 
        BEGIN 
            SELECT RAISE(ABORT, 'Audit events are immutable: DELETE blocked'); 
        END;
        """
    ]
    for t in triggers:
        await session.execute(text(t))
    await session.commit()

@pytest.mark.asyncio
async def test_audit_immutable_ops_fails(session):
    try:
        await apply_triggers(session)
        
        # 1. Insert Event
        await session.execute(text("""
            INSERT INTO auditevent (id, request_id, actor_user_id, tenant_id, action, resource_type, result, timestamp)
            VALUES ('imm_test_1', 'req1', 'actor1', 'tenant1', 'TEST_ACTION', 'test', 'success', '2025-01-01 10:00:00')
        """))
        await session.commit()
        
        # 2. Attempt Update
        with pytest.raises((DBAPIError, OperationalError, IntegrityError, Exception)) as excinfo:
            await session.execute(text("UPDATE auditevent SET result='tampered' WHERE id='imm_test_1'"))
            await session.commit()
        
        assert "UPDATE blocked" in str(excinfo.value)
        
        # 3. Attempt Delete
        with pytest.raises((DBAPIError, OperationalError, IntegrityError, Exception)) as excinfo:
            await session.execute(text("DELETE FROM auditevent WHERE id='imm_test_1'"))
            await session.commit()
            
        assert "DELETE blocked" in str(excinfo.value)
        
    finally:
        await session.close()
