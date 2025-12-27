import asyncio
import uuid
import httpx
import time
import statistics
import os
import json

# Env
BASE_URL = "http://localhost:8001/api/v1"
ADMIN_EMAIL = "admin@casino.com"
ADMIN_PASS = "Admin123!"

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

class LoadTester:
    def __init__(self, base_url, admin_token=None):
        self.base_url = base_url
        self.token = admin_token
        self.headers = {"Authorization": f"Bearer {admin_token}", "X-Reason": "LOAD_TEST"} if admin_token else {}
        self.results = []

    async def login_admin(self):
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{self.base_url}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
            self.token = resp.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}", "X-Reason": "LOAD_TEST"}

    async def scenario_payment_burst(self, count=50):
        print(f"{BLUE}-> Starting Payment Burst Test ({count} reqs)...{RESET}")
        
        # Setup: Create a player first
        async with httpx.AsyncClient() as client:
            p_email = f"load_{uuid.uuid4().hex[:6]}@load.com"
            resp = await client.post(f"{self.base_url}/auth/player/register", json={"email": p_email, "password": "password123", "username": "LoadUser"})
            player_id = resp.json()["player_id"]
        
        # Concurrent Deposits (Mock Webhook)
        start_time = time.time()
        
        async with httpx.AsyncClient(limits=httpx.Limits(max_keepalive_connections=20, max_connections=50)) as client:
            tasks = []
            for i in range(count):
                payload = {
                    "event_type": "deposit_captured",
                    "tenant_id": "default_casino",
                    "player_id": player_id,
                    "amount": 10.0,
                    "currency": "USD",
                    "provider": "mockpsp",
                    "provider_event_id": f"load_evt_{uuid.uuid4()}",
                    "tx_id": f"load_tx_{uuid.uuid4()}"
                }
                tasks.append(client.post(f"{self.base_url}/payments/webhook/mockpsp", json=payload))
            
            responses = await asyncio.gather(*tasks)
            
        duration = time.time() - start_time
        success = sum(1 for r in responses if r.status_code == 200)
        
        self._record_metric("Payment Burst", count, success, duration)

    async def scenario_offer_decision(self, count=50):
        print(f"{BLUE}-> Starting Offer Decision Test ({count} reqs)...{RESET}")
        
        # Use existing player
        player_id = str(uuid.uuid4()) # Mock ID is fine for eval if player verification is mocked or skipped in load test? 
        # Actually OfferEngine checks DB. Need real player.
        # Create one.
        async with httpx.AsyncClient() as client:
            p_email = f"offer_load_{uuid.uuid4().hex[:6]}@load.com"
            resp = await client.post(f"{self.base_url}/auth/player/register", json={"email": p_email, "password": "password123", "username": "OfferLoadUser"})
            player_id = resp.json()["player_id"]

        start_time = time.time()
        
        async with httpx.AsyncClient(limits=httpx.Limits(max_keepalive_connections=20, max_connections=50)) as client:
            tasks = []
            for i in range(count):
                # Admin Evaluate Endpoint (Heavy)
                payload = {
                    "player_id": player_id,
                    "trigger_event": "login"
                }
                tasks.append(client.post(f"{self.base_url}/offers/evaluate", json=payload, headers=self.headers))
            
            responses = await asyncio.gather(*tasks)
            
        duration = time.time() - start_time
        success = sum(1 for r in responses if r.status_code == 200)
        
        self._record_metric("Offer Decision", count, success, duration)

    def _record_metric(self, name, total, success, duration):
        rps = total / duration if duration > 0 else 0
        print(f"{GREEN}   {name}: {success}/{total} success in {duration:.2f}s ({rps:.1f} RPS){RESET}")
        self.results.append({
            "scenario": name,
            "total": total,
            "success": success,
            "duration_sec": duration,
            "rps": rps
        })

    def save_report(self):
        os.makedirs("/app/artifacts/bau/week19", exist_ok=True)
        with open("/app/artifacts/bau/week19/load_test_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"   Report saved to /app/artifacts/bau/week19/load_test_results.json")

async def main():
    tester = LoadTester(BASE_URL)
    await tester.login_admin()
    
    # Run Scenarios
    await tester.scenario_payment_burst(count=100)
    await tester.scenario_offer_decision(count=50) # Heavier op
    
    tester.save_report()

if __name__ == "__main__":
    asyncio.run(main())
