import asyncio
import sys
import os
import json
import logging
from datetime import datetime, timezone
import requests # Need simple request lib if we curl, but standard is httpx or curl
# We'll use subprocess curl for Health Check to be safe and independent of python libs if needed, but httpx is better
# Assuming httpx is installed
import httpx

# Paths
sys.path.append("/app/backend")
sys.path.append("/app/scripts")

# Env (Mock Prod for Hypercare Drill)
# In real life, these are set. Here we ensure they persist from previous step or set them.
if "ENV" not in os.environ:
    os.environ["ENV"] = "prod"
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:////app/backend/casino_prod.db" 

from config import settings

async def hc_health_check(hh: str):
    """HC-010: Check Ops Health"""
    print(f"[{hh}:00] HC-010 Ops Health Check...")
    
    # We need the backend running. If not, this fails.
    # In this environment, backend is on 8001.
    url = "http://localhost:8001/api/v1/ops/health"
    
    status = "FAIL"
    content = ""
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=5.0)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "green":
                    status = "GREEN"
                else:
                    status = f"WARN ({data.get('status')})"
                content = json.dumps(data, indent=2)
            else:
                status = f"FAIL ({resp.status_code})"
                content = resp.text
    except Exception as e:
        status = f"FAIL (Exception: {e})"
        content = str(e)
        
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    fname = f"/app/artifacts/hypercare/ops_health_{date_str}_{hh}.txt"
    
    with open(fname, "w") as f:
        f.write(f"Timestamp: {datetime.now(timezone.utc)}\nStatus: {status}\n\n{content}")
        
    print(f"Health Check: {status} -> {fname}")
    return status

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 hc_010_health.py <HH>")
        sys.exit(1)
    asyncio.run(hc_health_check(sys.argv[1]))
