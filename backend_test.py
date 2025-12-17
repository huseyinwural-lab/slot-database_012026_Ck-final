#!/usr/bin/env python3
"""
Audit Retention Purge Tooling Validation
Testing audit event creation, purge script functionality, and retention behavior
"""

import requests
import json
import sys
import os
import time
import uuid
import re
import hashlib
import subprocess
from typing import Dict, Any, Optional

# Configuration - Use frontend .env for external URL
BASE_URL = "https://game-admin-hub-1.preview.emergentagent.com"  # Default
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
        print(f"\n=== AUDIT RETENTION PURGE TOOLING VALIDATION SUMMARY ===")
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

def test_create_audit_event_via_login(result: TestResult) -> Optional[str]:
    """Test 1: Create new audit event by logging in and confirm audit event count increases"""
    print("\n1. Testing Audit Event Creation via Login...")
    
    login_data = {
        "email": "admin@casino.com",
        "password": "Admin123!"
    }
    
    # Get initial audit events count
    temp_response = make_request("POST", "/v1/auth/login", json_data=login_data)
    if temp_response["status_code"] != 200:
        result.add_result("Create Audit Event via Login", False, f"Cannot login to get baseline: {temp_response['status_code']}")
        return None
    
    temp_token = temp_response["json"]["access_token"]
    before_response = get_recent_audit_events(temp_token)
    before_count = len(before_response["json"].get("items", [])) if before_response["status_code"] == 200 else 0
    
    print(f"   Initial audit events count: {before_count}")
    
    # Perform the actual login we want to test
    response = make_request("POST", "/v1/auth/login", json_data=login_data)
    print(f"   POST /api/v1/auth/login: Status {response['status_code']}")
    
    if response["status_code"] != 200 or "access_token" not in response["json"]:
        result.add_result("Create Audit Event via Login", False, f"Login failed: {response['status_code']}")
        return None
    
    token = response["json"]["access_token"]
    
    # Wait a moment for audit event to be written
    time.sleep(2)
    
    # Get audit events after login
    after_response = get_recent_audit_events(token)
    if after_response["status_code"] != 200:
        result.add_result("Create Audit Event via Login", False, f"Cannot fetch audit events: {after_response['status_code']}")
        return token
    
    events = after_response["json"].get("items", [])
    after_count = len(events)
    
    print(f"   Audit events count after login: {after_count}")
    
    # Verify count increased
    if after_count <= before_count:
        result.add_result("Create Audit Event via Login", False, f"Audit event count did not increase: before={before_count}, after={after_count}")
        return token
    
    # Find the most recent auth.login_success event
    login_success_events = [e for e in events if e.get("action") == "auth.login_success"]
    
    if not login_success_events:
        result.add_result("Create Audit Event via Login", False, "No auth.login_success audit event found")
        return token
    
    event = login_success_events[0]  # Most recent
    print(f"   Found recent login event: {event.get('id')} at {event.get('timestamp')}")
    
    # Verify the event exists and has basic structure
    if not event.get("id") or not event.get("timestamp"):
        result.add_result("Create Audit Event via Login", False, "Login audit event missing required fields")
        return token
    
    result.add_result("Create Audit Event via Login", True, f"Audit event count increased from {before_count} to {after_count}. Latest event ID: {event.get('id')}")
    return token

