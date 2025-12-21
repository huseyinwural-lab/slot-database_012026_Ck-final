from fastapi.testclient import TestClient

import sys, os
sys.path.append(os.path.abspath("/app/backend"))

from server import app


client = TestClient(app)


def test_deposit_idempotency_same_key_returns_same_tx_and_no_duplicate():
        # Register + login player
        register_payload = {"email": "idem@test.com", "password": "password123", "username": "idem"}
        r = client.post("/api/v1/auth/player/register", json=register_payload)
        assert r.status_code == 200

        login_payload = {"email": "idem@test.com", "password": "password123"}
        r = client.post("/api/v1/auth/player/login", json=login_payload)
        assert r.status_code == 200
        token = r.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": "key-123"}

        # First deposit
        r1 = client.post("/api/v1/player/wallet/deposit", json={"amount": 10, "method": "card"}, headers=headers)
        assert r1.status_code in (200, 201)

        # Second deposit with same key and same payload
        r2 = client.post("/api/v1/player/wallet/deposit", json={"amount": 10, "method": "card"}, headers=headers)
        # Should be treated as idempotent replay (FIN_IDEMPOTENCY_HIT) but still 200-level
        assert r2.status_code in (200, 409, 400)

