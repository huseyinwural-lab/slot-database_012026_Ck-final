import pytest
from httpx import AsyncClient
from sqlalchemy import text
from app.models.sql_models import AuditEvent

@pytest.mark.asyncio
async def test_audit_immutable_update_fails(session):
    # 1. Insert Event
    # We use raw SQL to bypass SQLAlchemy ORM session mechanics for the update test
    # but use session to insert initial data
    
    # Actually, let's try raw SQL for everything to be sure
    await session.execute(text("""
        INSERT INTO auditevent (id, request_id, actor_user_id, tenant_id, action, resource_type, result, timestamp)
        VALUES ('imm_test_1', 'req1', 'actor1', 'tenant1', 'TEST_ACTION', 'test', 'success', '2025-01-01 10:00:00')
    """))
    await session.commit()
    
    # 2. Attempt Update
    with pytest.raises(Exception) as excinfo:
        await session.execute(text("UPDATE auditevent SET result='tampered' WHERE id='imm_test_1'"))
        await session.commit()
    
    assert "UPDATE blocked" in str(excinfo.value)

@pytest.mark.asyncio
async def test_audit_immutable_delete_fails(session):
    # 1. Insert
    await session.execute(text("""
        INSERT INTO auditevent (id, request_id, actor_user_id, tenant_id, action, resource_type, result, timestamp)
        VALUES ('imm_test_2', 'req2', 'actor1', 'tenant1', 'TEST_ACTION', 'test', 'success', '2025-01-01 10:00:00')
    """))
    await session.commit()
    
    # 2. Attempt Delete
    with pytest.raises(Exception) as excinfo:
        await session.execute(text("DELETE FROM auditevent WHERE id='imm_test_2'"))
        await session.commit()
        
    assert "DELETE blocked" in str(excinfo.value)
