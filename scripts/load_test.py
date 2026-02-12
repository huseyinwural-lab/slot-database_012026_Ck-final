import asyncio
import aiohttp
import time
import random
from datetime import datetime

API_URL = "http://localhost:8001/api/v1"
CONCURRENT_USERS = 50
BETS_PER_USER = 10

success_count = 0
fail_count = 0
rate_limited_count = 0

async def user_session(session, user_id):
    global success_count, fail_count, rate_limited_count
    
    email = f"load_{user_id}_{int(time.time())}@load.test"
    password = "Password123!"
    
    try:
        # Register
        async with session.post(f"{API_URL}/auth/player/register", json={
            "email": email,
            "password": password,
            "username": f"user_{user_id}",
            "phone": f"+1555{str(user_id).zfill(7)}"
        }) as resp:
            if resp.status != 200:
                print(f"Register failed: {resp.status}")
                return

        # Login
        async with session.post(f"{API_URL}/auth/player/login", json={"email": email, "password": password}) as resp:
            data = await resp.json()
            token = data.get("access_token")
            if not token:
                return

        headers = {"Authorization": f"Bearer {token}"}
        
        # Verify (Mock)
        await session.post(f"{API_URL}/test/set-kyc", json={"email": email, "status": "verified"}, headers=headers)
        
        # Deposit
        await session.post(f"{API_URL}/player/wallet/deposit", json={"amount": 1000, "currency": "USD", "method": "test"}, headers={**headers, "Idempotency-Key": f"dep_{user_id}"})

        # Bets loop
        for i in range(BETS_PER_USER):
            await asyncio.sleep(random.uniform(0.1, 0.5)) # Human-like delay
            
            async with session.post(f"{API_URL}/games/callback/simulator", json={
                "action": "bet",
                "player_id": data["user"]["id"], # Use ID from login
                "game_id": "slot_load",
                "round_id": f"r_{user_id}_{i}",
                "tx_id": f"tx_{user_id}_{i}",
                "amount": 10,
                "currency": "USD"
            }, headers=headers) as resp:
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
    print(f"--- STARTING LOAD TEST: {CONCURRENT_USERS} Users, {BETS_PER_USER} Bets each ---")
    start = time.time()
    
    async with aiohttp.ClientSession() as session:
        tasks = [user_session(session, i) for i in range(CONCURRENT_USERS)]
        await asyncio.gather(*tasks)
        
    duration = time.time() - start
    print(f"--- DONE in {duration:.2f}s ---")
    print(f"Success: {success_count}")
    print(f"Failed: {fail_count}")
    print(f"Rate Limited (429): {rate_limited_count}")
    print(f"RPS: {(success_count + fail_count + rate_limited_count) / duration:.2f}")

if __name__ == "__main__":
    asyncio.run(main())
