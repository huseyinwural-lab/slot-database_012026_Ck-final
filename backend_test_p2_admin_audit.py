#!/usr/bin/env python3
"""
P2 Backlog #2 - Admin Change Audit Events End-to-End Testing
Testing admin user changes and their corresponding audit events with PII redaction
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
BASE_URL = "https://payout-system-7.preview.emergentagent.com"  # Default
try:
    with open("/app/frontend/.env", "r") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip()
                break
except FileNotFoundError:
    pass

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
        print(f"\n=== P2 ADMIN CHANGE AUDIT EVENTS VALIDATION SUMMARY ===")
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

def test_owner_login(result: TestResult) -> Optional[str]:
    """Test 1: Owner login and get token"""
    print("\n1. Testing Owner Login...")
    
    login_data = {
        "email": "admin@casino.com",
        "password": "Admin123!"
    }
    
    response = make_request("POST", "/v1/auth/login", json_data=login_data)
    print(f"   POST /api/v1/auth/login: Status {response['status_code']}")
    
    if response["status_code"] != 200 or "access_token" not in response["json"]:
        result.add_result("Owner Login", False, f"Login failed: {response['status_code']}")
        return None
    
    token = response["json"]["access_token"]
    result.add_result("Owner Login", True, f"Token obtained (length: {len(token)} chars)")
    return token

def test_create_admin_user(result: TestResult, token: str) -> Optional[str]:
    """Test 2: Create a new admin user (invite) in default_casino"""
    print("\n2. Testing Admin User Creation...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Generate unique email for this test run
    test_email = f"test.admin.{int(time.time())}@casino.com"
    
    admin_data = {
        "email": test_email,
        "full_name": "Test Admin User",
        "role": "Admin",
        "tenant_role": "tenant_admin",
        "password_mode": "invite",
        "tenant_id": "default_casino"
    }
    
    response = make_request("POST", "/v1/admin/users", headers=headers, json_data=admin_data)
    print(f"   POST /api/v1/admin/users: Status {response['status_code']}")
    
    if response["status_code"] != 200:
        result.add_result("Create Admin User", False, f"Admin creation failed: {response['status_code']} - {response['json']}")
        return None
    
    # Get the created admin ID by listing admins
    list_response = make_request("GET", "/v1/admin/users", headers=headers)
    if list_response["status_code"] != 200:
        result.add_result("Create Admin User", False, "Cannot list admins to get created user ID")
        return None
    
    admins = list_response["json"]
    created_admin = None
    for admin in admins:
        if admin.get("email") == test_email:
            created_admin = admin
            break
    
    if not created_admin:
        result.add_result("Create Admin User", False, "Created admin not found in list")
        return None
    
    admin_id = created_admin["id"]
    result.add_result("Create Admin User", True, f"Admin created with ID: {admin_id}")
    return admin_id

def test_admin_user_updates(result: TestResult, token: str, admin_id: str) -> None:
    """Test 3: Call PATCH /api/v1/admin/users/{id} with various changes"""
    print("\n3. Testing Admin User Updates...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 3a: Full name change (safe field)
    print("   3a. Testing full_name change (safe field)...")
    update_data = {
        "full_name": "Updated Test Admin User"
    }
    
    response = make_request("PATCH", f"/v1/admin/users/{admin_id}", headers=headers, json_data=update_data)
    print(f"   PATCH /api/v1/admin/users/{admin_id} (full_name): Status {response['status_code']}")
    
    if response["status_code"] != 200:
        result.add_result("Admin Update - Full Name", False, f"Full name update failed: {response['status_code']}")
    else:
        result.add_result("Admin Update - Full Name", True, "Full name updated successfully")
    
    time.sleep(1)  # Wait for audit event
    
    # Test 3b: Email change (PII - must be surrogate only in audit)
    print("   3b. Testing email change (PII field)...")
    new_email = f"updated.test.admin.{int(time.time())}@casino.com"
    update_data = {
        "email": new_email
    }
    
    response = make_request("PATCH", f"/v1/admin/users/{admin_id}", headers=headers, json_data=update_data)
    print(f"   PATCH /api/v1/admin/users/{admin_id} (email): Status {response['status_code']}")
    
    if response["status_code"] != 200:
        result.add_result("Admin Update - Email", False, f"Email update failed: {response['status_code']}")
    else:
        result.add_result("Admin Update - Email", True, "Email updated successfully")
    
    time.sleep(1)  # Wait for audit event
    
    # Test 3c: Role change (should also emit admin.user_role_changed)
    print("   3c. Testing role change...")
    update_data = {
        "role": "Senior Admin"
    }
    
    response = make_request("PATCH", f"/v1/admin/users/{admin_id}", headers=headers, json_data=update_data)
    print(f"   PATCH /api/v1/admin/users/{admin_id} (role): Status {response['status_code']}")
    
    if response["status_code"] != 200:
        result.add_result("Admin Update - Role", False, f"Role update failed: {response['status_code']}")
    else:
        result.add_result("Admin Update - Role", True, "Role updated successfully")
    
    time.sleep(1)  # Wait for audit event

def test_admin_status_changes(result: TestResult, token: str, admin_id: str) -> None:
    """Test 4: Call POST /api/v1/admin/users/{id}/status twice"""
    print("\n4. Testing Admin Status Changes...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 4a: Disable admin (is_active=false -> admin.user_disabled)
    print("   4a. Testing admin disable...")
    status_data = {
        "is_active": False
    }
    
    response = make_request("POST", f"/v1/admin/users/{admin_id}/status", headers=headers, json_data=status_data)
    print(f"   POST /api/v1/admin/users/{admin_id}/status (disable): Status {response['status_code']}")
    
    if response["status_code"] != 200:
        result.add_result("Admin Status - Disable", False, f"Admin disable failed: {response['status_code']}")
    else:
        result.add_result("Admin Status - Disable", True, "Admin disabled successfully")
    
    time.sleep(1)  # Wait for audit event
    
    # Test 4b: Enable admin (is_active=true -> admin.user_enabled)
    print("   4b. Testing admin enable...")
    status_data = {
        "is_active": True
    }
    
    response = make_request("POST", f"/v1/admin/users/{admin_id}/status", headers=headers, json_data=status_data)
    print(f"   POST /api/v1/admin/users/{admin_id}/status (enable): Status {response['status_code']}")
    
    if response["status_code"] != 200:
        result.add_result("Admin Status - Enable", False, f"Admin enable failed: {response['status_code']}")
    else:
        result.add_result("Admin Status - Enable", True, "Admin enabled successfully")
    
    time.sleep(1)  # Wait for audit event

def test_audit_events_query(result: TestResult, token: str) -> None:
    """Test 5: Query audit endpoint for various actions"""
    print("\n5. Testing Audit Events Query...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test each expected audit action
    expected_actions = [
        "admin.user_updated",
        "admin.user_role_changed", 
        "admin.user_disabled",
        "admin.user_enabled"
    ]
    
    for action in expected_actions:
        print(f"   5.{expected_actions.index(action) + 1}. Querying {action}...")
        
        response = make_request("GET", f"/v1/audit/events?action={action}&since_hours=1&limit=50", headers=headers)
        print(f"   GET /api/v1/audit/events?action={action}: Status {response['status_code']}")
        
        if response["status_code"] != 200:
            result.add_result(f"Audit Query - {action}", False, f"Query failed: {response['status_code']}")
            continue
        
        events = response["json"].get("items", [])
        if not events:
            result.add_result(f"Audit Query - {action}", False, f"No {action} events found")
            continue
        
        result.add_result(f"Audit Query - {action}", True, f"Found {len(events)} {action} events")

def test_audit_event_assertions(result: TestResult, token: str) -> None:
    """Test 6: Verify audit event structure and PII redaction"""
    print("\n6. Testing Audit Event Assertions...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get recent admin audit events
    response = make_request("GET", "/v1/audit/events?action=admin.user_updated&since_hours=1&limit=10", headers=headers)
    
    if response["status_code"] != 200:
        result.add_result("Audit Assertions", False, f"Cannot fetch audit events: {response['status_code']}")
        return
    
    events = response["json"].get("items", [])
    if not events:
        result.add_result("Audit Assertions", False, "No admin.user_updated events found for validation")
        return
    
    # Test the most recent admin.user_updated event
    event = events[0]
    
    print(f"   Testing event ID: {event.get('id')}")
    
    # Test 6a: Required canonical fields exist
    required_fields = [
        "request_id", "actor_user_id", "tenant_id", "action", 
        "resource_type", "resource_id", "result", "timestamp", "ip_address"
    ]
    
    missing_fields = []
    for field in required_fields:
        if field not in event or event[field] is None or event[field] == "":
            missing_fields.append(field)
    
    if missing_fields:
        result.add_result("Audit Assertions - Required Fields", False, f"Missing required fields: {missing_fields}")
    else:
        result.add_result("Audit Assertions - Required Fields", True, "All required canonical fields present")
    
    # Test 6b: Email PII redaction in details.changed.email
    details = event.get("details", {})
    changed = details.get("changed", {})
    
    if "email" in changed:
        email_change = changed["email"]
        
        # Check if it's properly redacted (should have changed, before_hash, after_hash)
        if isinstance(email_change, dict) and "changed" in email_change:
            if (email_change.get("changed") is True and 
                "before_hash" in email_change and 
                "after_hash" in email_change):
                
                # Verify hashes are 64 hex chars
                before_hash = email_change.get("before_hash", "")
                after_hash = email_change.get("after_hash", "")
                
                if (re.match(r'^[a-f0-9]{64}$', before_hash) and 
                    re.match(r'^[a-f0-9]{64}$', after_hash)):
                    result.add_result("Audit Assertions - Email PII Redaction", True, "Email properly redacted with SHA256 hashes")
                else:
                    result.add_result("Audit Assertions - Email PII Redaction", False, f"Invalid hash format: before={before_hash}, after={after_hash}")
            else:
                result.add_result("Audit Assertions - Email PII Redaction", False, f"Email change structure invalid: {email_change}")
        else:
            # Check if raw email appears (should not)
            details_str = json.dumps(details).lower()
            if "@casino.com" in details_str:
                result.add_result("Audit Assertions - Email PII Redaction", False, "Raw email found in audit details")
            else:
                result.add_result("Audit Assertions - Email PII Redaction", True, "No raw email in details (may not have email change in this event)")
    else:
        result.add_result("Audit Assertions - Email PII Redaction", True, "No email change in this event (expected for some updates)")
    
    # Test 6c: Safe fields (full_name/role) contain raw values
    safe_field_found = False
    for field in ["full_name", "role", "tenant_role"]:
        if field in changed:
            field_change = changed[field]
            if isinstance(field_change, dict) and "before" in field_change and "after" in field_change:
                safe_field_found = True
                result.add_result(f"Audit Assertions - Safe Field {field}", True, f"Safe field {field} contains raw before/after values")
                break
    
    if not safe_field_found:
        result.add_result("Audit Assertions - Safe Fields", True, "No safe field changes in this event (may be email-only change)")
    
    # Test 6d: No sensitive data leaked
    details_str = json.dumps(details).lower()
    sensitive_terms = ["password", "token", "authorization", "cookie", "secret"]
    leaked_terms = [term for term in sensitive_terms if term in details_str]
    
    if leaked_terms:
        result.add_result("Audit Assertions - No Sensitive Data", False, f"Sensitive data leaked: {leaked_terms}")
    else:
        result.add_result("Audit Assertions - No Sensitive Data", True, "No sensitive data found in audit details")

def main():
    print("=== P2 ADMIN CHANGE AUDIT EVENTS END-TO-END VALIDATION ===")
    print(f"Testing against: {BASE_URL}")
    
    result = TestResult()
    
    # Test 1: Owner login and get token
    token = test_owner_login(result)
    if not token:
        print("❌ Cannot proceed without valid token")
        result.print_summary()
        return False
    
    # Test 2: Create a new admin user (invite) in default_casino
    admin_id = test_create_admin_user(result, token)
    if not admin_id:
        print("❌ Cannot proceed without created admin user")
        result.print_summary()
        return False
    
    # Test 3: Call PATCH /api/v1/admin/users/{id} with various changes
    test_admin_user_updates(result, token, admin_id)
    
    # Test 4: Call POST /api/v1/admin/users/{id}/status twice
    test_admin_status_changes(result, token, admin_id)
    
    # Test 5: Query audit endpoint for various actions
    test_audit_events_query(result, token)
    
    # Test 6: Verify audit event structure and PII redaction
    test_audit_event_assertions(result, token)
    
    # Print final summary
    success = result.print_summary()
    
    if success:
        print("\n🎉 ALL P2 ADMIN CHANGE AUDIT EVENTS VALIDATION TESTS PASSED!")
        return True
    else:
        print(f"\n💥 {result.failed} TEST(S) FAILED - ADMIN AUDIT EVENTS ISSUES DETECTED!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)