import asyncio
import uuid
import httpx
import os
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
    print(f"{GREEN}=== BAU W14 COLLUSION RISK RUNNER ==={RESET}")
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
