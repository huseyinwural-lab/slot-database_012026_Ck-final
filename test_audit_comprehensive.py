#!/usr/bin/env python3
"""
Comprehensive P2 Audit Log Backend Test
"""

import requests
import json
import sys
import time
import uuid
from typing import Dict, Any, Optional

# Configuration
try:
    with open("/app/frontend/.env", "r") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip()
                break
        else:
            BASE_URL = "https://wallet-release.preview.emergentagent.com"
except:
    BASE_URL = "https://wallet-release.preview.emergentagent.com"

API_BASE = f"{BASE_URL}/api"

class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []
    
    def add_result(self, test_name: str, passed: bool, details: str = ""):
        self.results.append({
            "test": test_name,
            "status": "PASS" if passed else "FAIL", 
            "details": details
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def print_summary(self):
        print(f"\n=== P2 AUDIT LOG COMPREHENSIVE TEST SUMMARY ===")
        for result in self.results:
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            print(f"{status_icon} {result['test']}: {result['status']}")
            if result["details"]:
                print(f"   Details: {result['details']}")
        
        print(f"\nTotal: {self.passed + self.failed} tests")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        
        return self.failed == 0

def make_request(method: str, endpoint: str, headers: Dict = None, json_data: Dict = None) -> Dict[str, Any]:
    """Make HTTP request and return response details"""
    url = f"{API_BASE}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=json_data, timeout=30)
        elif method.upper() == "PATCH":
            response = requests.patch(url, headers=headers, json=json_data, timeout=30)
        
        try:
            response_json = response.json()
        except:
            response_json = {"raw_text": response.text}
        
        return {
            "status_code": response.status_code,
            "json": response_json,
            "headers": dict(response.headers)
        }
    except Exception as e:
        return {
            "status_code": 0,
            "json": {"error": str(e)},
            "headers": {}
        }

def run_comprehensive_audit_test():
    """Run comprehensive P2 Audit Log test"""
    result = TestResult()
    
    print("=== P2 AUDIT LOG COMPREHENSIVE BACKEND TEST ===")
    print(f"Testing against: {BASE_URL}")
    
    # Step 1: Login as owner (admin@casino.com / Admin123!) and get token
    print("\n1) Login as owner and get token...")
    login_data = {"email": "admin@casino.com", "password": "Admin123!"}
    response = make_request("POST", "/v1/auth/login", json_data=login_data)
    
    if response["status_code"] == 200 and "access_token" in response["json"]:
        token = response["json"]["access_token"]
        result.add_result("Owner Login", True, f"Login successful, token length: {len(token)}")
        print(f"   ✅ Login successful, token obtained")
    else:
        result.add_result("Owner Login", False, f"Login failed: {response['status_code']} - {response['json']}")
        print(f"   ❌ Login failed")
        result.print_summary()
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 2: Create a new tenant via POST /api/v1/tenants/
    print("\n2) Create a new tenant...")
    tenant_data = {
        "name": f"Audit Test Tenant {uuid.uuid4().hex[:8]}",
        "type": "renter",
        "features": {
            "can_manage_admins": True,
            "can_view_reports": True,
            "can_manage_affiliates": False,
            "can_use_crm": False
        }
    }
    
    response = make_request("POST", "/v1/tenants/", headers=headers, json_data=tenant_data)
    
    if response["status_code"] == 200 and "id" in response["json"]:
        tenant_id = response["json"]["id"]
        result.add_result("Tenant Creation", True, f"Tenant created: {tenant_id}")
        print(f"   ✅ Tenant created: {tenant_id}")
    else:
        result.add_result("Tenant Creation", False, f"Tenant creation failed: {response['status_code']}")
        print(f"   ❌ Tenant creation failed")
        result.print_summary()
        return False
    
    # Step 3: Create a new admin via POST /api/v1/admin/users (use password_mode=invite)
    print("\n3) Create a new admin user...")
    admin_data = {
        "email": f"audit.admin.{uuid.uuid4().hex[:8]}@casino.com",
        "password_mode": "invite",
        "full_name": "Audit Test Admin",
        "role": "Admin",
        "tenant_id": tenant_id
    }
    
    response = make_request("POST", "/v1/admin/users", headers=headers, json_data=admin_data)
    
    if response["status_code"] == 200:
        result.add_result("Admin User Creation", True, f"Admin created: {admin_data['email']}")
        print(f"   ✅ Admin user created: {admin_data['email']}")
    else:
        result.add_result("Admin User Creation", False, f"Admin creation failed: {response['status_code']}")
        print(f"   ❌ Admin creation failed")
    
    # Step 4: Update tenant features via PATCH /api/v1/tenants/{tenant_id}
    print("\n4) Update tenant features...")
    features_data = {
        "features": {
            "can_manage_admins": True,
            "can_view_reports": True,
            "can_manage_affiliates": True,
            "can_use_crm": True,
            "can_manage_experiments": False,
            "can_use_kill_switch": False
        }
    }
    
    response = make_request("PATCH", f"/v1/tenants/{tenant_id}", headers=headers, json_data=features_data)
    
    if response["status_code"] == 200:
        result.add_result("Tenant Feature Update", True, "Features updated successfully")
        print(f"   ✅ Tenant features updated")
    else:
        result.add_result("Tenant Feature Update", False, f"Feature update failed: {response['status_code']}")
        print(f"   ❌ Feature update failed")
    
    # Step 5: Fetch audit events as owner
    print("\n5) Fetch audit events...")
    response = make_request("GET", "/v1/audit/events?since_hours=24&limit=50", headers=headers)
    
    if response["status_code"] == 200 and "items" in response["json"]:
        items = response["json"]["items"]
        actions_found = set(item.get("action", "") for item in items)
        
        # Check for expected actions
        expected_actions = {"tenant.created", "admin.user_created", "tenant.feature_flags_changed"}
        found_expected = expected_actions.intersection(actions_found)
        
        # Verify required fields
        required_fields_valid = True
        for item in items:
            required_fields = ["request_id", "actor_user_id", "tenant_id", "action", "resource_type", "result"]
            for field in required_fields:
                if field not in item or item[field] is None:
                    required_fields_valid = False
                    break
        
        if len(found_expected) >= 2 and required_fields_valid:
            result.add_result("Audit Events Retrieval", True, 
                            f"Found {len(items)} events, {len(found_expected)} expected actions, all required fields present")
            print(f"   ✅ Found {len(items)} audit events with expected actions: {sorted(found_expected)}")
        else:
            result.add_result("Audit Events Retrieval", False, 
                            f"Missing expected actions or invalid fields. Found: {found_expected}")
            print(f"   ❌ Audit events validation failed")
    else:
        result.add_result("Audit Events Retrieval", False, f"Failed to fetch audit events: {response['status_code']}")
        print(f"   ❌ Failed to fetch audit events")
    
    # Step 6: Verify tenant scoping behavior
    print("\n6) Verify tenant scoping behavior...")
    
    # Without X-Tenant-ID header
    response1 = make_request("GET", "/v1/audit/events?limit=10", headers=headers)
    
    # With X-Tenant-ID header
    headers_with_tenant = headers.copy()
    headers_with_tenant["X-Tenant-ID"] = tenant_id
    response2 = make_request("GET", "/v1/audit/events?limit=10", headers=headers_with_tenant)
    
    if response1["status_code"] == 200 and response2["status_code"] == 200:
        items1 = response1["json"].get("items", [])
        items2 = response2["json"].get("items", [])
        
        tenant_ids_1 = set(item.get("tenant_id") for item in items1)
        tenant_ids_2 = set(item.get("tenant_id") for item in items2)
        
        # Check scoping behavior
        multiple_tenants = len(tenant_ids_1) > 1 or "default_casino" in tenant_ids_1
        scoped_correctly = len(tenant_ids_2) == 1 and tenant_id in tenant_ids_2
        
        if multiple_tenants and scoped_correctly:
            result.add_result("Tenant Scoping", True, 
                            f"Without header: {len(tenant_ids_1)} tenants, with header: {len(tenant_ids_2)} tenant")
            print(f"   ✅ Tenant scoping working correctly")
        else:
            result.add_result("Tenant Scoping", False, 
                            f"Scoping failed. Multiple: {multiple_tenants}, Scoped: {scoped_correctly}")
            print(f"   ❌ Tenant scoping failed")
    else:
        result.add_result("Tenant Scoping", False, "Failed to test tenant scoping")
        print(f"   ❌ Tenant scoping test failed")
    
    # Step 7: Verify redaction functionality (test the redaction logic directly)
    print("\n7) Verify redaction functionality...")
    
    # Since the API doesn't expose sensitive data in audit logs by design,
    # we'll test the redaction logic directly
    try:
        import sys
        sys.path.append('/app/backend')
        from app.services.audit import _mask_sensitive
        
        test_data = {
            "email": "test@example.com",
            "password": "secret123",
            "token": "bearer-token",
            "api_key": "key123",
            "secret": "mysecret",
            "normal_field": "normal_value"
        }
        
        masked = _mask_sensitive(test_data)
        
        # Check redaction
        redacted_count = sum(1 for k, v in masked.items() 
                           if k.lower() in ["password", "token", "api_key", "secret"] and v == "[REDACTED]")
        
        if redacted_count >= 4:
            result.add_result("Redaction Functionality", True, f"Redacted {redacted_count} sensitive fields")
            print(f"   ✅ Redaction working correctly ({redacted_count} fields redacted)")
        else:
            result.add_result("Redaction Functionality", False, f"Only {redacted_count} fields redacted")
            print(f"   ❌ Redaction not working properly")
    except Exception as e:
        result.add_result("Redaction Functionality", False, f"Redaction test failed: {str(e)}")
        print(f"   ❌ Redaction test failed: {str(e)}")
    
    # Print final summary
    success = result.print_summary()
    
    if success:
        print("\n🎉 ALL P2 AUDIT LOG TESTS PASSED!")
    else:
        print(f"\n💥 {result.failed} TEST(S) FAILED!")
    
    return success

if __name__ == "__main__":
    success = run_comprehensive_audit_test()
    sys.exit(0 if success else 1)