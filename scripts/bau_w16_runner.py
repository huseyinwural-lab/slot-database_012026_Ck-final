import asyncio
import uuid
import httpx
import os
import json
from datetime import datetime

# Env
BASE_URL = "http://localhost:8001/api/v1"
ADMIN_EMAIL = "admin@casino.com"
ADMIN_PASS = "Admin123!"

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

async def main():
    print(f"{GREEN}=== BAU W16 OFFER OPTIMIZER & A/B RUNNER ==={RESET}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Login Admin
        print(f"-> Logging in Admin...")
        resp = await client.post(f"{BASE_URL}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}", "X-Reason": "BAU_W16_TEST"}
        
        # 2. Setup Offers
        print(f"-> Creating Offers...")
        offer_a = {"name": "Welcome 100%", "type": "BONUS_GRANT", "cost_value": 100.0}
        resp = await client.post(f"{BASE_URL}/offers", json=offer_a, headers=headers)
        id_a = resp.json()["id"]
        
        offer_b = {"name": "Welcome Free Spins", "type": "FREESPIN", "cost_value": 20.0}
        resp = await client.post(f"{BASE_URL}/offers", json=offer_b, headers=headers)
        id_b = resp.json()["id"]
        
        # 3. Setup Experiment
        print(f"-> Creating Experiment (50/50)...")
        exp_key = "exp_signup_bonus"
        exp_data = {
            "key": exp_key,
            "name": "Signup Bonus Optimization",
            "status": "running",
            "variants": {
                "A": {"weight": 50, "offer_id": id_a},
                "B": {"weight": 50, "offer_id": id_b}
            }
        }
        resp = await client.post(f"{BASE_URL}/offers/experiments", json=exp_data, headers=headers)
        exp_id = resp.json()["id"]
        print(f"{GREEN}   Experiment Created: {exp_id}{RESET}")
        
        # 4. Create Players & Evaluate
        print(f"-> Evaluating Assignments (Deterministic)...")
        
        # Player 1
        p1_email = f"ab1_{uuid.uuid4().hex[:6]}@example.com"
        resp = await client.post(f"{BASE_URL}/auth/player/register", json={"email": p1_email, "password": "password123", "username": "AB_User1"})
        p1_id = resp.json()["player_id"]
        
        # Evaluate
        eval_payload = {"player_id": p1_id, "trigger_event": "signup_bonus"} 
        # Note: trigger_event in engine looks for 'exp_{trigger}' -> 'exp_signup_bonus'
        
        resp = await client.post(f"{BASE_URL}/offers/evaluate", json=eval_payload, headers=headers)
        decision = resp.json()
        variant_1 = decision.get("variant")
        print(f"   Player 1 Assigned: {variant_1} (Decision: {decision['decision']})")
        
        # Verify Sticky
        resp = await client.post(f"{BASE_URL}/offers/evaluate", json=eval_payload, headers=headers)
        decision_retry = resp.json()
        if decision_retry.get("variant") == variant_1:
             print(f"{GREEN}   [PASS] Assignment is Sticky{RESET}")
        else:
             print(f"{RED}   [FAIL] Assignment Changed!{RESET}")

        # 5. Metrics Snapshot
        snapshot = {
            "experiment_key": exp_key,
            "p1_variant": variant_1,
            "decision_record": decision,
            "timestamp": datetime.utcnow().isoformat()
        }
        with open("experiment_metrics_snapshot.json", "w") as f:
            json.dump(snapshot, f, indent=2)
        print(f"{GREEN}   Snapshot saved.{RESET}")

    print(f"{GREEN}=== RUN COMPLETE ==={RESET}")

if __name__ == "__main__":
    asyncio.run(main())
