import os
import sys
import requests
import time
import json

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8001/api/v1")
IS_MOCK = os.getenv("MOCK_EXTERNAL_SERVICES", "true").lower() == "true"

print(f"--- STAGING SMOKE TEST (Mock={IS_MOCK}) ---")

def check(name, success, details=""):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} | {name} {details}")
    if not success and not IS_MOCK:
        # In real staging, we might want to exit, but let's run all
        pass

def run_tests():
    # 1. Health
    try:
        r = requests.get(f"http://localhost:8001/api/health")
        check("Health Check", r.status_code == 200, f"Status: {r.status_code}")
    except Exception as e:
        check("Health Check", False, f"Error: {e}")
        return # Block

    # 2. Auth - Register
    # Use a unique email to avoid conflict
    email = f"smoke_{int(time.time())}@staging.test"
    password = "Password123!"
    try:
        r = requests.post(f"{API_URL}/auth/player/register", json={
            "email": email,
            "username": f"user_{int(time.time())}",
            "password": password,
            "phone": "+15550009999",
            "dob": "1990-01-01"
        })
        check("Register", r.status_code == 200 or r.status_code == 429, f"Code: {r.status_code}")
    except Exception as e:
        check("Register", False, str(e))

    # Login to get token
    token = None
    try:
        r = requests.post(f"{API_URL}/auth/player/login", json={
            "email": email,
            "password": password
        })
        if r.status_code == 200:
            token = r.json().get("access_token")
            check("Login", True)
        else:
            check("Login", False, f"Status: {r.status_code}")
    except:
        check("Login", False, "Exception")

    if not token:
        print("Skipping authenticated tests due to login failure")
        return

    headers = {"Authorization": f"Bearer {token}"}

    # 3. Verify Email Send
    try:
        r = requests.post(f"{API_URL}/verify/email/send", json={"email": email}, headers=headers)
        if IS_MOCK:
            check("Email Send (Mock)", r.status_code == 200)
        else:
            # In staging, checking if Resend key works
            check("Email Send (Real)", r.status_code == 200, r.text if r.status_code != 200 else "")
    except Exception as e:
        check("Email Send", False, str(e))

    # 4. Verify SMS Send
    try:
        r = requests.post(f"{API_URL}/verify/sms/send", json={"phone": "+15550009999"}, headers=headers)
        if IS_MOCK:
            check("SMS Send (Mock)", r.status_code == 200)
        else:
            check("SMS Send (Real)", r.status_code == 200, r.text if r.status_code != 200 else "")
    except Exception as e:
        check("SMS Send", False, str(e))

    # 5. Deposit Init
    try:
        # Mock verification to allow deposit
        # (If real, we can't deposit without verifying email/sms first)
        # But we can verify with the code if we know it?
        # In real mode, we can't know the code.
        # So Deposit test in Real Staging requires manually verifying the user via DB or Admin API first?
        # Or we skip it.
        
        # Let's try deposit, expect 403 (Unverified) or 200 (if we verify)
        r = requests.post(f"{API_URL}/payments/deposit", json={"amount": 100, "currency": "USD"}, headers=headers)
        
        if r.status_code == 403:
            print("ℹ️ Deposit blocked as expected (Unverified)")
        elif r.status_code == 200:
            check("Deposit Init", True)
        elif r.status_code == 503:
             check("Deposit Init", False, "Missing Stripe Key")
        else:
             check("Deposit Init", False, f"Status: {r.status_code}")

    except Exception as e:
        check("Deposit", False, str(e))

if __name__ == "__main__":
    run_tests()
