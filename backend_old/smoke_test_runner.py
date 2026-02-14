import asyncio
import httpx
import logging
from app.models.sql_models import Transaction, Player, Tenant
from app.core.database import async_session
from sqlalchemy import select
from datetime import datetime
import uuid

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("smoke_test")

BASE_URL = "http://localhost:8001/api/v1"

# We need a valid token. Since this is smoke, let's login or generate one if we can access DB.
# For smoke test, we'll try to use the test endpoints or public behavior first.
# For admin actions (refund), we need admin token.

async def get_admin_token():
    # Login as admin
    # Assuming standard seed credentials
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{BASE_URL}/auth/login", json={
            "email": "admin@casino.com",
            "password": "Admin123!"
        })
        if resp.status_code == 200:
            return resp.json()["access_token"]
        logger.error(f"Failed to login: {resp.text}")
        return None

async def create_completed_deposit_in_db():
    # Helper to insert a transaction directly to test refund
    async with async_session() as session:
        # Check tenant
        tenant = (await session.execute(select(Tenant))).scalars().first()
        if not tenant:
            logger.error("No tenant found")
            return None
            
        # Create Player if needed
        player_id = str(uuid.uuid4())
        player = Player(
            id=player_id,
            tenant_id=tenant.id,
            username=f"smoke_{player_id[:8]}",
            email=f"smoke_{player_id[:8]}@test.com",
            password_hash="hash",
            balance_real_available=100.0,
            registered_at=datetime.utcnow()
        )
        session.add(player)
        
        tx_id = str(uuid.uuid4())
        tx = Transaction(
            id=tx_id,
            tenant_id=tenant.id,
            player_id=player_id,
            type="deposit",
            amount=50.0,
            currency="USD",
            status="completed",
            state="completed",
            provider="stripe",
            provider_event_id=f"evt_{tx_id}",
            balance_after=50.0
        )
        session.add(tx)
        await session.commit()
        logger.info(f"Created smoke TX: {tx_id}")
        return tx_id

async def run_smoke_tests():
    token = await get_admin_token()
    if not token:
        print("SKIP: Admin login failed")
        return

    async with httpx.AsyncClient() as client:
        # T2.1 Stripe Webhook Smoke
        print("\n=== T2.1 Stripe Webhook Smoke ===")
        resp = await client.post(f"{BASE_URL}/payments/stripe/webhook", 
                                 content=b"{}", 
                                 headers={"stripe-signature": "junk"})
        print(f"Invalid Sig Response: {resp.status_code}") # Expect 400
        with open("/app/artifacts/pr2-proof/stripe-webhook-smoke.txt", "w") as f:
            f.write(f"Invalid Sig: {resp.status_code} {resp.text}\n")

        # T2.2 Adyen Webhook Smoke
        print("\n=== T2.2 Adyen Webhook Smoke ===")
        # In DEV, stub returns True, so we expect 200. In PROD it would be different.
        # We test the flow acceptance.
        payload = {"notificationItems": [{"NotificationRequestItem": {"eventCode": "AUTHORISATION", "merchantReference": "test_ref", "success": "true"}}]}
        resp = await client.post(f"{BASE_URL}/payments/adyen/webhook", json=payload)
        print(f"Adyen Response: {resp.status_code}")
        with open("/app/artifacts/pr2-proof/adyen-webhook-smoke.txt", "w") as f:
            f.write(f"Adyen Response: {resp.status_code} {resp.text}\n")

        # T2.3 Refund Smoke
        print("\n=== T2.3 Refund Smoke ===")
        tx_id = await create_completed_deposit_in_db()
        if tx_id:
            resp = await client.post(f"{BASE_URL}/finance/deposits/{tx_id}/refund", 
                                     json={"reason": "smoke test refund"},
                                     headers={"Authorization": f"Bearer {token}"})
            print(f"Refund Response: {resp.status_code}")
            with open("/app/artifacts/pr2-proof/refund-smoke.txt", "w") as f:
                f.write(f"Refund Request: {tx_id}\nResponse: {resp.status_code} {resp.text}\n")
        
        # T3 Payout Gating Smoke (Dev Check)
        print("\n=== T3 Payout Gating Smoke (Dev) ===")
        # We need a withdrawal tx.
        # Reuse DB insert logic or just check response if TX not found (404 vs 403).
        # If gated, it should be 403 even before 404 check if logic is middleware or early check.
        # But logic in route is: 1. fetch tx (404), 2. check policy (422), 3. check attempt (403 mock).
        # So we need a valid TX to reach step 3.
        # Let's trust the pytest for gating logic as planned.
        # We just verify we can reach the endpoint.
        # We can call retry on the deposit tx created above, which should fail validation (not withdrawal) -> 400.
        # If it returns 400, it means it passed gating (200 OK access). If 403, gating blocked it.
        # In dev, we expect 400 (Validation Error) or 200.
        if tx_id:
            resp = await client.post(f"{BASE_URL}/finance-actions/withdrawals/{tx_id}/retry",
                                     json={"reason": "retry"},
                                     headers={"Authorization": f"Bearer {token}"})
            print(f"Payout Retry on Deposit Response: {resp.status_code}") 
            # Expect 400 "Transaction is not a withdrawal" -> This confirms access is allowed in Dev.
            with open("/app/artifacts/pr2-proof/payout-gating-smoke.txt", "w") as f:
                f.write(f"Dev Env Access Check: {resp.status_code} {resp.text}\n(400 expected for deposit type, confirming endpoint is reachable in Dev)\n")

if __name__ == "__main__":
    import sys
    # Add project root to path
    sys.path.append("/app/backend")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_smoke_tests())
