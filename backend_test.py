#!/usr/bin/env python3
"""
P2 Auth Audit Events Backend Validation
Testing P2 Auth audit events end-to-end including successful login, failed login, 
rate limiting, logout (if exists), and required fields validation
"""

import requests
import json
import sys
import os
import time
import uuid
import re
import hashlib
from typing import Dict, Any, Optional

# Configuration - Use frontend .env for external URL
with open("/app/frontend/.env", "r") as f:
    for line in f:
        if line.startswith("REACT_APP_BACKEND_URL="):
            BASE_URL = line.split("=", 1)[1].strip()
            break
else:
    BASE_URL = "https://game-admin-hub-1.preview.emergentagent.com"

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
        print(f"\n=== P2 AUTH AUDIT EVENTS VALIDATION SUMMARY ===")
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

def get_recent_audit_events(token: str, since_minutes: int = 5) -> Dict[str, Any]:
    """Helper to get recent audit events"""
    headers = {"Authorization": f"Bearer {token}"}
    return make_request("GET", f"/v1/audit/events?since_hours=1&limit=50", headers=headers)

def test_successful_login_audit(result: TestResult) -> Optional[str]:
    """Test 1: Successful login creates auth.login_success audit event"""
    print("\n1. Testing Successful Login Audit Event...")
    
    login_data = {
        "email": "admin@casino.com",
        "password": "Admin123!"
    }
    
    # Get audit events count before login
    temp_response = make_request("POST", "/v1/auth/login", json_data=login_data)
    if temp_response["status_code"] != 200:
        result.add_result("Successful Login Audit", False, f"Cannot login to get baseline: {temp_response['status_code']}")
        return None
    
    temp_token = temp_response["json"]["access_token"]
    before_response = get_recent_audit_events(temp_token)
    before_count = len(before_response["json"].get("items", [])) if before_response["status_code"] == 200 else 0
    
    # Perform the actual login we want to test
    response = make_request("POST", "/v1/auth/login", json_data=login_data)
    print(f"   POST /api/v1/auth/login: Status {response['status_code']}")
    
    if response["status_code"] != 200 or "access_token" not in response["json"]:
        result.add_result("Successful Login Audit", False, f"Login failed: {response['status_code']}")
        return None
    
    token = response["json"]["access_token"]
    
    # Wait a moment for audit event to be written
    time.sleep(1)
    
    # Get audit events after login
    after_response = get_recent_audit_events(token)
    if after_response["status_code"] != 200:
        result.add_result("Successful Login Audit", False, f"Cannot fetch audit events: {after_response['status_code']}")
        return token
    
    events = after_response["json"].get("items", [])
    
    # Find the most recent auth.login_success event
    login_success_events = [e for e in events if e.get("action") == "auth.login_success"]
    
    if not login_success_events:
        result.add_result("Successful Login Audit", False, "No auth.login_success audit event found")
        return token
    
    event = login_success_events[0]  # Most recent
    
    # Verify required fields
    required_fields = ["request_id", "tenant_id", "action", "resource_type", "result", "timestamp", "ip_address"]
    missing_fields = [f for f in required_fields if not event.get(f)]
    
    if missing_fields:
        result.add_result("Successful Login Audit", False, f"Missing required fields: {missing_fields}")
        return token
    
    # Verify specific values
    checks = []
    if event.get("action") != "auth.login_success":
        checks.append(f"action={event.get('action')} (expected auth.login_success)")
    if event.get("resource_type") != "auth":
        checks.append(f"resource_type={event.get('resource_type')} (expected auth)")
    if event.get("result") != "success":
        checks.append(f"result={event.get('result')} (expected success)")
    
    # Verify details structure
    details = event.get("details", {})
    expected_detail_keys = ["method", "mfa", "user_agent", "tenant_context"]
    missing_detail_keys = [k for k in expected_detail_keys if k not in details]
    
    if missing_detail_keys:
        checks.append(f"Missing details keys: {missing_detail_keys}")
    
    if details.get("method") != "password":
        checks.append(f"details.method={details.get('method')} (expected password)")
    
    # Verify resource_id is 64 hex chars (sha256)
    resource_id = event.get("resource_id", "")
    if not re.match(r'^[a-f0-9]{64}$', resource_id):
        checks.append(f"resource_id not 64 hex chars: {resource_id}")
    
    # Verify no raw email/username in details
    details_str = json.dumps(details).lower()
    if "admin@casino.com" in details_str or "admin123!" in details_str:
        checks.append("Raw credentials found in details")
    
    if checks:
        result.add_result("Successful Login Audit", False, f"Validation failures: {'; '.join(checks)}")
    else:
        result.add_result("Successful Login Audit", True, f"All validations passed. Event ID: {event.get('id')}")
    
    return token

