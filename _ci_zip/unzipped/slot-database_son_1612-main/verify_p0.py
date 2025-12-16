import requests
import sys

BASE_URL = "http://localhost:8001/api/v1"
OWNER_EMAIL = "admin@casino.com"
OWNER_PASS = "Admin123!"

def test_p0_04():
    print("--- P0-04 Verification ---")
    
    # 1. Login as Owner
    resp = requests.post(f"{BASE_URL}/auth/login", json={"email": OWNER_EMAIL, "password": OWNER_PASS})
    if resp.status_code != 200:
        print(f"Owner Login Failed: {resp.status_code} {resp.text}")
        sys.exit(1)
    
    owner_token = resp.json()["access_token"]
    print(f"Owner Login OK. Token len: {len(owner_token)}")

    # 2. Create Non-Owner Admin
    non_owner_email = "support@casino.com"
    non_owner_pass = "Support123!"
    
    headers = {"Authorization": f"Bearer {owner_token}"}
    payload = {
        "email": non_owner_email,
        "password": non_owner_pass,
        "full_name": "Support Staff",
        "role": "support",
        "tenant_role": "admin"
    }
    
    # Check if exists first (for idempotency)
    # Just try create, ignore 400
    resp = requests.post(f"{BASE_URL}/admin/users", json=payload, headers=headers)
    if resp.status_code == 200:
        print("Non-Owner User Created.")
    elif resp.status_code == 400 and "exists" in resp.text:
        print("Non-Owner User Already Exists.")
    else:
        print(f"Create Non-Owner Failed: {resp.status_code} {resp.text}")
        sys.exit(1)

    # 3. Login as Non-Owner
    resp = requests.post(f"{BASE_URL}/auth/login", json={"email": non_owner_email, "password": non_owner_pass})
    if resp.status_code != 200:
        print(f"Non-Owner Login Failed: {resp.status_code} {resp.text}")
        sys.exit(1)
    
    support_token = resp.json()["access_token"]
    print("Non-Owner Login OK.")

    # 4. Try to create user for ANOTHER tenant
    headers_support = {"Authorization": f"Bearer {support_token}"}
    target_tenant = "forbidden_tenant"
    
    payload_attack = {
        "email": "victim@forbidden.com",
        "password": "Victim123!",
        "full_name": "Victim User",
        "role": "admin",
        "tenant_id": target_tenant 
    }
    
    resp = requests.post(f"{BASE_URL}/admin/users", json=payload_attack, headers=headers_support)
    
    if resp.status_code == 200:
        data = resp.json()
        created_tenant = data["user"]["tenant_id"]
        print(f"Attack Attempt Result: Status 200. Created Tenant: {created_tenant}")
        
        if created_tenant == "default_casino":
            print("✅ SUCCESS: Tenant ID was forcibly overwritten to user's own tenant.")
        elif created_tenant == target_tenant:
            print("❌ FAILURE: Non-owner was able to create user in another tenant!")
            sys.exit(1)
        else:
            print(f"⚠️ UNKNOWN: Created in {created_tenant}")
            
    elif resp.status_code == 403:
        print("✅ SUCCESS: Server returned 403 Forbidden.")
    else:
        print(f"Unexpected response: {resp.status_code} {resp.text}")

if __name__ == "__main__":
    test_p0_04()
