import asyncio
import aiohttp
import time
import random
from datetime import datetime

API_URL = "http://localhost:8001/api/v1"
CONCURRENT_USERS = 50
BETS_PER_USER = 20 # Increased
PREFIX = "load_user_"

success_count = 0
fail_count = 0
rate_limited_count = 0
latencies = []

async def user_session(session, user_id):
    global success_count, fail_count, rate_limited_count
    
    email = f"{PREFIX}{user_id}@load.test"
    password = "Password123!"
    
    try:
        # Login (Pre-seeded)
        async with session.post(f"{API_URL}/auth/player/login", json={"email": email, "password": password}) as resp:
            if resp.status != 200:
                print(f"Login failed {user_id}: {resp.status}")
                fail_count += 1
                return
            data = await resp.json()
            token = data.get("access_token")
            player_id = data["user"]["id"]

        headers = {"Authorization": f"Bearer {token}"}
        
        # Bets loop
        for i in range(BETS_PER_USER):
            # No sleep -> Hammer the system
            
            t0 = time.time()
            async with session.post(f"{API_URL}/games/callback/simulator", json={
                "action": "bet",
                "player_id": player_id, 
                "game_id": "slot_load",
                "round_id": f"r_{user_id}_{i}",
                "tx_id": f"tx_{user_id}_{i}",
                "amount": 10,
                "currency": "USD"
            }, headers=headers) as resp:
                lat = (time.time() - t0) * 1000
                latencies.append(lat)
                
                if resp.status == 200:
                    success_count += 1
                elif resp.status == 429:
                    rate_limited_count += 1
                else:
                    fail_count += 1
                    # print(f"Bet failed: {resp.status}")

    except Exception as e:
        print(f"User {user_id} error: {e}")
        fail_count += 1

async def main():
    print(f"--- STARTING LOAD TEST (SEED MODE): {CONCURRENT_USERS} Users, {BETS_PER_USER} Bets each ---")
    start = time.time()
    
    async with aiohttp.ClientSession() as session:
        tasks = [user_session(session, i) for i in range(CONCURRENT_USERS)]
        await asyncio.gather(*tasks)
        
    duration = time.time() - start
    total_reqs = success_count + fail_count + rate_limited_count
    
    import statistics
    p50 = statistics.median(latencies) if latencies else 0
    p95 = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else 0
    
    print(f"--- RESULTS ({duration:.2f}s) ---")
    print(f"Total Requests: {total_reqs}")
    print(f"RPS: {total_reqs / duration:.2f}")
    print(f"Success: {success_count}")
    print(f"Failed: {fail_count}")
    print(f"Rate Limited: {rate_limited_count}")
    print(f"Latency P50: {p50:.2f}ms")
    print(f"Latency P95: {p95:.2f}ms")

if __name__ == "__main__":
    asyncio.run(main())
