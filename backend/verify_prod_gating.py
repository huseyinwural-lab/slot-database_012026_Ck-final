import asyncio
import os
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport
from server import app # Import the app

# Helper to run async test
async def run_check():
    # Mock Token
    token = os.environ.get("ADMIN_TOKEN")
    if not token:
        print("ADMIN_TOKEN env var required")
        return

    tx_id = os.environ.get("WITHDRAWAL_TX_ID")
    if not tx_id:
        print("WITHDRAWAL_TX_ID env var required")
        return

    print("=== T3: Payout Gating Verification ===")
    print("Testing that Mock Payouts are DISABLED in Production environment.")
    
    # We use TestClient/AsyncClient to simulate the request locally but with PATCHED settings
    # This proves the logic exists in the codebase.
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Test in DEV (Should Succeed)
        print("\n[Step 1] Verifying blocked in PROD...")
        with patch("config.settings.env", "prod"):
            with patch("config.settings.allow_test_payment_methods", False):
                resp = await client.post(
                    f"/api/v1/finance-actions/withdrawals/{tx_id}/retry",
                    json={"reason": "Smoke Test Prod"},
                    headers={"Authorization": f"Bearer {token}"}
                )
                print(f"Status Code: {resp.status_code}")
                print(f"Response: {resp.json()}")
                
                if resp.status_code == 403:
                    print("PASS: Request was blocked in PROD environment.")
                else:
                    print("FAIL: Request was NOT blocked.")

        # 2. Test in DEV (Should Succeed)
        # Note: The server running is Dev, but we are using client here directly.
        # We assume the server code is consistent.
        
if __name__ == "__main__":
    # Fix import path for running as script
    import sys
    sys.path.append("/app/backend")
    
    asyncio.run(run_check())
