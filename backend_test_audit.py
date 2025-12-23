#!/usr/bin/env python3
"""
P2 Audit Log Backend Validation
Testing P2 Audit Log functionality end-to-end including login, tenant creation, admin creation, 
feature updates, audit event retrieval, tenant scoping, and redaction
"""

import requests
import json
import sys
import os
import time
import uuid
import re
from typing import Dict, Any, Optional

# Configuration - Use frontend .env for external URL
try:
    with open("/app/frontend/.env", "r") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip()
                break
        else:
            BASE_URL = "https://pay-processor-2.preview.emergentagent.com"
except:
    BASE_URL = "https://pay-processor-2.preview.emergentagent.com"

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
        print(f"\n=== P2 AUDIT LOG VALIDATION SUMMARY ===")
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
        elif method.upper() == "OPTIONS":
            response = requests.options(url, headers=headers, timeout=30)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
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

def test_owner_login_and_get_token(result: TestResult) -> Optional[str]:
    """Test 1: Login as owner and get token"""
    print("\n1. Testing Owner Login...")
    
    login_data = {
        "email": "admin@casino.com",
        "password": "Admin123!"
    }
    
    response = make_request("POST", "/v1/auth/login", json_data=login_data)
    print(f"   POST /api/v1/auth/login: Status {response['status_code']}")
    
    if response["status_code"] == 200 and "access_token" in response["json"]:
        token = response["json"]["access_token"]
        result.add_result(
            "Owner Login", 
            True, 
            f"Login successful, token length: {len(token)}"
        )
        return token
    else:
        result.add_result(
            "Owner Login", 
            False, 
            f"Expected 200 with access_token, got {response['status_code']}: {response['json']}"
        )
        return None

def test_create_tenant(result: TestResult, token: str) -> Optional[str]:
    """Test 2: Create a new tenant via POST /api/v1/tenants/"""
    print("\n2. Testing Tenant Creation...")
    
    headers = {"Authorization": f"Bearer {token}"}
    tenant_data = {
        "name": f"Test Tenant {uuid.uuid4().hex[:8]}",
        "type": "renter",
        "features": {
            "can_manage_admins": True,
            "can_view_reports": True,
            "can_manage_affiliates": False,
            "can_use_crm": False
        }
    }
    
    response = make_request("POST", "/v1/tenants/", headers=headers, json_data=tenant_data)
    print(f"   POST /api/v1/tenants/: Status {response['status_code']}")
    
    if response["status_code"] == 200 and "id" in response["json"]:
        tenant_id = response["json"]["id"]
        result.add_result(
            "Tenant Creation", 
            True, 
            f"Tenant created successfully, ID: {tenant_id}"
        )
        return tenant_id
    else:
        result.add_result(
            "Tenant Creation", 
            False, 
            f"Expected 200 with tenant ID, got {response['status_code']}: {response['json']}"
        )
        return None

def test_create_admin_user(result: TestResult, token: str, tenant_id: str) -> None:
    """Test 3: Create a new admin via POST /api/v1/admin/users"""
    print("\n3. Testing Admin User Creation...")
    
    headers = {"Authorization": f"Bearer {token}"}
    admin_data = {
        "email": f"test.admin.{uuid.uuid4().hex[:8]}@casino.com",
        "password_mode": "invite",
        "full_name": "Test Admin User",
        "role": "Admin",
        "tenant_id": tenant_id
    }
    
    response = make_request("POST", "/v1/admin/users", headers=headers, json_data=admin_data)
    print(f"   POST /api/v1/admin/users: Status {response['status_code']}")
    
    if response["status_code"] == 200 and "user" in response["json"]:
        result.add_result(
            "Admin User Creation", 
            True, 
            f"Admin user created successfully: {admin_data['email']}"
        )
    else:
        result.add_result(
            "Admin User Creation", 
            False, 
            f"Expected 200 with user data, got {response['status_code']}: {response['json']}"
        )

