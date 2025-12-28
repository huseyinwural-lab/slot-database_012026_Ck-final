import asyncio
import uuid
import httpx
import os
from datetime import datetime, timedelta
import json

# Import shared utils
try:
    from runner_utils import get_env_config, login_admin_with_retry, get_auth_headers
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from runner_utils import get_env_config, login_admin_with_retry, get_auth_headers

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

async def main():
    print(f"{GREEN}=== BAU W14 MTT LATE REG & RE-ENTRY RUNNER ==={RESET}")
    config = get_env_config()
    BASE_URL = config["BASE_URL"]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Login Admin
        try:
            token = await login_admin_with_retry(client)
            headers = get_auth_headers(token)
            headers["X-Reason"] = "BAU_W14_TEST"
        except Exception as e:
            print(f"{RED}Login Failed: {e}{RESET}")
            return
        
        # 2. Create Tournament with Late Reg
        print(f"-> Creating MTT...")
        mtt_data = {
            "name": "Late Reg Turbo",
            "buy_in": 10.0,
            "fee": 1.0,
            "start_at": (datetime.utcnow() - timedelta(minutes=5)).isoformat(), # Started 5 mins ago
            "late_reg_until": (datetime.utcnow() + timedelta(minutes=30)).isoformat(),
            "reentry_max": 1,
            "starting_chips": 5000
        }
        resp = await client.post(f"{BASE_URL}/poker/mtt", json=mtt_data, headers=headers)
        if resp.status_code != 200:
             print(f"{RED}Create MTT Failed: {resp.text}{RESET}")
             return
        mtt_id = resp.json()["id"]
        print(f"{GREEN}   MTT Created: {mtt_id}{RESET}")
        
        # Start it (State transition)
        await client.post(f"{BASE_URL}/poker/mtt/{mtt_id}/start", headers=headers)
        
        # 3. Create Player
        print(f"-> Registering Player...")
        player_email = f"mtt_{uuid.uuid4().hex[:6]}@example.com"
        resp = await client.post(f"{BASE_URL}/auth/player/register", json={"email": player_email, "password": "password123", "username": "MttHero"})
        player_id = resp.json()["player_id"]
        
        # Login Player
        resp = await client.post(f"{BASE_URL}/auth/player/login", json={"email": player_email, "password": "password123"})
        p_token = resp.json()["access_token"]
        p_headers = {"Authorization": f"Bearer {p_token}"}
        
        # Fund Player ($100)
        # Mock Deposit
        await client.post(f"{BASE_URL}/payments/webhook/mockpsp", json={
            "event_type": "deposit_captured",
            "tenant_id": "default_casino",
            "player_id": player_id,
            "amount": 100.0,
            "currency": "USD",
            "provider": "mockpsp",
            "provider_event_id": f"evt_{uuid.uuid4()}",
            "tx_id": f"tx_{uuid.uuid4()}"
        })
        
        # 4. Late Registration
        print(f"-> Attempting Late Registration...")
        # Assuming standard register endpoint
        resp = await client.post(f"{BASE_URL}/poker/mtt/{mtt_id}/register", headers=p_headers)
        if resp.status_code != 200:
             print(f"{RED}Register Failed: {resp.text}{RESET}")
             return
        print(f"{GREEN}   [PASS] Registered Successfully (Late Reg){RESET}")
        
        # 5. Simulate Bust (Elimination)
        print(f"-> Simulating Elimination...")
        # Admin marks bust
        bust_data = {"player_id": player_id}
        await client.post(f"{BASE_URL}/poker/mtt/{mtt_id}/eliminate", json=bust_data, headers=headers)
        
        # 6. Re-entry
        print(f"-> Attempting Re-entry 1...")
        resp = await client.post(f"{BASE_URL}/poker/mtt/{mtt_id}/reentry", headers=p_headers)
        if resp.status_code != 200:
             print(f"{RED}Re-entry Failed: {resp.text}{RESET}")
             return
        print(f"{GREEN}   [PASS] Re-entered Successfully{RESET}")
        
        # 7. Simulate Bust Again
        await client.post(f"{BASE_URL}/poker/mtt/{mtt_id}/eliminate", json=bust_data, headers=headers)
        
        # 8. Re-entry 2 (Should Fail - Max 1)
        print(f"-> Attempting Re-entry 2 (Should Fail)...")
        resp = await client.post(f"{BASE_URL}/poker/mtt/{mtt_id}/reentry", headers=p_headers)
        if resp.status_code == 400:
             print(f"{GREEN}   [PASS] Re-entry Blocked (Limit Reached){RESET}")
        else:
             print(f"{RED}   [FAIL] Re-entry Allowed beyond limit! {resp.status_code}{RESET}")

    print(f"{GREEN}=== RUN COMPLETE ==={RESET}")

if __name__ == "__main__":
    asyncio.run(main())
