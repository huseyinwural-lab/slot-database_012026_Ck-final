import pytest
from httpx import AsyncClient
from app.models.robot_models import RobotDefinition

@pytest.mark.asyncio
async def test_toggle_robot_missing_reason_fails(client: AsyncClient, admin_token, session):
    # Setup
    robot = RobotDefinition(name="No Reason Bot", config={}, config_hash="dummy_hash_fail_1", is_active=False)
    session.add(robot)
    await session.commit()
    
    headers = {"Authorization": f"Bearer {admin_token}"} # No X-Reason
    
    # Attempt Toggle
    resp = await client.post(f"/api/v1/robots/{robot.id}/toggle", headers=headers)
    
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "REASON_REQUIRED"

@pytest.mark.asyncio
async def test_clone_robot_missing_reason_fails(client: AsyncClient, admin_token, session):
    robot = RobotDefinition(name="No Reason Clone", config={}, config_hash="dummy_hash_fail_2", is_active=True)
    session.add(robot)
    await session.commit()
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {"name_suffix": " (Fail)"} # No reason in body
    
    resp = await client.post(f"/api/v1/robots/{robot.id}/clone", json=payload, headers=headers)
    
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "REASON_REQUIRED"
