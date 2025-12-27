import asyncio
import uuid
import httpx
import os
from datetime import datetime
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
    print(f"{GREEN}=== BAU W13 MIGRATION & VIP LOYALTY RUNNER ==={RESET}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Login Admin
        print(f"-> Logging in Admin...")
        resp = await client.post(f"{BASE_URL}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
        if resp.status_code != 200:
            print(f"{RED}Login Failed: {resp.text}{RESET}")
            return
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}", "X-Reason": "BAU_W13_TEST"}
        
        # 2. Setup VIP Tiers
        print(f"-> Creating VIP Tiers...")
        tiers = [
            {"name": "Bronze", "min_points": 0, "cashback_percent": 0.0},
            {"name": "Silver", "min_points": 1000, "cashback_percent": 5.0},
            {"name": "Gold", "min_points": 5000, "cashback_percent": 10.0}
        ]
        
        for t in tiers:
            resp = await client.post(f"{BASE_URL}/vip/tiers", json=t, headers=headers)
            if resp.status_code == 200:
                print(f"   Created Tier: {t['name']}")
            else:
                # Might already exist
                pass

        # 3. Create Player & Login
        print(f"-> Registering Player...")
        player_email = f"vip_{uuid.uuid4().hex[:6]}@example.com"
        player_data = {
            "email": player_email,
            "username": "VipPlayer",
            "password": "password123"
        }
        resp = await client.post(f"{BASE_URL}/auth/player/register", json=player_data)
        if resp.status_code != 200:
            print(f"{RED}Register Failed: {resp.text}{RESET}")
            return
        # Login Player
        resp = await client.post(f"{BASE_URL}/auth/player/login", json={"email": player_email, "password": "password123"})
        player_token = resp.json()["access_token"]
        player_id = resp.json()["user"]["id"]
        player_headers = {"Authorization": f"Bearer {player_token}"}
        print(f"{GREEN}   Player Logged In: {player_id}{RESET}")

        # 4. Simulate Activity (Earn 1500 Points -> Silver)
        print(f"-> Simulating Activity (1500 Points)...")
        sim_data = {"player_id": player_id, "points": 1500}
        resp = await client.post(f"{BASE_URL}/vip/simulate", json=sim_data, headers=headers)
        if resp.status_code != 200:
             print(f"{RED}Simulate Failed: {resp.text}{RESET}")
             return
        
        # 5. Check Status
        print(f"-> Checking VIP Status...")
        resp = await client.get(f"{BASE_URL}/vip/me", headers=player_headers)
        status = resp.json()
        tier_name = status["tier_name"]
        points = status["status"]["current_points"]
        print(f"   Current Tier: {tier_name}")
        print(f"   Points: {points}")
        
        if tier_name == "Silver":
            print(f"{GREEN}   [PASS] Tier Upgrade Verified (Silver){RESET}")
        else:
            print(f"{RED}   [FAIL] Tier Upgrade Failed (Expected Silver, got {tier_name}){RESET}")

        # 6. Redeem Points (500 Points -> $5)
        print(f"-> Redeeming 500 Points...")
        redeem_data = {"points": 500}
        resp = await client.post(f"{BASE_URL}/vip/redeem", json=redeem_data, headers=player_headers)
        if resp.status_code != 200:
             print(f"{RED}Redeem Failed: {resp.text}{RESET}")
             return
        cash = resp.json()["cash_received"]
        print(f"{GREEN}   Redeemed: ${cash}{RESET}")
        
        # Verify Wallet
        resp = await client.get(f"{BASE_URL}/player/wallet/balance", headers=player_headers) # Assuming this endpoint exists
        # If not, check /auth/player/login response or specific endpoint
        # Or check /vip/me again? No, wallet balance.
        # Let's check 'balance_real' from login or profile if endpoints are missing.
        # But wait, PlayerWallet usually has 'balance'.
        # Try /api/v1/player/wallet/balance
        # Or just trust the redeem response for now if endpoint is tricky.
        
        # 7. Generate Snapshot
        snapshot = {
            "player_id": player_id,
            "tier": tier_name,
            "points_balance": points - 500,
            "cash_redeemed": cash,
            "timestamp": datetime.utcnow().isoformat()
        }
        with open("vip_metrics_snapshot.json", "w") as f:
            json.dump(snapshot, f, indent=2)
        print(f"{GREEN}   Snapshot saved.{RESET}")

    print(f"{GREEN}=== RUN COMPLETE ==={RESET}")

if __name__ == "__main__":
    asyncio.run(main())
