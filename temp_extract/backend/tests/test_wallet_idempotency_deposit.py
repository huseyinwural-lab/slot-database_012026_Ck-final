import os
import sys

import pytest

sys.path.append(os.path.abspath("/app/backend"))


@pytest.mark.usefixtures("client", "player_with_token")
def test_deposit_idempotency_same_key_returns_same_tx_and_no_duplicate(client, player_with_token):
    tenant, player, token = player_with_token

    headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": "key-123"}

    # First deposit
    r1 = client.post("/api/v1/player/wallet/deposit", json={"amount": 10, "method": "card"}, headers=headers)
    assert r1.status_code in (200, 201)

    # Second deposit with same key and same payload
    r2 = client.post("/api/v1/player/wallet/deposit", json={"amount": 10, "method": "card"}, headers=headers)
    # Same payload + same key => 200 and same transaction id
    assert r2.status_code == 200
    body1 = r1.json()
    body2 = r2.json()
    assert body2["transaction"]["id"] == body1["transaction"]["id"]

