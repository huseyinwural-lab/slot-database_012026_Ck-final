import pytest
from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient
import hmac
import hashlib
import time
from unittest.mock import patch

from app.routes.integrations.security.hmac import verify_hmac_signature


@pytest.mark.asyncio
async def test_generic_hmac_verification_success():
    app = FastAPI()

    secret = "test-secret"

    @app.post("/cb")
    async def cb(request: Request):
        # read body first so request._body is populated
        await request.body()
        verify_hmac_signature(request, secret, header_prefix="X")
        return {"ok": True}

    body = b"{\"hello\":\"world\"}"
    ts = str(int(time.time()))
    msg = f"{ts}.".encode("utf-8") + body
    sig = hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()

    with patch("config.settings.webhook_signature_enforced", True):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/cb",
                content=body,
                headers={"X-Signature": sig, "X-Timestamp": ts},
            )
            assert resp.status_code == 200


@pytest.mark.asyncio
async def test_generic_hmac_verification_failure():
    app = FastAPI()

    secret = "test-secret"

    @app.post("/cb")
    async def cb(request: Request):
        await request.body()
        verify_hmac_signature(request, secret, header_prefix="X")
        return {"ok": True}

    body = b"{\"hello\":\"world\"}"
    ts = str(int(time.time()))

    with patch("config.settings.webhook_signature_enforced", True):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/cb",
                content=body,
                headers={"X-Signature": "deadbeef", "X-Timestamp": ts},
            )
            assert resp.status_code == 401