def test_failed_login_audit(result: TestResult) -> None:
    """Test 2: Failed login creates auth.login_failed audit event"""
    print("\n2. Testing Failed Login Audit Event...")
    
    # First get a valid token to check audit events
    valid_login = {
        "email": "admin@casino.com",
        "password": "Admin123!"
    }
    temp_response = make_request("POST", "/v1/auth/login", json_data=valid_login)
    if temp_response["status_code"] != 200:
        result.add_result("Failed Login Audit", False, "Cannot get token for audit check")
        return
    
    token = temp_response["json"]["access_token"]
    
    # Get baseline audit events
    before_response = get_recent_audit_events(token)
    before_count = len(before_response["json"].get("items", [])) if before_response["status_code"] == 200 else 0
    
    # Attempt login with wrong password
    failed_login_data = {
        "email": "admin@casino.com",
        "password": "WrongPassword123!"
    }
    
    response = make_request("POST", "/v1/auth/login", json_data=failed_login_data)
    print(f"   POST /api/v1/auth/login (wrong password): Status {response['status_code']}")
    
    if response["status_code"] != 401:
        result.add_result("Failed Login Audit", False, f"Expected 401, got {response['status_code']}")
        return
    
    # Wait for audit event
    time.sleep(1)
    
    # Get audit events after failed login
    after_response = get_recent_audit_events(token)
    if after_response["status_code"] != 200:
        result.add_result("Failed Login Audit", False, f"Cannot fetch audit events: {after_response['status_code']}")
        return
    
    events = after_response["json"].get("items", [])
    
    # Find the most recent auth.login_failed event
    login_failed_events = [e for e in events if e.get("action") == "auth.login_failed"]
    
    if not login_failed_events:
        result.add_result("Failed Login Audit", False, "No auth.login_failed audit event found")
        return
    
    event = login_failed_events[0]  # Most recent
    
    # Verify required fields
    required_fields = ["request_id", "tenant_id", "action", "resource_type", "result", "timestamp", "ip_address"]
    missing_fields = [f for f in required_fields if not event.get(f)]
    
    if missing_fields:
        result.add_result("Failed Login Audit", False, f"Missing required fields: {missing_fields}")
        return
    
    # Verify specific values
    checks = []
    if event.get("action") != "auth.login_failed":
        checks.append(f"action={event.get('action')} (expected auth.login_failed)")
    if event.get("resource_type") != "auth":
        checks.append(f"resource_type={event.get('resource_type')} (expected auth)")
    if event.get("result") != "failed":
        checks.append(f"result={event.get('result')} (expected failed)")
    
    # Verify actor_user_id (can be 'unknown' or actual id)
    actor_user_id = event.get("actor_user_id")
    if not actor_user_id:
        checks.append("actor_user_id is missing")
    
    # Verify resource_id is 64 hex chars (sha256 surrogate)
    resource_id = event.get("resource_id", "")
    if not re.match(r'^[a-f0-9]{64}$', resource_id):
        checks.append(f"resource_id not 64 hex chars: {resource_id}")
    
    # Verify details.failure_reason
    details = event.get("details", {})
    failure_reason = details.get("failure_reason")
    allowed_reasons = ["INVALID_CREDENTIALS", "USER_DISABLED", "ACCOUNT_LOCKED"]
    if failure_reason not in allowed_reasons:
        checks.append(f"failure_reason={failure_reason} not in allowed values: {allowed_reasons}")
    
    # Verify no sensitive data in details
    details_str = json.dumps(details).lower()
    sensitive_terms = ["password", "token", "authorization", "cookie", "wrongpassword123!"]
    found_sensitive = [term for term in sensitive_terms if term in details_str]
    if found_sensitive:
        checks.append(f"Sensitive data found in details: {found_sensitive}")
    
    if checks:
        result.add_result("Failed Login Audit", False, f"Validation failures: {'; '.join(checks)}")
    else:
        result.add_result("Failed Login Audit", True, f"All validations passed. Event ID: {event.get('id')}")

