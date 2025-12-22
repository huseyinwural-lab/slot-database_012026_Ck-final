#!/usr/bin/env python3
"""
Backend Regression Test - Logger NameError Fix Validation
Testing:
1) Backend health: GET /api/health returns 200
2) Login rate limit: 6 rapid POST /api/v1/auth/login with wrong password returns [401 x5, 429]
3) CORS preflight: OPTIONS /api/v1/auth/login with Origin https://evil.example does not allow origin
"""

import requests
import json
import sys
import os
import time
from typing import Dict, Any, Optional

# Configuration - Use environment variable from frontend/.env
BASE_URL = os.getenv("REACT_APP_BACKEND_URL", "https://pspreconcile.preview.emergentagent.com")
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
        print(f"\n=== BACKEND REGRESSION TEST SUMMARY ===")
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

def test_backend_health(result: TestResult):
    """Test 1: Backend health endpoint returns 200"""
    print("\n1. Testing Backend Health...")
    
    response = make_request("GET", "/health")
    
    if response["status_code"] == 200:
        result.add_result(
            "Backend Health Check", 
            True, 
            f"GET /api/health returned 200 OK with status: {response['json'].get('status', 'unknown')}"
        )
    else:
        result.add_result(
            "Backend Health Check", 
            False, 
            f"Expected 200, got {response['status_code']} - {response['json']}"
        )

def test_login_rate_limit(result: TestResult):
    """Test 2: Login rate limit - 6 rapid requests with wrong password"""
    print("\n2. Testing Login Rate Limit...")
    
    login_data = {
        "email": "admin@casino.com",
        "password": "WrongPassword123!"
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
            "Login Rate Limiting", 
            True, 
            f"Correct pattern: {status_codes} - First 5 requests 401, 6th request 429"
        )
    else:
        result.add_result(
            "Login Rate Limiting", 
            False, 
            f"Expected {expected_pattern}, got {status_codes}"
        )

def test_cors_preflight_evil_origin(result: TestResult):
    """Test 3: CORS preflight with evil origin should not allow origin"""
    print("\n3. Testing CORS Preflight with Evil Origin...")
    
    # Send OPTIONS preflight request with evil origin
    headers = {"Origin": "https://evil.example"}
    
    try:
        response = requests.options(
            f"{API_BASE}/v1/auth/login",
            headers=headers,
            timeout=30
        )
        
        access_control_origin = response.headers.get("Access-Control-Allow-Origin")
        
        print(f"   Response Status: {response.status_code}")
        print(f"   Access-Control-Allow-Origin: {access_control_origin}")
        
        # Check if evil origin is blocked (should not return the evil origin)
        if access_control_origin != "https://evil.example":
            result.add_result(
                "CORS Evil Origin Blocked", 
                True, 
                f"Evil origin blocked - Access-Control-Allow-Origin: {access_control_origin or 'None'}"
            )
        else:
            result.add_result(
                "CORS Evil Origin Blocked", 
                False, 
                f"Evil origin allowed - Access-Control-Allow-Origin: {access_control_origin}"
            )
            
    except Exception as e:
        result.add_result(
            "CORS Preflight Test", 
            False, 
            f"Failed to test CORS preflight: {str(e)}"
        )

def main():
    print("=== BACKEND REGRESSION TEST - Logger NameError Fix ===")
    print(f"Testing against: {BASE_URL}")
    
    result = TestResult()
    
    # Test 1: Backend health
    test_backend_health(result)
    
    # Test 2: Login rate limiting
    test_login_rate_limit(result)
    
    # Test 3: CORS preflight with evil origin
    test_cors_preflight_evil_origin(result)
    
    # Print final summary
    success = result.print_summary()
    
    if success:
        print("\n🎉 ALL REGRESSION TESTS PASSED!")
        return True
    else:
        print(f"\n💥 {result.failed} TEST(S) FAILED!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)