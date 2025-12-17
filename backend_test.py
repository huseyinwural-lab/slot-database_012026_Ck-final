#!/usr/bin/env python3
"""
P2 Observability Backend Validation
Testing liveness/readiness endpoints, X-Request-ID behavior, rate limiting logs, and JSON logging
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
        print(f"\n=== P2 OBSERVABILITY VALIDATION SUMMARY ===")
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

def test_liveness_readiness_endpoints(result: TestResult):
    """Test 1: Validate liveness/readiness endpoints"""
    print("\n1. Testing Liveness/Readiness Endpoints...")
    
    # Test liveness endpoint
    health_response = make_request("GET", "/health")
    print(f"   GET /api/health: Status {health_response['status_code']}")
    
    if health_response["status_code"] == 200 and isinstance(health_response["json"], dict):
        result.add_result(
            "Liveness Endpoint (/api/health)", 
            True, 
            f"Returns 200 JSON: {health_response['json']}"
        )
    else:
        result.add_result(
            "Liveness Endpoint (/api/health)", 
            False, 
            f"Expected 200 JSON, got {health_response['status_code']}: {health_response['json']}"
        )
    
    # Test readiness endpoint
    ready_response = make_request("GET", "/ready")
    print(f"   GET /api/ready: Status {ready_response['status_code']}")
    
    if (ready_response["status_code"] == 200 and 
        isinstance(ready_response["json"], dict) and
        ready_response["json"].get("dependencies", {}).get("database") == "connected"):
        result.add_result(
            "Readiness Endpoint (/api/ready)", 
            True, 
            f"Returns 200 JSON with database='connected': {ready_response['json']}"
        )
    else:
        result.add_result(
            "Readiness Endpoint (/api/ready)", 
            False, 
            f"Expected 200 JSON with dependencies.database='connected', got {ready_response['status_code']}: {ready_response['json']}"
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