def test_rate_limited_audit(result: TestResult) -> None:
    """Test 3: Rate limiting creates auth.login_rate_limited audit event"""
    print("\n3. Testing Rate Limited Audit Event...")
    
    # First get a valid token to check audit events
    valid_login = {
        "email": "admin@casino.com",
        "password": "Admin123!"
    }
    temp_response = make_request("POST", "/v1/auth/login", json_data=valid_login)
    if temp_response["status_code"] != 200:
        result.add_result("Rate Limited Audit", False, "Cannot get token for audit check")
        return
    
    token = temp_response["json"]["access_token"]
    
    # Trigger rate limiting by making multiple failed login attempts
    failed_login_data = {
        "email": "admin@casino.com",
        "password": "WrongPassword123!"
    }
    
    print("   Triggering rate limit with multiple failed attempts...")
    rate_limited = False
    
    # Make 6 attempts to exceed the 5/min limit
    for i in range(6):
        response = make_request("POST", "/v1/auth/login", json_data=failed_login_data)
        print(f"   Attempt {i+1}: Status {response['status_code']}")
        
        if response["status_code"] == 429:
            rate_limited = True
            break
        elif i < 5 and response["status_code"] != 401:
            result.add_result("Rate Limited Audit", False, f"Unexpected status on attempt {i+1}: {response['status_code']}")
            return
    
    if not rate_limited:
        result.add_result("Rate Limited Audit", False, "Rate limiting not triggered after 6 attempts")
        return
    
    # Wait for audit event
    time.sleep(2)
    
    # Get audit events after rate limiting
    after_response = get_recent_audit_events(token)
    if after_response["status_code"] != 200:
        result.add_result("Rate Limited Audit", False, f"Cannot fetch audit events: {after_response['status_code']}")
        return
    
    events = after_response["json"].get("items", [])
    
    # Find auth.login_rate_limited event
    rate_limited_events = [e for e in events if e.get("action") == "auth.login_rate_limited"]
    
    if not rate_limited_events:
        result.add_result("Rate Limited Audit", False, "No auth.login_rate_limited audit event found")
        return
    
    event = rate_limited_events[0]  # Most recent
    
    # Verify required fields
    required_fields = ["request_id", "tenant_id", "action", "resource_type", "result", "timestamp", "ip_address"]
    missing_fields = [f for f in required_fields if not event.get(f)]
    
    if missing_fields:
        result.add_result("Rate Limited Audit", False, f"Missing required fields: {missing_fields}")
        return
    
    # Verify specific values
    checks = []
    if event.get("action") != "auth.login_rate_limited":
        checks.append(f"action={event.get('action')} (expected auth.login_rate_limited)")
    if event.get("resource_type") != "auth":
        checks.append(f"resource_type={event.get('resource_type')} (expected auth)")
    if event.get("result") != "rate_limited":
        checks.append(f"result={event.get('result')} (expected rate_limited)")
    
    # Verify details structure
    details = event.get("details", {})
    if details.get("limit") != "5/min":
        checks.append(f"details.limit={details.get('limit')} (expected 5/min)")
    if details.get("window_sec") != 60:
        checks.append(f"details.window_sec={details.get('window_sec')} (expected 60)")
    
    if checks:
        result.add_result("Rate Limited Audit", False, f"Validation failures: {'; '.join(checks)}")
    else:
        result.add_result("Rate Limited Audit", True, f"All validations passed. Event ID: {event.get('id')}")

def test_logout_audit(result: TestResult, token: str) -> None:
    """Test 4: Logout endpoint (if exists) creates auth.logout audit event"""
    print("\n4. Testing Logout Audit Event...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Check if logout endpoint exists
    response = make_request("POST", "/v1/auth/logout", headers=headers)
    print(f"   POST /api/v1/auth/logout: Status {response['status_code']}")
    
    if response["status_code"] == 404:
        result.add_result("Logout Audit", True, "Logout endpoint not implemented (as expected)")
        return
    elif response["status_code"] == 405:
        # Try GET method
        response = make_request("GET", "/v1/auth/logout", headers=headers)
        print(f"   GET /api/v1/auth/logout: Status {response['status_code']}")
        
        if response["status_code"] == 404:
            result.add_result("Logout Audit", True, "Logout endpoint not implemented (as expected)")
            return
    
    if response["status_code"] not in [200, 204]:
        result.add_result("Logout Audit", False, f"Logout endpoint exists but returned unexpected status: {response['status_code']}")
        return
    
    # If logout endpoint exists and works, check for audit event
    time.sleep(1)
    
    # Get audit events after logout
    # Note: We need a new token since logout might invalidate the current one
    new_login = make_request("POST", "/v1/auth/login", json_data={"email": "admin@casino.com", "password": "Admin123!"})
    if new_login["status_code"] != 200:
        result.add_result("Logout Audit", False, "Cannot get new token to check audit events after logout")
        return
    
    new_token = new_login["json"]["access_token"]
    after_response = get_recent_audit_events(new_token)
    
    if after_response["status_code"] != 200:
        result.add_result("Logout Audit", False, f"Cannot fetch audit events: {after_response['status_code']}")
        return
    
    events = after_response["json"].get("items", [])
    
    # Find auth.logout event
    logout_events = [e for e in events if e.get("action") == "auth.logout"]
    
    if not logout_events:
        result.add_result("Logout Audit", False, "Logout endpoint exists but no auth.logout audit event found")
        return
    
    event = logout_events[0]  # Most recent
    
    # Verify required fields
    required_fields = ["request_id", "tenant_id", "action", "resource_type", "result", "timestamp", "ip_address"]
    missing_fields = [f for f in required_fields if not event.get(f)]
    
    if missing_fields:
        result.add_result("Logout Audit", False, f"Missing required fields: {missing_fields}")
        return
    
    # Verify specific values
    checks = []
    if event.get("action") != "auth.logout":
        checks.append(f"action={event.get('action')} (expected auth.logout)")
    if event.get("resource_type") != "auth":
        checks.append(f"resource_type={event.get('resource_type')} (expected auth)")
    
    if checks:
        result.add_result("Logout Audit", False, f"Validation failures: {'; '.join(checks)}")
    else:
        result.add_result("Logout Audit", True, f"Logout endpoint working with audit event. Event ID: {event.get('id')}")

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