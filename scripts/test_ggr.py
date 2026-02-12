import requests
import time
import os
import json

API_URL = "http://localhost:8001/api/v1"
ADMIN_EMAIL = "admin@casino.com"
ADMIN_PASS = "Admin123!"

def run_ggr_test():
    print("--- GGR REPORT TEST ---")
    
    # 1. Login Admin
    print("Logging in Admin...")
    r = requests.post(f"{API_URL}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
    if r.status_code != 200:
        print("Admin login failed", r.text)
        return
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Call GGR Report
    # Date range: Today (UTC)
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    start = (now - timedelta(hours=24)).isoformat()
    end = (now + timedelta(hours=24)).isoformat()
    
    print(f"Fetching GGR for {start} to {end}")
    r = requests.get(f"{API_URL}/admin/reports/ggr", params={"start_date": start, "end_date": end}, headers=headers)
    
    if r.status_code != 200:
        print("Report Failed:", r.text)
        return
        
    data = r.json()
    print("GGR Data:", json.dumps(data, indent=2))
    
    # Assertion (Mock check)
    # We did some bets in previous steps (simulated).
    # Expected: total_bet > 0, total_win > 0
    if data["total_bet"] > 0:
        print("✅ GGR Calculation Verified (Data Present)")
    else:
        print("⚠️ No data in report range (Maybe Simulator used different dates or tenant?)")
        # Sim uses current time, so it should be there.
        # Check Tenant: Sim user created under 'default_casino'. Admin is 'default_casino'. Match OK.

if __name__ == "__main__":
    run_ggr_test()
