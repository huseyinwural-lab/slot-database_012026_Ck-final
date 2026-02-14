import pytest


@pytest.mark.asyncio
async def test_games_domain_unauthorized_is_wrapped(client):
    res = await client.get("/api/v1/games?page=1&page_size=1")
    assert res.status_code == 401
    body = res.json()
    assert body["error_code"] == "UNAUTHORIZED"
    assert "message" in body
    assert "details" in body


@pytest.mark.asyncio
async def test_games_missing_route_is_normalized_to_feature_not_implemented(client, admin_token):
    # This route does not exist in the backend; FastAPI would normally return 404.
    res = await client.post(
        "/api/v1/games/00000000-0000-0000-0000-000000000000/toggle",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 501
    body = res.json()
    assert body["error_code"] == "FEATURE_NOT_IMPLEMENTED"


@pytest.mark.asyncio
async def test_games_config_missing_is_game_config_not_found(client, session, admin_token):
    # For config we want deterministic resource-level 404
    res = await client.get(
        "/api/v1/games/00000000-0000-0000-0000-000000000000/config",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 404
    body = res.json()
    assert body["error_code"] == "GAME_CONFIG_NOT_FOUND"


@pytest.mark.asyncio
async def test_non_games_paths_are_not_wrapped(client):
    # Regression guard: ensure non-games paths keep legacy FastAPI error shapes
    res = await client.get("/api/v1/finance/transactions")
    assert res.status_code == 401
    body = res.json()
    assert "error_code" not in body
    assert body.get("detail") == "Not authenticated"
