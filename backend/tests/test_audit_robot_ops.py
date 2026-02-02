import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy import select
from app.models.sql_models import AuditEvent
from app.models.robot_models import RobotDefinition
from app.models.game_models import Game

@pytest.mark.asyncio
async def test_robot_toggle_audit(client: AsyncClient, admin_token, session):
    # 1. Create Robot (Direct DB)
    robot = RobotDefinition(
        name="Audit Test Robot",
        config={"rtp": 96.5},
        config_hash="dummy_hash_1",
        is_active=False
    )
    session.add(robot)
    await session.commit()
    await session.refresh(robot)
    
    # 2. Toggle Robot with Reason
    headers = {"Authorization": f"Bearer {admin_token}", "X-Reason": "End of Quarter maintenance"}
    resp = await client.post(f"/api/v1/robots/{robot.id}/toggle", headers=headers)
    assert resp.status_code == 200
    
    # 3. Verify Audit
    stmt = select(AuditEvent).where(
        AuditEvent.resource_id == str(robot.id),
        AuditEvent.action == "ROBOT_TOGGLE"
    ).order_by(AuditEvent.timestamp.desc())
    
    result = await session.execute(stmt)
    event = result.scalars().first()
    
    assert event is not None
    assert event.reason == "End of Quarter maintenance"
    assert event.status == "SUCCESS"
    assert event.before_json["is_active"] is False
    assert event.after_json["is_active"] is True
    assert event.diff_json["is_active"]["from"] is False
    assert event.diff_json["is_active"]["to"] is True

@pytest.mark.asyncio
async def test_robot_clone_audit(client: AsyncClient, admin_token, session):
    # 1. Create Robot
    original = RobotDefinition(name="Original Robot", config={"rtp": 95}, config_hash="dummy_hash_2", is_active=True)
    session.add(original)
    await session.commit()
    
    # 2. Clone
    payload = {"name_suffix": " (Copy)", "reason": "Scaling up"} # Sending reason in body
    headers = {"Authorization": f"Bearer {admin_token}"}
    resp = await client.post(f"/api/v1/robots/{original.id}/clone", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    new_id = data["id"]
    
    # 3. Verify Audit
    stmt = select(AuditEvent).where(
        AuditEvent.resource_id == new_id,
        AuditEvent.action == "ROBOT_CLONE"
    )
    event = (await session.execute(stmt)).scalars().first()
    
    assert event is not None
    assert event.reason == "Scaling up"
    assert event.metadata_json["original_robot_id"] == str(original.id)
    assert event.after_json["name"] == "Original Robot (Copy)"

@pytest.mark.asyncio
async def test_math_asset_upload_audit(client: AsyncClient, admin_token, session):
    payload = {
        "ref_key": f"asset_audit_{uuid.uuid4().hex}",
        "type": "paytable",
        "content": {"payouts": [1, 2, 3]}
    }
    # Send reason in header to avoid body parsing conflicts with Dict Body
    headers = {"Authorization": f"Bearer {admin_token}", "X-Reason": "New math version"}
    resp = await client.post("/api/v1/math-assets/", json=payload, headers=headers)
    assert resp.status_code == 200
    asset_id = resp.json()["id"]
    
    # Verify Audit
    stmt = select(AuditEvent).where(AuditEvent.resource_id == asset_id)
    event = (await session.execute(stmt)).scalars().first()
    
    assert event.action == "MATH_ASSET_UPLOAD"
    assert event.reason == "New math version"
    assert "hash" in event.metadata_json

@pytest.mark.asyncio
async def test_game_robot_bind_audit(client: AsyncClient, admin_token, session):
    # Setup
    robot = RobotDefinition(name="Binder Bot", config={}, config_hash="dummy_hash_3", is_active=True)
    game = Game(
        name="Bind Game", 
        external_id="bind_game_1", 
        provider="internal",
        provider_id="internal_1", # Fixed: Missing field
        tenant_id="default_casino",
        client_type="html5", 
        provider_game_id="bind_game_1",
        category="slot"
    )
    session.add(robot)
    session.add(game)
    await session.commit()
    
    # Bind
    payload = {"robot_id": str(robot.id), "reason": "Activating new math"}
    headers = {"Authorization": f"Bearer {admin_token}"}
    resp = await client.post(f"/api/v1/games/{game.id}/robot", json=payload, headers=headers)
    assert resp.status_code == 200
    
    # Verify
    stmt = select(AuditEvent).where(
        AuditEvent.resource_id == str(game.id), 
        AuditEvent.action == "GAME_ROBOT_BIND"
    )
    event = (await session.execute(stmt)).scalars().first()
    
    assert event.reason == "Activating new math"
    assert event.after_json["robot_id"] == str(robot.id)
