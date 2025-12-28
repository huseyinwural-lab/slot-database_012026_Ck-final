import asyncio
import uuid
import httpx
import os
import json
from datetime import datetime

# Import shared utils
try:
    from runner_utils import get_env_config, login_admin_with_retry, get_auth_headers
except ImportError:
    # Fallback for direct execution if not in path
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from runner_utils import get_env_config, login_admin_with_retry, get_auth_headers

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

async def main():
    print(f"{GREEN}=== BAU W12 GROWTH CORE RUNNER ==={RESET}")
    config = get_env_config()
    BASE_URL = config["BASE_URL"]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Login Admin
        try:
            token = await login_admin_with_retry(client)
            headers = get_auth_headers(token)
            headers["X-Reason"] = "BAU_W12_TEST"
        except Exception as e:
            print(f"{RED}Login Failed: {e}{RESET}")
            return

        # 2. Setup Affiliate
        print(f"-> Creating Affiliate...")
        aff_data = {
            "username": f"Partner_{uuid.uuid4().hex[:6]}",
            "email": f"partner_{uuid.uuid4().hex[:6]}@example.com",
            "model": "CPA",
            "cpa_amount": 100.0
        }
        resp = await client.post(f"{BASE_URL}/affiliates", json=aff_data, headers=headers)
        if resp.status_code != 200:
            print(f"{RED}Create Affiliate Failed: {resp.text}{RESET}")
            return
        affiliate = resp.json()
        aff_id = affiliate["id"]
        print(f"{GREEN}   Affiliate Created: {affiliate['username']} ({aff_id}){RESET}")
        
        # 3. Create Tracking Link
        print(f"-> Creating Link...")
        link_code = f"WIN{uuid.uuid4().hex[:4].upper()}"
        link_data = {"code": link_code, "campaign": "Summer25"}
        resp = await client.post(f"{BASE_URL}/affiliates/{aff_id}/links", json=link_data, headers=headers)
        if resp.status_code != 200:
            print(f"{RED}Create Link Failed: {resp.text}{RESET}")
            return
        print(f"{GREEN}   Link Created: {link_code}{RESET}")
        
        # 4. Register Player with Link
        print(f"-> Registering Player with ref_code={link_code}...")
        player_email = f"player_{uuid.uuid4().hex[:6]}@example.com"
        player_data = {
            "email": player_email,
            "username": "NewPlayer",
            "password": "password123",
            "ref_code": link_code
        }
        resp = await client.post(f"{BASE_URL}/auth/player/register", json=player_data)
        if resp.status_code != 200:
            print(f"{RED}Register Failed: {resp.text}{RESET}")
            return
        player_id = resp.json()["player_id"]
        print(f"{GREEN}   Player Registered: {player_id}{RESET}")
        
        # 5. First Deposit (Trigger CPA & CRM)
        print(f"-> Simulating First Deposit ($50)...")
        # Ensure 'deposit_match' bonus campaign exists for CRM trigger test
        camp_data = {
            "name": "Welcome Bonus",
            "type": "deposit_match",
            "config": {"match_percent": 100}
        }
        resp = await client.post(f"{BASE_URL}/bonuses/campaigns", json={"payload": camp_data}, headers=headers)
        if resp.status_code != 200:
             print(f"{RED}Create Campaign Failed: {resp.text}{RESET}")
             return
        camp_id = resp.json()["id"]
        
        # Activate Campaign (Reason required)
        status_data = {"status": "active"}
        resp = await client.post(f"{BASE_URL}/bonuses/campaigns/{camp_id}/status", json=status_data, headers=headers)
        if resp.status_code != 200:
             print(f"{RED}Activate Campaign Failed: {resp.text}{RESET}")
             return
        print(f"{GREEN}   Campaign Activated: {camp_id}{RESET}")

        # Deposit via Webhook (MockPSP)
        webhook_payload = {
            "event_type": "deposit_captured",
            "tenant_id": "default_casino",
            "player_id": player_id,
            "amount": 50.0,
            "currency": "USD",
            "provider": "mockpsp",
            "provider_ref": f"ref_{uuid.uuid4()}",
            "provider_event_id": f"evt_{uuid.uuid4()}",
            "tx_id": f"tx_{uuid.uuid4()}",
            "timestamp": datetime.utcnow().isoformat()
        }
        resp = await client.post(f"{BASE_URL}/payments/webhook/mockpsp", json=webhook_payload)
        if resp.status_code != 200:
             print(f"{RED}Deposit Webhook Failed: {resp.text}{RESET}")
             return
        print(f"{GREEN}   Deposit Processed.{RESET}")
        
        # 6. Verification
        print(f"-> Verifying Results...")
        
        await asyncio.sleep(2) # Wait for async processing if any
        
        resp = await client.get(f"{BASE_URL}/audit/events?resource_type=bonus_grant&action=CRM_OFFER_GRANT", headers=headers)
        events = resp.json().get("items", [])
        
        found_crm = False
        for e in events:
            if e["result"] == "success": 
                found_crm = True
                break
        
        if found_crm:
            print(f"{GREEN}   [PASS] CRM Triggered (Bonus Granted){RESET}")
        else:
            print(f"{RED}   [FAIL] CRM Trigger NOT found in Audit Log{RESET}")

        # Check Affiliate Stats (Link Clicks/Signups)
        resp = await client.get(f"{BASE_URL}/affiliates/{aff_id}/links", headers=headers)
        links = resp.json()
        target_link = next((l for l in links if l["code"] == link_code), None)
        if target_link and target_link["signups"] > 0:
            print(f"{GREEN}   [PASS] Link Signups Incremented: {target_link['signups']}{RESET}")
        else:
            print(f"{RED}   [FAIL] Link Signups NOT Incremented{RESET}")
            
        # 7. Generate Snapshot
        snapshot = {
            "affiliate": affiliate,
            "link": target_link,
            "crm_events_found": found_crm,
            "timestamp": datetime.utcnow().isoformat()
        }
        with open("growth_metrics_snapshot.json", "w") as f:
            json.dump(snapshot, f, indent=2)
        print(f"{GREEN}   Snapshot saved to growth_metrics_snapshot.json{RESET}")

    print(f"{GREEN}=== RUN COMPLETE ==={RESET}")

if __name__ == "__main__":
    asyncio.run(main())