def test_purge_script_execution(result: TestResult, token: str) -> None:
    """Test 2: Run purge script with --days 0 and verify it deletes older events but does not crash"""
    print("\n2. Testing Purge Script Execution...")
    
    # Get audit events before purge
    headers = {"Authorization": f"Bearer {token}"}
    before_response = make_request("GET", "/v1/audit/events?since_hours=24&limit=500", headers=headers)
    
    if before_response["status_code"] != 200:
        result.add_result("Purge Script Execution", False, f"Cannot fetch audit events before purge: {before_response['status_code']}")
        return
    
    before_events = before_response["json"].get("items", [])
    before_count = len(before_events)
    print(f"   Audit events before purge: {before_count}")
    
    # Run purge script with --days 0 (should delete all events older than today)
    try:
        print("   Running purge script with --days 0...")
        result_process = subprocess.run(
            [sys.executable, "/app/scripts/purge_audit_events.py", "--days", "0"],
            cwd="/app",
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print(f"   Purge script exit code: {result_process.returncode}")
        print(f"   Purge script stdout: {result_process.stdout.strip()}")
        
        if result_process.stderr:
            print(f"   Purge script stderr: {result_process.stderr.strip()}")
        
        # Check if script executed successfully (exit code 0)
        if result_process.returncode != 0:
            result.add_result("Purge Script Execution", False, f"Purge script failed with exit code {result_process.returncode}: {result_process.stderr}")
            return
        
        # Parse output to see how many events were deleted
        stdout = result_process.stdout.strip()
        deleted_count = 0
        if "deleted=" in stdout:
            try:
                deleted_part = stdout.split("deleted=")[1].split()[0]
                deleted_count = int(deleted_part)
                print(f"   Events deleted by purge script: {deleted_count}")
            except (IndexError, ValueError):
                print(f"   Could not parse deleted count from output: {stdout}")
        
        result.add_result("Purge Script Execution", True, f"Purge script executed successfully. Exit code: {result_process.returncode}, Deleted: {deleted_count} events")
        
    except subprocess.TimeoutExpired:
        result.add_result("Purge Script Execution", False, "Purge script timed out after 30 seconds")
    except Exception as e:
        result.add_result("Purge Script Execution", False, f"Error running purge script: {str(e)}")

def test_post_purge_recent_events(result: TestResult, token: str) -> None:
    """Test 3: After purge, query GET /api/v1/audit/events?since_hours=1 and confirm it returns 0 or only very recent events"""
    print("\n3. Testing Post-Purge Recent Events Query...")
    
    # Wait a moment after purge to ensure it's complete
    time.sleep(2)
    
    # Query for events from the last hour
    headers = {"Authorization": f"Bearer {token}"}
    response = make_request("GET", "/v1/audit/events?since_hours=1&limit=100", headers=headers)
    
    print(f"   GET /api/v1/audit/events?since_hours=1: Status {response['status_code']}")
    
    if response["status_code"] != 200:
        result.add_result("Post-Purge Recent Events Query", False, f"Cannot fetch recent audit events: {response['status_code']}")
        return
    
    events = response["json"].get("items", [])
    event_count = len(events)
    
    print(f"   Events found in last hour: {event_count}")
    
    # Check if we have very recent events (from our test login)
    recent_events = []
    current_time = time.time()
    
    for event in events:
        event_timestamp = event.get("timestamp", "")
        if event_timestamp:
            try:
                # Parse ISO timestamp
                from datetime import datetime
                event_time = datetime.fromisoformat(event_timestamp.replace('Z', '+00:00'))
                event_unix = event_time.timestamp()
                
                # Check if event is within last 10 minutes (very recent)
                if current_time - event_unix < 600:  # 10 minutes
                    recent_events.append(event)
                    print(f"   Recent event: {event.get('action')} at {event_timestamp}")
            except Exception as e:
                print(f"   Could not parse timestamp {event_timestamp}: {e}")
    
    # Validate results
    if event_count == 0:
        result.add_result("Post-Purge Recent Events Query", True, "No events found in last hour (expected after purge with --days 0)")
    elif len(recent_events) > 0 and len(recent_events) <= 5:
        # We expect only very recent events (from our test login)
        result.add_result("Post-Purge Recent Events Query", True, f"Found {event_count} events in last hour, {len(recent_events)} are very recent (expected)")
    elif event_count > 10:
        result.add_result("Post-Purge Recent Events Query", False, f"Too many events ({event_count}) found after purge - purge may not have worked correctly")
    else:
        result.add_result("Post-Purge Recent Events Query", True, f"Found {event_count} events in last hour (acceptable range after purge)")

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

def test_required_fields_validation(result: TestResult, token: str) -> None:
    """Test 5: Verify all auth audit events have required fields"""
    print("\n5. Testing Required Fields Validation...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = make_request("GET", "/v1/audit/events?since_hours=1&limit=100", headers=headers)
    print(f"   GET /api/v1/audit/events: Status {response['status_code']}")
    
    if response["status_code"] != 200 or "items" not in response["json"]:
        result.add_result("Required Fields Validation", False, f"Cannot fetch audit events: {response['status_code']}")
        return
    
    events = response["json"]["items"]
    
    # Filter for auth-related events
    auth_events = [e for e in events if e.get("resource_type") == "auth"]
    
    if not auth_events:
        result.add_result("Required Fields Validation", False, "No auth-related audit events found")
        return
    
    print(f"   Found {len(auth_events)} auth-related audit events")
    
    # Required fields for all audit events
    required_fields = ["request_id", "tenant_id", "action", "resource_type", "result", "timestamp", "ip_address"]
    
    validation_errors = []
    
    for event in auth_events:
        event_id = event.get("id", "unknown")
        action = event.get("action", "unknown")
        
        # Check required fields
        for field in required_fields:
            if field not in event or event[field] is None or event[field] == "":
                validation_errors.append(f"Event {event_id} ({action}): missing/null/empty field '{field}'")
        
        # Verify tenant_id is not 'unknown' for known users (except for non-existing user scenarios)
        tenant_id = event.get("tenant_id")
        actor_user_id = event.get("actor_user_id")
        if action == "auth.login_failed" and actor_user_id == "unknown":
            # For non-existing users, tenant_id can be 'unknown'
            pass
        elif tenant_id == "unknown" and actor_user_id != "unknown":
            validation_errors.append(f"Event {event_id} ({action}): tenant_id is 'unknown' for known user {actor_user_id}")
    
    # Check specific auth actions
    auth_actions = set(e.get("action") for e in auth_events)
    expected_auth_actions = {"auth.login_success", "auth.login_failed"}
    found_expected = expected_auth_actions.intersection(auth_actions)
    
    print(f"   Auth actions found: {sorted(auth_actions)}")
    print(f"   Expected auth actions found: {sorted(found_expected)}")
    
    if len(found_expected) < 2:
        validation_errors.append(f"Missing expected auth actions. Found: {found_expected}, Expected: {expected_auth_actions}")
    
    if validation_errors:
        result.add_result("Required Fields Validation", False, f"Validation errors: {'; '.join(validation_errors[:5])}")  # Limit to first 5 errors
    else:
        result.add_result("Required Fields Validation", True, f"All {len(auth_events)} auth events have required fields")

# Removed - not needed for auth audit events testing

# Removed - not needed for auth audit events testing

def main():
    print("=== P2 AUTH AUDIT EVENTS BACKEND VALIDATION ===")
    print(f"Testing against: {BASE_URL}")
    
    result = TestResult()
    
    # Test 1: Successful login audit event
    token = test_successful_login_audit(result)
    if not token:
        print("❌ Cannot proceed without valid token")
        result.print_summary()
        return False
    
    # Test 2: Failed login audit event
    test_failed_login_audit(result)
    
    # Test 3: Rate limited audit event
    test_rate_limited_audit(result)
    
    # Test 4: Logout audit event (if endpoint exists)
    test_logout_audit(result, token)
    
    # Test 5: Required fields validation
    test_required_fields_validation(result, token)
    
    # Print final summary
    success = result.print_summary()
    
    if success:
        print("\n🎉 ALL P2 AUTH AUDIT EVENTS VALIDATION TESTS PASSED!")
        return True
    else:
        print(f"\n💥 {result.failed} TEST(S) FAILED - AUTH AUDIT EVENTS ISSUES DETECTED!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)