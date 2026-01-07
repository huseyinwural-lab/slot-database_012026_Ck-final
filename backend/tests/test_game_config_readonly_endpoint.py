import pytest


@pytest.mark.asyncio
async def test_game_config_readonly_endpoint_returns_min_payload(client, session, admin_token):
    from app.models.game_models import Game
    from sqlmodel import select

    # Seed a game (SQLModel table)
    g = Game(
        tenant_id="default_casino",
        provider_id="mock",
        external_id="g-readonly",
        name="Game 1",
        provider="mock",
        category="slot",
        status="active",
        configuration={},
    )
    session.add(g)
    await session.commit()
    await session.refresh(g)

    res = await client.get(
        f"/api/v1/games/{g.id}/config",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    body = res.json()

    # Minimum payload contract
    assert body["game_id"] == g.id
    assert body["name"] == "Game 1"
    assert body["provider"]
    assert body["category"] == "slot"
    assert "status" in body
    assert body["rtp"] is None
    assert body["volatility"] is None
    assert body["limits"] is None
    assert isinstance(body["features"], list)
    assert body["is_read_only"] is True
