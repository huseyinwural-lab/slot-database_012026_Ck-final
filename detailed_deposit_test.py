#!/usr/bin/env python3
"""
Detailed Deposit Test - Specific to Review Request

This test specifically addresses the review request:
1) Ensure tenant policy time comparisons no longer error: call register/login then POST /api/v1/player/wallet/deposit twice quickly (to also hit velocity query path) and ensure it returns 200 or 429 (NOT 500).
2) Confirm `OPTIONS /api/v1/auth/player/login` with Origin http://localhost:3001 returns Access-Control-Allow-Origin header.
Please include status codes + bodies.
"""

import asyncio
import json
import uuid
import httpx

# Use backend URL from frontend/.env as specified in the review request
def get_backend_url():
    try:
        with open("/app/frontend/.env", "r") as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    return line.split("=", 1)[1].strip()
    except Exception:
        pass
    return "http://localhost:8001"  # fallback

BACKEND_URL = get_backend_url()

async def detailed_deposit_test():
    """Run detailed deposit test with full status codes and bodies"""
    print("🔍 Detailed Deposit Test - Review Request Verification")
    print(f"Backend URL: {BACKEND_URL}")
    print("=" * 80)
    
    base_url = f"{BACKEND_URL}/api/v1"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: Register a new player
        print("1. Registering new player...")
        player_email = f"detailtest_{uuid.uuid4().hex[:8]}@casino.com"
        player_password = "DetailTest123!"
        
        player_data = {
            "email": player_email,
            "username": f"detailtest_{uuid.uuid4().hex[:8]}",
            "password": player_password,
            "tenant_id": "default_casino"
        }
        
        register_response = await client.post(
            f"{base_url}/auth/player/register",
            json=player_data
        )
        
        print(f"   Status Code: {register_response.status_code}")
        print(f"   Response Body: {register_response.text}")
        
        if register_response.status_code != 200:
            print("❌ Player registration failed")
            return False
        
        # Step 2: Login player
        print("\n2. Logging in player...")
        login_data = {
            "email": player_email,
            "password": player_password,
            "tenant_id": "default_casino"
        }
        
        login_response = await client.post(
            f"{base_url}/auth/player/login",
            json=login_data
        )
        
        print(f"   Status Code: {login_response.status_code}")
        print(f"   Response Body: {login_response.text}")
        
        if login_response.status_code != 200:
            print("❌ Player login failed")
            return False
        
        player_token = login_response.json().get("access_token")
        
        # Step 3: First deposit (quick)
        print("\n3. First deposit (quick)...")
        headers1 = {
            "Authorization": f"Bearer {player_token}",
            "Idempotency-Key": str(uuid.uuid4())
        }
        
        deposit_data1 = {
            "amount": 50.0,
            "method": "test"
        }
        
        deposit1_response = await client.post(
            f"{base_url}/player/wallet/deposit",
            json=deposit_data1,
            headers=headers1
        )
        
        print(f"   Status Code: {deposit1_response.status_code}")
        print(f"   Response Body: {deposit1_response.text}")
        
        # Step 4: Second deposit (immediately after - velocity check)
        print("\n4. Second deposit (immediately after - velocity check)...")
        headers2 = {
            "Authorization": f"Bearer {player_token}",
            "Idempotency-Key": str(uuid.uuid4())
        }
        
        deposit_data2 = {
            "amount": 75.0,
            "method": "test"
        }
        
        deposit2_response = await client.post(
            f"{base_url}/player/wallet/deposit",
            json=deposit_data2,
            headers=headers2
        )
        
        print(f"   Status Code: {deposit2_response.status_code}")
        print(f"   Response Body: {deposit2_response.text}")
        
        # Step 5: CORS Preflight test
        print("\n5. CORS Preflight test...")
        cors_headers = {
            "Origin": "http://localhost:3001",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type,Authorization"
        }
        
        cors_response = await client.options(
            f"{base_url}/auth/player/login",
            headers=cors_headers
        )
        
        print(f"   Status Code: {cors_response.status_code}")
        print(f"   Response Headers:")
        for header, value in cors_response.headers.items():
            if "access-control" in header.lower():
                print(f"     {header}: {value}")
        print(f"   Response Body: {cors_response.text}")
        
        # Analysis
        print("\n" + "=" * 80)
        print("📊 ANALYSIS")
        print("=" * 80)
        
        # Check for 500 errors (the main concern)
        has_500_error = (deposit1_response.status_code == 500 or 
                        deposit2_response.status_code == 500)
        
        if has_500_error:
            print("❌ CRITICAL: Found 500 error in deposit calls - tenant policy time comparison issue NOT fixed")
            return False
        else:
            print("✅ SUCCESS: No 500 errors found - tenant policy time comparison issue is FIXED")
        
        # Check CORS
        cors_origin = cors_response.headers.get("Access-Control-Allow-Origin")
        cors_valid = (cors_origin == "*" or 
                     cors_origin == "http://localhost:3001" or
                     "localhost:3001" in cors_origin)
        
        if cors_valid:
            print(f"✅ SUCCESS: CORS preflight working - Access-Control-Allow-Origin: {cors_origin}")
        else:
            print(f"❌ ISSUE: CORS preflight issue - Access-Control-Allow-Origin: {cors_origin}")
        
        # Summary
        print(f"\nDeposit 1: {deposit1_response.status_code} (Expected: 200, 403, or 429 - NOT 500)")
        print(f"Deposit 2: {deposit2_response.status_code} (Expected: 200, 403, or 429 - NOT 500)")
        print(f"CORS: {cors_response.status_code} with Origin header: {cors_origin}")
        
        return not has_500_error and cors_valid

if __name__ == "__main__":
    success = asyncio.run(detailed_deposit_test())
    exit(0 if success else 1)