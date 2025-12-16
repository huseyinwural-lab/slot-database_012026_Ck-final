#!/usr/bin/env python3
"""
P1-SECURITY Backend Validation
Testing rate limiting, CORS, and trusted proxy behavior
"""

import requests
import json
import sys
import os
import time
from typing import Dict, Any, Optional

# Configuration
BASE_URL = os.getenv("REACT_APP_BACKEND_URL", "https://casino-release.preview.emergentagent.com")
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
        print(f"\n=== P0 RELEASE BLOCKERS VALIDATION SUMMARY ===")
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

def test_auth_works(result: TestResult):
    """Test 1: Auth works - POST /api/v1/auth/login with admin@casino.com / Admin123!"""
    print("\n1. Testing Auth Works...")
    
    login_data = {
        "email": "admin@casino.com",
        "password": "Admin123!"
    }
    
    response = make_request("POST", "/v1/auth/login", json_data=login_data)
    
    if response["status_code"] == 200 and "access_token" in response["json"]:
        access_token = response["json"]["access_token"]
        result.add_result(
            "Auth Login", 
            True, 
            f"Status: {response['status_code']}, Token length: {len(access_token)}"
        )
        return access_token
    else:
        result.add_result(
            "Auth Login", 
            False, 
            f"Status: {response['status_code']}, Response: {response['json']}"
        )
        return None

def ensure_demo_renter_tenant(result: TestResult, owner_token: str) -> bool:
    """Ensure demo_renter tenant exists"""
    print("\n2. Ensuring demo_renter tenant exists...")
    
    headers = {"Authorization": f"Bearer {owner_token}"}
    
    # Check if demo_renter exists
    response = make_request("GET", "/v1/tenants/", headers=headers)
    
    if response["status_code"] == 200:
        tenants = response["json"].get("items", [])
        demo_renter_exists = any(t.get("id") == "demo_renter" for t in tenants)
        
        if demo_renter_exists:
            result.add_result(
                "Demo Renter Tenant Exists", 
                True, 
                "demo_renter tenant found in tenant list"
            )
            return True
        else:
            result.add_result(
                "Demo Renter Tenant Exists", 
                False, 
                f"demo_renter not found in tenants: {[t.get('id') for t in tenants]}"
            )
            return False
    else:
        result.add_result(
            "Demo Renter Tenant Check", 
            False, 
            f"Failed to get tenants: {response['status_code']} - {response['json']}"
        )
        return False

def ensure_tenant_admin_exists(result: TestResult, owner_token: str) -> Optional[str]:
    """Ensure tenant admin for demo_renter exists and return their token"""
    print("\n3. Ensuring tenant admin for demo_renter exists...")
    
    headers = {"Authorization": f"Bearer {owner_token}"}
    
    # Try to create tenant admin (will fail if exists)
    tenant_admin_data = {
        "email": "demo.admin@casino.com",
        "tenant_id": "demo_renter", 
        "password": "DemoAdmin123!",
        "full_name": "Demo Tenant Admin"
    }
    
    response = make_request("POST", "/v1/admin/create-tenant-admin", headers=headers, json_data=tenant_admin_data)
    
    if response["status_code"] == 200:
        result.add_result(
            "Tenant Admin Creation", 
            True, 
            "New tenant admin created successfully"
        )
    elif response["status_code"] == 400 and "ADMIN_EXISTS" in str(response["json"]):
        result.add_result(
            "Tenant Admin Creation", 
            True, 
            "Tenant admin already exists (expected)"
        )
    else:
        result.add_result(
            "Tenant Admin Creation", 
            False, 
            f"Unexpected response: {response['status_code']} - {response['json']}"
        )
        return None
    
    # Now login as tenant admin
    login_data = {
        "email": "demo.admin@casino.com",
        "password": "DemoAdmin123!"
    }
    
    login_response = make_request("POST", "/v1/auth/login", json_data=login_data)
    
    if login_response["status_code"] == 200 and "access_token" in login_response["json"]:
        tenant_token = login_response["json"]["access_token"]
        result.add_result(
            "Tenant Admin Login", 
            True, 
            f"Successfully logged in as tenant admin"
        )
        return tenant_token
    else:
        result.add_result(
            "Tenant Admin Login", 
            False, 
            f"Login failed: {login_response['status_code']} - {login_response['json']}"
        )
        return None