def test_update_tenant_features(result: TestResult, token: str, tenant_id: str) -> None:
    """Test 4: Update tenant features via PATCH /api/v1/tenants/{tenant_id}"""
    print("\n4. Testing Tenant Feature Update...")
    
    headers = {"Authorization": f"Bearer {token}"}
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
    print(f"   PATCH /api/v1/tenants/{tenant_id}: Status {response['status_code']}")
    
    if response["status_code"] == 200:
        result.add_result(
            "Tenant Feature Update", 
            True, 
            f"Tenant features updated successfully"
        )
    else:
        result.add_result(
            "Tenant Feature Update", 
            False, 
            f"Expected 200, got {response['status_code']}: {response['json']}"
        )

def test_fetch_audit_events(result: TestResult, token: str) -> None:
    """Test 5: Fetch audit events as owner"""
    print("\n5. Testing Audit Events Retrieval...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = make_request("GET", "/v1/audit/events?since_hours=24&limit=50", headers=headers)
    print(f"   GET /api/v1/audit/events: Status {response['status_code']}")
    
    if response["status_code"] == 200 and "items" in response["json"]:
        items = response["json"]["items"]
        
        # Check for expected actions
        actions_found = set()
        required_fields_valid = True
        
        for item in items:
            actions_found.add(item.get("action", ""))
            
            # Verify required fields are present and non-null
            required_fields = ["request_id", "actor_user_id", "tenant_id", "action", "resource_type", "result"]
            for field in required_fields:
                if field not in item or item[field] is None:
                    required_fields_valid = False
                    print(f"   Missing or null field '{field}' in audit event: {item.get('id', 'unknown')}")
        
        expected_actions = {"tenant.created", "admin.user_created", "tenant.feature_flags_changed"}
        found_expected = expected_actions.intersection(actions_found)
        
        print(f"   Found {len(items)} audit events")
        print(f"   Actions found: {sorted(actions_found)}")
        print(f"   Expected actions found: {sorted(found_expected)}")
        
        if len(found_expected) >= 2 and required_fields_valid:  # At least 2 of the 3 expected actions
            result.add_result(
                "Audit Events Retrieval", 
                True, 
                f"Found {len(items)} events with {len(found_expected)} expected actions, all required fields present"
            )
        else:
            result.add_result(
                "Audit Events Retrieval", 
                False, 
                f"Expected actions missing or invalid fields. Found: {found_expected}, Fields valid: {required_fields_valid}"
            )
    else:
        result.add_result(
            "Audit Events Retrieval", 
            False, 
            f"Expected 200 with items array, got {response['status_code']}: {response['json']}"
        )

def test_tenant_scoping_behavior(result: TestResult, token: str, tenant_id: str) -> None:
    """Test 6: Verify tenant scoping behavior"""
    print("\n6. Testing Tenant Scoping Behavior...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test without X-Tenant-ID header (should include multiple tenants)
    response1 = make_request("GET", "/v1/audit/events?limit=10", headers=headers)
    print(f"   GET /api/v1/audit/events (no header): Status {response1['status_code']}")
    
    # Test with X-Tenant-ID header (should only include that tenant)
    headers_with_tenant = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": tenant_id
    }
    response2 = make_request("GET", "/v1/audit/events?limit=10", headers=headers_with_tenant)
    print(f"   GET /api/v1/audit/events (with X-Tenant-ID): Status {response2['status_code']}")
    
    if response1["status_code"] == 200 and response2["status_code"] == 200:
        items1 = response1["json"].get("items", [])
        items2 = response2["json"].get("items", [])
        
        # Check tenant IDs in responses
        tenant_ids_1 = set(item.get("tenant_id") for item in items1)
        tenant_ids_2 = set(item.get("tenant_id") for item in items2)
        
        print(f"   Without header - tenant IDs: {sorted(tenant_ids_1)}")
        print(f"   With header - tenant IDs: {sorted(tenant_ids_2)}")
        
        # Without header should have multiple tenants or at least default_casino
        # With header should only have the specified tenant
        multiple_tenants = len(tenant_ids_1) > 1 or "default_casino" in tenant_ids_1
        scoped_correctly = len(tenant_ids_2) == 1 and tenant_id in tenant_ids_2
        
        if multiple_tenants and scoped_correctly:
            result.add_result(
                "Tenant Scoping Behavior", 
                True, 
                f"Scoping works correctly. Without header: {len(tenant_ids_1)} tenants, with header: {len(tenant_ids_2)} tenant"
            )
        else:
            result.add_result(
                "Tenant Scoping Behavior", 
                False, 
                f"Scoping issue. Multiple tenants: {multiple_tenants}, Scoped correctly: {scoped_correctly}"
            )
    else:
        result.add_result(
            "Tenant Scoping Behavior", 
            False, 
            f"API calls failed. Status codes: {response1['status_code']}, {response2['status_code']}"
        )

def test_redaction_in_details(result: TestResult, token: str, tenant_id: str) -> None:
    """Test 7: Verify redaction in details (PII/credential keys)"""
    print("\n7. Testing Redaction in Details...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create an admin with password field to trigger redaction
    admin_data = {
        "email": f"redaction.test.{uuid.uuid4().hex[:8]}@casino.com",
        "password": "TestPassword123!",
        "full_name": "Redaction Test Admin",
        "role": "Admin",
        "tenant_id": tenant_id,
        "api_key": "secret-api-key-123",
        "token": "secret-token-456"
    }
    
    # Create admin (this should log an event with sensitive data)
    create_response = make_request("POST", "/v1/admin/users", headers=headers, json_data=admin_data)
    print(f"   POST /api/v1/admin/users (with sensitive data): Status {create_response['status_code']}")
    
    # Wait a moment for the audit event to be logged
    time.sleep(1)
    
    # Fetch recent audit events
    response = make_request("GET", "/v1/audit/events?since_hours=1&limit=10", headers=headers)
    print(f"   GET /api/v1/audit/events (checking redaction): Status {response['status_code']}")
    
    if response["status_code"] == 200 and "items" in response["json"]:
        items = response["json"]["items"]
        
        redaction_working = False
        sensitive_keys_found = []
        
        for item in items:
            details = item.get("details", {})
            if isinstance(details, dict):
                # Check for redacted sensitive keys
                for key, value in details.items():
                    if key.lower() in ["password", "token", "secret", "api_key"]:
                        if value == "[REDACTED]":
                            redaction_working = True
                        else:
                            sensitive_keys_found.append(f"{key}={value}")
        
        if redaction_working and not sensitive_keys_found:
            result.add_result(
                "Redaction in Details", 
                True, 
                "Sensitive keys properly redacted as [REDACTED]"
            )
        elif redaction_working and sensitive_keys_found:
            result.add_result(
                "Redaction in Details", 
                False, 
                f"Partial redaction - some sensitive data leaked: {sensitive_keys_found}"
            )
        else:
            result.add_result(
                "Redaction in Details", 
                False, 
                "No redaction detected - sensitive data may be exposed"
            )
    else:
        result.add_result(
            "Redaction in Details", 
            False, 
            f"Failed to fetch audit events for redaction test: {response['status_code']}"
        )

def main():
    print("=== P2 AUDIT LOG BACKEND VALIDATION ===")
    print(f"Testing against: {BASE_URL}")
    
    result = TestResult()
    
    # Test 1: Login as owner and get token
    token = test_owner_login_and_get_token(result)
    if not token:
        print("❌ Cannot proceed without valid token")
        result.print_summary()
        return False
    
    # Test 2: Create a new tenant
    tenant_id = test_create_tenant(result, token)
    if not tenant_id:
        print("❌ Cannot proceed without valid tenant ID")
        result.print_summary()
        return False
    
    # Test 3: Create a new admin user
    test_create_admin_user(result, token, tenant_id)
    
    # Test 4: Update tenant features
    test_update_tenant_features(result, token, tenant_id)
    
    # Test 5: Fetch audit events
    test_fetch_audit_events(result, token)
    
    # Test 6: Verify tenant scoping behavior
    test_tenant_scoping_behavior(result, token, tenant_id)
    
    # Test 7: Verify redaction in details
    test_redaction_in_details(result, token, tenant_id)
    
    # Print final summary
    success = result.print_summary()
    
    if success:
        print("\n🎉 ALL P2 AUDIT LOG VALIDATION TESTS PASSED!")
        return True
    else:
        print(f"\n💥 {result.failed} TEST(S) FAILED - AUDIT LOG ISSUES DETECTED!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)