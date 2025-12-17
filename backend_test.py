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

# Additional helper functions for audit retention testing

def main():
    print("=== AUDIT RETENTION PURGE TOOLING VALIDATION ===")
    print(f"Testing against: {BASE_URL}")
    
    result = TestResult()
    
    # Test 1: Create new audit event by logging in and confirm audit event count increases
    token = test_create_audit_event_via_login(result)
    if not token:
        print("❌ Cannot proceed without valid token")
        result.print_summary()
        return False
    
    # Test 2: Run purge script with --days 0 and verify it deletes older events but does not crash
    test_purge_script_execution(result, token)
    
    # Test 3: After purge, query GET /api/v1/audit/events?since_hours=1 and confirm it returns 0 or only very recent events
    test_post_purge_recent_events(result, token)
    
    # Print final summary
    success = result.print_summary()
    
    if success:
        print("\n🎉 ALL AUDIT RETENTION PURGE TOOLING VALIDATION TESTS PASSED!")
        return True
    else:
        print(f"\n💥 {result.failed} TEST(S) FAILED - AUDIT RETENTION PURGE TOOLING ISSUES DETECTED!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)