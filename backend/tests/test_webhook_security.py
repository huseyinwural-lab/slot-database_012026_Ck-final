import hmac
import os
import time
from hashlib import sha256

import pytest
from fastapi import status
from httpx import AsyncClient

from server import app
from app.core.database import async_session


@pytest.fixture
async def client():
  async with AsyncClient(app=app, base_url="http://testserver") as c:
    yield c


def sign(body: bytes, ts: int, secret: str) -> str:
  signed_payload = f"{ts}.".encode("utf-8") + body
  mac = hmac.new(secret.encode("utf-8"), signed_payload, sha256)
  return mac.hexdigest()


@pytest.fixture(autouse=True)
def _set_webhook_secret(monkeypatch):
  monkeypatch.setenv("WEBHOOK_SECRET", "test_webhook_secret")


def test_webhook_missing_signature_headers_returns_400():
  payload = {
    "provider": "mockpsp",
    "provider_event_id": "evt_1",
    "withdraw_tx_id": "nonexistent",
    "status": "paid",
    "error_code": None,
    "provider_ref": None,
  }

  # No timestamp/signature headers
  res = client.post("/api/v1/finance/withdrawals/payout/webhook", json=payload)
  assert res.status_code == status.HTTP_400_BAD_REQUEST
  body = res.json()
  assert body["detail"]["error_code"] == "WEBHOOK_SIGNATURE_MISSING"


def test_webhook_invalid_signature_returns_401():
  payload = {
    "provider": "mockpsp",
    "provider_event_id": "evt_2",
    "withdraw_tx_id": "nonexistent",
    "status": "paid",
    "error_code": None,
    "provider_ref": None,
  }
  body_bytes = client._encode_json(payload, "utf-8")  # type: ignore[attr-defined]
  ts = int(time.time())

  # Use wrong secret so that signature does not match
  wrong_sig = sign(body_bytes, ts, "other_secret")

  res = client.post(
    "/api/v1/finance/withdrawals/payout/webhook",
    json=payload,
    headers={
      "X-Webhook-Timestamp": str(ts),
      "X-Webhook-Signature": wrong_sig,
    },
  )
  assert res.status_code == status.HTTP_401_UNAUTHORIZED
  body = res.json()
  assert body["detail"]["error_code"] == "WEBHOOK_SIGNATURE_INVALID"


def test_webhook_valid_signature_allows_handler_execution():
  payload = {
    "provider": "mockpsp",
    "provider_event_id": "evt_valid",
    "withdraw_tx_id": "nonexistent",
    "status": "paid",
    "error_code": None,
    "provider_ref": None,
  }
  body_bytes = client._encode_json(payload, "utf-8")  # type: ignore[attr-defined]
  ts = int(time.time())

  sig = sign(body_bytes, ts, "test_webhook_secret")

  res = client.post(
    "/api/v1/finance/withdrawals/payout/webhook",
    json=payload,
    headers={
      "X-Webhook-Timestamp": str(ts),
      "X-Webhook-Signature": sig,
    },
  )

  # For unknown withdraw_tx_id, handler returns 200 with orphan flag after
  # verifying signature. We only care that we pass the signature gate here.
  assert res.status_code == status.HTTP_200_OK
  body = res.json()
  assert body.get("orphan") is True
