import asyncio
import random
import time
import uuid
import httpx
import hmac
import hashlib
import logging
import os

# Config
BASE_URL = os.getenv("BASE_URL", "http://localhost:8001") # Internal container URL
PROVIDER_ENDPOINT = "/api/v1/games/callback/pragmatic"
SECRET_KEY = os.getenv("TEST_SECRET_KEY", "test_secret") 
CONCURRENCY = int(os.getenv("LOAD_TEST_CONCURRENCY", 10))
TOTAL_REQUESTS = int(os.getenv("LOAD_TEST_REQUESTS", 1000))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("load_test")

class PragmaticLoadTest:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)
        self.stats = {"success": 0, "fail": 0, "latency": []}

    def sign_payload(self, payload: dict) -> str:
        canonical = "&".join([f"{k}={v}" for k, v in sorted(payload.items())])
        return hmac.new(
            SECRET_KEY.encode("utf-8"),
            canonical.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

    async def send_bet(self, user_id: str):
        tx_id = str(uuid.uuid4())
        payload = {
            "action": "bet",
            "userId": user_id,
            "gameId": "load_game_1",
            "roundId": f"r_{uuid.uuid4()}",
            "reference": tx_id,
            "amount": 1.0,
            "currency": "USD"
        }
        payload["hash"] = self.sign_payload(payload)
        
        start = time.time()
        try:
            resp = await self.client.post(f"{BASE_URL}{PROVIDER_ENDPOINT}", json=payload)
            dur = time.time() - start
            self.stats["latency"].append(dur)
            
            if resp.status_code == 200 and resp.json().get("error") == 0:
                self.stats["success"] += 1
            else:
                self.stats["fail"] += 1
                logger.error(f"Fail: {resp.status_code} {resp.text}")
        except Exception as e:
            self.stats["fail"] += 1
            logger.error(f"Exception: {e}")

    async def worker(self, user_id: str, count: int):
        for _ in range(count):
            await self.send_bet(user_id)
            await asyncio.sleep(0.05) # Rate limit slightly

    async def run(self):
        logger.info("Starting Load Test...")
        start_global = time.time()
        
        tasks = []
        # Simulate users
        for i in range(CONCURRENCY):
            user_id = f"load_user_{i}"
            tasks.append(self.worker(user_id, int(TOTAL_REQUESTS / CONCURRENCY)))
            
        await asyncio.gather(*tasks)
        
        duration = time.time() - start_global
        logger.info(f"Finished in {duration:.2f}s")
        logger.info(f"TPS: {TOTAL_REQUESTS / duration:.2f}")
        logger.info(f"Stats: {self.stats['success']} Success, {self.stats['fail']} Fail")
        
        if self.stats["latency"]:
            avg = sum(self.stats["latency"]) / len(self.stats["latency"])
            logger.info(f"Avg Latency: {avg*1000:.2f}ms")

if __name__ == "__main__":
    test = PragmaticLoadTest()
    asyncio.run(test.run())
