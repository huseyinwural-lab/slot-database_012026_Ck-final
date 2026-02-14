import pytest


@pytest.mark.asyncio
async def test_games_toggle_endpoint_flips_is_active(client, session, admin_token):
    from app.models.game_models import Game

    # Seed game under same tenant as admin token
    from jose import jwt
    from config import settings

    payload = jwt.decode(admin_token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    tenant_id = payload["tenant_id"]

    g = Game(
        tenant_id=tenant_id,
        provider_id="mock",
        external_id="toggle-1",
        name="Toggle Game",
        provider="mock",
        category="slot",
        status="active",
        is_active=True,
        configuration={},
    )
    session.add(g)
    await session.commit()
    await session.refresh(g)

    res = await client.post(
        f"/api/v1/games/{g.id}/toggle",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["id"] == g.id
    assert body["is_active"] is False
    assert body["business_status"] == "inactive"
    assert body["runtime_status"] == "offline"
