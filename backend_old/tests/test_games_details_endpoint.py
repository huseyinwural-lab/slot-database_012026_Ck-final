import pytest


@pytest.mark.asyncio
async def test_games_details_endpoint_updates_tags_in_configuration(client, session, admin_token):
    from app.models.game_models import Game
    from jose import jwt
    from config import settings

    payload = jwt.decode(admin_token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    tenant_id = payload["tenant_id"]

    g = Game(
        tenant_id=tenant_id,
        provider_id="mock",
        external_id="details-1",
        name="Details Game",
        provider="mock",
        category="slot",
        status="active",
        is_active=True,
        configuration={},
    )
    session.add(g)
    await session.commit()
    await session.refresh(g)

    res = await client.put(
        f"/api/v1/games/{g.id}/details",
        json={"tags": ["VIP"]},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["id"] == g.id
    assert body["tags"] == ["VIP"]

    # Verify it appears on list endpoint as top-level tags
    lst = await client.get(
        "/api/v1/games?page=1&page_size=50",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert lst.status_code == 200
    items = lst.json().get("items") or []
    target = [x for x in items if x.get("id") == g.id][0]
    assert target.get("tags") == ["VIP"]
