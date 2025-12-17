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