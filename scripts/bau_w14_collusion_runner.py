import asyncio
import uuid
import httpx
import os
import json

# Env
BASE_URL = "http://localhost:8001/api/v1"
ADMIN_EMAIL = "admin@casino.com"
ADMIN_PASS = "Admin123!"

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

async def main():
    print(f"{GREEN}=== BAU W14 COLLUSION RISK RUNNER ==={RESET}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Login Admin
        print(f"-> Logging in Admin...")
        resp = await client.post(f"{BASE_URL}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}", "X-Reason": "BAU_W14_TEST"}
        
        # 2. Simulate Flagging
        print(f"-> Flagging Player Manual...")
        fake_player_id = str(uuid.uuid4())
        flag_data = {"reason": "Suspicious play patterns in Hand #123"}
        resp = await client.post(f"{BASE_URL}/admin/risk/players/{fake_player_id}/flag", json=flag_data, headers=headers)
        if resp.status_code != 200:
             print(f"{RED}Flag Failed: {resp.text}{RESET}")
             return
        signal = resp.json()
        print(f"{GREEN}   Signal Created: {signal['id']} ({signal['signal_type']}){RESET}")
        
        # 3. Verify Signal List
        print(f"-> Verifying Signal List...")
        resp = await client.get(f"{BASE_URL}/admin/risk/signals?type=MANUAL_FLAG", headers=headers)
        signals = resp.json()
        found = any(s["id"] == signal["id"] for s in signals)
        
        if found:
            print(f"{GREEN}   [PASS] Signal found in registry{RESET}")
        else:
            print(f"{RED}   [FAIL] Signal not found{RESET}")

    print(f"{GREEN}=== RUN COMPLETE ==={RESET}")

if __name__ == "__main__":
    asyncio.run(main())