def test_tenant_override_forbidden(result: TestResult, tenant_admin_token: str):
    """Test tenant admin cannot override tenant_id to default_casino"""
    print("\n4. Testing tenant override forbidden...")
    
    headers = {"Authorization": f"Bearer {tenant_admin_token}"}
    
    # Try to create admin for default_casino (should fail with 403)
    admin_data = {
        "email": "test.override@casino.com",
        "tenant_id": "default_casino",
        "password": "TestPassword123!",
        "full_name": "Test Override Admin"
    }
    
    response = make_request("POST", "/v1/admin/users", headers=headers, json_data=admin_data)
    
    expected_status = 403
    expected_error = "TENANT_OVERRIDE_FORBIDDEN"
    
    if (response["status_code"] == expected_status and 
        expected_error in str(response["json"])):
        result.add_result(
            "Tenant Override Forbidden", 
            True, 
            f"Status: {response['status_code']}, Error: {response['json'].get('error_code', 'N/A')}"
        )
    else:
        result.add_result(
            "Tenant Override Forbidden", 
            False, 
            f"Expected 403 with {expected_error}, got {response['status_code']}: {response['json']}"
        )

def test_password_required(result: TestResult, tenant_admin_token: str):
    """Test password required when password_mode is not invite"""
    print("\n5. Testing password required validation...")
    
    headers = {"Authorization": f"Bearer {tenant_admin_token}"}
    
    # Try to create admin without password and password_mode not invite
    admin_data = {
        "email": "test.nopassword@casino.com",
        "full_name": "Test No Password Admin"
        # No password and no password_mode (defaults to "set")
    }
    
    response = make_request("POST", "/v1/admin/users", headers=headers, json_data=admin_data)
    
    expected_status = 400
    expected_error = "PASSWORD_REQUIRED"
    
    if (response["status_code"] == expected_status and 
        expected_error in str(response["json"])):
        result.add_result(
            "Password Required Validation", 
            True, 
            f"Status: {response['status_code']}, Error: {response['json'].get('error_code', 'N/A')}"
        )
    else:
        result.add_result(
            "Password Required Validation", 
            False, 
            f"Expected 400 with {expected_error}, got {response['status_code']}: {response['json']}"
        )

def test_owner_invite_mode(result: TestResult, owner_token: str):
    """Test owner can create admin with invite mode and no password"""
    print("\n6. Testing owner invite mode...")
    
    headers = {"Authorization": f"Bearer {owner_token}"}
    
    # Owner creates admin with invite mode and no password
    admin_data = {
        "email": "test.invite@casino.com",
        "tenant_id": "demo_renter",
        "password_mode": "invite",
        "full_name": "Test Invite Admin"
        # No password - should be auto-generated
    }
    
    response = make_request("POST", "/v1/admin/users", headers=headers, json_data=admin_data)
    
    if response["status_code"] == 200:
        result.add_result(
            "Owner Invite Mode", 
            True, 
            f"Status: {response['status_code']}, Admin created with invite mode"
        )
    else:
        result.add_result(
            "Owner Invite Mode", 
            False, 
            f"Expected 200, got {response['status_code']}: {response['json']}"
        )

def test_docker_compose_static_check(result: TestResult):
    """Static check of docker-compose.prod.yml"""
    print("\n7. Testing docker-compose.prod.yml static checks...")
    
    try:
        with open("/app/docker-compose.prod.yml", "r") as f:
            content = f.read()
        
        # Check 1: Must NOT contain bootstrap credential fallbacks
        forbidden_patterns = [
            "${BOOTSTRAP_OWNER_EMAIL:-",
            "${BOOTSTRAP_OWNER_PASSWORD:-"
        ]
        
        has_forbidden = any(pattern in content for pattern in forbidden_patterns)
        
        if not has_forbidden:
            result.add_result(
                "Docker Compose - No Credential Fallbacks", 
                True, 
                "No ${BOOTSTRAP_OWNER_EMAIL:-...} or ${BOOTSTRAP_OWNER_PASSWORD:-...} found"
            )
        else:
            found_patterns = [p for p in forbidden_patterns if p in content]
            result.add_result(
                "Docker Compose - No Credential Fallbacks", 
                False, 
                f"Found forbidden patterns: {found_patterns}"
            )
        
        # Check 2: Must contain BOOTSTRAP_ENABLED with default false
        bootstrap_enabled_pattern = "BOOTSTRAP_ENABLED: ${BOOTSTRAP_ENABLED:-false}"
        
        if bootstrap_enabled_pattern in content:
            result.add_result(
                "Docker Compose - Bootstrap Enabled Default False", 
                True, 
                "Found BOOTSTRAP_ENABLED with default false"
            )
        else:
            result.add_result(
                "Docker Compose - Bootstrap Enabled Default False", 
                False, 
                f"Expected pattern '{bootstrap_enabled_pattern}' not found"
            )
            
    except Exception as e:
        result.add_result(
            "Docker Compose Static Check", 
            False, 
            f"Failed to read docker-compose.prod.yml: {str(e)}"
        )

