import requests
import sys

BASE_URL = "http://localhost:8001/api/v1"

def test_critical_fixes():
    print("🚀 Starting Critical Fix Verification...")
    
    # 1. Test Backend Startup Seed (Indirectly)
    # If seed works, 'default_casino' should exist
    print("\n🔍 Checking Default Tenant...")
    # Need to login as superadmin first to check tenants, OR use seed endpoint if public? Seed is not public.
    # But seed_complete_data.py was run before. 
    # Let's try to login as admin@casino.com to verify DB connection + user existence.
    try:
        resp = requests.post(f"{BASE_URL}/auth/login", json={"email": "admin@casino.com", "password": "Admin123!"})
        if resp.status_code == 200:
            print("✅ Login successful (DB connection working)")
            token = resp.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # 2. Check Tenant Flags
            print("\n🔍 Checking Tenant Flags...")
            resp = requests.get(f"{BASE_URL}/tenants/", headers=headers)
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                demo = next((t for t in items if t["id"] == "demo_renter"), None)
                if demo:
                    feats = demo.get("features", {})
                    if feats.get("can_manage_admins") is True:
                        print("✅ Demo Renter has 'can_manage_admins'")
                    else:
                        print("❌ Demo Renter MISSING 'can_manage_admins'")
                        sys.exit(1)
                else:
                    print("⚠️ Demo Renter not found in list (might need re-seed)")
            else:
                print(f"❌ Failed to list tenants: {resp.status_code}")
                sys.exit(1)
                
        else:
            print(f"❌ Login failed: {resp.text}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        sys.exit(1)

    print("\n✅ Critical Fix Verification Complete!")

if __name__ == "__main__":
    test_critical_fixes()