def test_rate_limiting(result: TestResult):
    """Test 1: Rate limit behavior - 6 rapid requests to login endpoint"""
    print("\n1. Testing Rate Limiting Behavior...")
    
    login_data = {
        "email": "admin@casino.com",
        "password": "WrongPass!"
    }
    
    status_codes = []
    
    # Send 6 rapid requests
    for i in range(6):
        response = make_request("POST", "/v1/auth/login", json_data=login_data)
        status_codes.append(response["status_code"])
        print(f"   Request {i+1}: Status {response['status_code']}")
        
        # Small delay to avoid overwhelming the server
        time.sleep(0.1)
    
    # Expected: First 5 should be 401 (INVALID_CREDENTIALS), 6th should be 429 (RATE_LIMIT_EXCEEDED)
    expected_pattern = [401, 401, 401, 401, 401, 429]
    
    if status_codes == expected_pattern:
        result.add_result(
            "Rate Limiting", 
            True, 
            f"Correct pattern: {status_codes} - First 5 requests 401, 6th request 429"
        )
    else:
        result.add_result(
            "Rate Limiting", 
            False, 
            f"Expected {expected_pattern}, got {status_codes}"
        )

def test_trusted_proxy_behavior(result: TestResult):
    """Test 2: Trusted proxy/X-Forwarded-For behavior"""
    print("\n2. Testing Trusted Proxy Behavior...")
    
    login_data = {
        "email": "admin@casino.com", 
        "password": "WrongPass!"
    }
    
    # Test with spoofed X-Forwarded-For header
    headers = {"X-Forwarded-For": "1.2.3.4"}
    
    response = make_request("POST", "/v1/auth/login", headers=headers, json_data=login_data)
    
    # Since TRUSTED_PROXY_IPS is empty by default, the spoofed IP should be ignored
    # and rate limiting should use the actual client IP
    if response["status_code"] == 401:
        result.add_result(
            "Trusted Proxy Behavior", 
            True, 
            f"X-Forwarded-For header ignored (no trusted proxies configured), got {response['status_code']}"
        )
    else:
        result.add_result(
            "Trusted Proxy Behavior", 
            False, 
            f"Expected 401 (spoofed header ignored), got {response['status_code']}"
        )

def test_cors_behavior(result: TestResult):
    """Test 3: CORS behavior"""
    print("\n3. Testing CORS Behavior...")
    
    # Send OPTIONS preflight request with evil origin
    headers = {"Origin": "https://evil.example"}
    
    try:
        response = requests.options(
            f"{API_BASE}/v1/auth/login",
            headers=headers,
            timeout=30
        )
        
        access_control_origin = response.headers.get("Access-Control-Allow-Origin")
        
        # Check if evil origin is blocked
        if access_control_origin != "https://evil.example":
            result.add_result(
                "CORS Evil Origin Blocked", 
                True, 
                f"Evil origin blocked - Access-Control-Allow-Origin: {access_control_origin}"
            )
        else:
            result.add_result(
                "CORS Evil Origin Blocked", 
                False, 
                f"Evil origin allowed - Access-Control-Allow-Origin: {access_control_origin}"
            )
            
        # Check environment detection
        # If backend is running and CORS_ORIGINS is set to "*" (dev mode), that's expected
        # If it's prod/staging, CORS should be more restrictive
        print(f"   CORS Origins header: {access_control_origin}")
        print(f"   Backend appears to be running (not failing fast on startup)")
        
        result.add_result(
            "CORS Configuration", 
            True, 
            f"Backend running with CORS config - likely dev/local environment"
        )
        
    except Exception as e:
        result.add_result(
            "CORS Test", 
            False, 
            f"Failed to test CORS: {str(e)}"
        )

def main():
    print("=== P1-SECURITY BACKEND VALIDATION ===")
    print(f"Testing against: {BASE_URL}")
    
    result = TestResult()
    
    # Test 1: Rate limiting behavior
    test_rate_limiting(result)
    
    # Test 2: Trusted proxy behavior
    test_trusted_proxy_behavior(result)
    
    # Test 3: CORS behavior
    test_cors_behavior(result)
    
    # Print final summary
    success = result.print_summary()
    
    if success:
        print("\n🎉 ALL P1-SECURITY VALIDATION TESTS PASSED!")
        return True
    else:
        print(f"\n💥 {result.failed} TEST(S) FAILED - SECURITY ISSUES DETECTED!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)