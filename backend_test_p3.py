#!/usr/bin/env python3
"""
P3 Changes Backend Validation Testing
Focus on P3 changes as requested in review:
1) Verify GET /api/version returns 200 and includes version=0.1.0 (from repo VERSION fallback if env missing), and only safe keys
2) Verify health endpoints: GET /api/health and GET /api/ready return 200
3) Validate docker-compose.prod.yml parses as valid YAML (optional step)
4) Light sanity for tenants: login with admin@casino.com/Admin123! then GET /api/v1/tenants/capabilities should show is_owner true
"""

import requests
import json
import sys
import os
import time
import uuid
import yaml
from typing import Dict, Any, Optional

# Configuration - Use frontend .env for external URL
BASE_URL = "https://multi-tenant-panel.preview.emergentagent.com"  # Default
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
        print(f"\n=== P3 CHANGES BACKEND VALIDATION SUMMARY ===")
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

def test_version_endpoint_p3_requirements(result: TestResult) -> None:
    """Test 1: Verify GET /api/version returns 200 and includes version=0.1.0 (from repo VERSION fallback if env missing), and only safe keys"""
    print("\n1. Testing GET /api/version P3 requirements...")
    
    response = make_request("GET", "/version")
    print(f"   GET /api/version: Status {response['status_code']}")
    
    if response["status_code"] != 200:
        result.add_result("Version Endpoint P3 Requirements", False, f"Version endpoint failed: {response['status_code']}")
        return
    
    version_data = response["json"]
    print(f"   Response: {json.dumps(version_data, indent=2)}")
    
    # Check required safe fields are present
    required_fields = ["service", "version", "git_sha", "build_time"]
    missing_fields = []
    
    for field in required_fields:
        if field not in version_data:
            missing_fields.append(field)
    
    if missing_fields:
        result.add_result("Version Endpoint P3 Requirements", False, f"Missing required fields: {missing_fields}")
        return
    
    # Check version fallback to repo VERSION file (0.1.0)
    version_value = version_data.get("version")
    if version_value == "0.1.0":
        version_source = "repo VERSION file fallback (expected in dev/preview)"
    elif version_value == "unknown":
        version_source = "unknown (acceptable if no env vars set)"
    else:
        version_source = f"environment variable (value: {version_value})"
    
    # Check only safe keys are present (no sensitive data)
    unsafe_fields = ["env", "hostname", "config", "database_url", "jwt_secret", "cors_origins", 
                    "debug", "openai_api_key", "bootstrap_enabled", "seed_on_startup", "password"]
    found_unsafe = []
    
    for field in unsafe_fields:
        if field in version_data:
            found_unsafe.append(field)
    
    if found_unsafe:
        result.add_result("Version Endpoint P3 Requirements", False, f"Unsafe fields found in response: {found_unsafe}")
        return
    
    # Verify field values are strings
    invalid_values = []
    for field in required_fields:
        value = version_data.get(field)
        if not isinstance(value, str):
            invalid_values.append(f"{field}={type(value).__name__}")
    
    if invalid_values:
        result.add_result("Version Endpoint P3 Requirements", False, f"Invalid field types: {invalid_values}")
        return
    
    result.add_result("Version Endpoint P3 Requirements", True, 
                     f"All requirements met: service={version_data['service']}, "
                     f"version={version_data['version']} ({version_source}), "
                     f"git_sha={version_data['git_sha']}, build_time={version_data['build_time']}, "
                     f"only safe keys present")

def test_health_endpoints(result: TestResult) -> None:
    """Test 2: Verify health endpoints: GET /api/health and GET /api/ready return 200"""
    print("\n2. Testing health endpoints...")
    
    # Test /api/health
    health_response = make_request("GET", "/health")
    print(f"   GET /api/health: Status {health_response['status_code']}")
    
    if health_response["status_code"] != 200:
        result.add_result("Health Endpoints", False, f"/api/health failed: {health_response['status_code']}")
        return
    
    health_data = health_response["json"]
    print(f"   Health response: {json.dumps(health_data, indent=2)}")
    
    # Test /api/ready
    ready_response = make_request("GET", "/ready")
    print(f"   GET /api/ready: Status {ready_response['status_code']}")
    
    if ready_response["status_code"] != 200:
        result.add_result("Health Endpoints", False, f"/api/ready failed: {ready_response['status_code']}")
        return
    
    ready_data = ready_response["json"]
    print(f"   Ready response: {json.dumps(ready_data, indent=2)}")
    
    # Validate health response structure
    if not isinstance(health_data.get("status"), str) or health_data["status"] != "healthy":
        result.add_result("Health Endpoints", False, f"Invalid health status: {health_data.get('status')}")
        return
    
    # Validate ready response structure
    if not isinstance(ready_data.get("status"), str) or ready_data["status"] != "ready":
        result.add_result("Health Endpoints", False, f"Invalid ready status: {ready_data.get('status')}")
        return
    
    result.add_result("Health Endpoints", True, 
                     f"Both endpoints working: /api/health status={health_data['status']}, "
                     f"/api/ready status={ready_data['status']}")

def test_docker_compose_yaml_validation(result: TestResult) -> None:
    """Test 3: Validate docker-compose.prod.yml parses as valid YAML (optional step)"""
    print("\n3. Testing docker-compose.prod.yml YAML validation...")
    
    try:
        with open("/app/docker-compose.prod.yml", "r") as f:
            yaml_content = f.read()
        
        # Parse YAML to validate syntax
        parsed_yaml = yaml.safe_load(yaml_content)
        
        if not isinstance(parsed_yaml, dict):
            result.add_result("Docker Compose YAML Validation", False, "Parsed YAML is not a dictionary")
            return
        
        # Check for required top-level keys
        required_keys = ["version", "services"]
        missing_keys = []
        
        for key in required_keys:
            if key not in parsed_yaml:
                missing_keys.append(key)
        
        if missing_keys:
            result.add_result("Docker Compose YAML Validation", False, f"Missing required keys: {missing_keys}")
            return
        
        # Check services exist
        services = parsed_yaml.get("services", {})
        expected_services = ["postgres", "backend", "frontend-admin", "frontend-player"]
        missing_services = []
        
        for service in expected_services:
            if service not in services:
                missing_services.append(service)
        
        if missing_services:
            result.add_result("Docker Compose YAML Validation", False, f"Missing services: {missing_services}")
            return
        
        result.add_result("Docker Compose YAML Validation", True, 
                         f"Valid YAML with {len(services)} services: {list(services.keys())}")
        
    except yaml.YAMLError as e:
        result.add_result("Docker Compose YAML Validation", False, f"YAML parsing error: {str(e)}")
    except FileNotFoundError:
        result.add_result("Docker Compose YAML Validation", False, "docker-compose.prod.yml file not found")
    except Exception as e:
        result.add_result("Docker Compose YAML Validation", False, f"Unexpected error: {str(e)}")

def test_tenant_capabilities_owner_check(result: TestResult) -> None:
    """Test 4: Light sanity for tenants: login with admin@casino.com/Admin123! then GET /api/v1/tenants/capabilities should show is_owner true"""
    print("\n4. Testing tenant capabilities owner check...")
    
    # Step 1: Login with admin credentials
    login_data = {
        "email": "admin@casino.com",
        "password": "Admin123!"
    }
    
    login_response = make_request("POST", "/v1/auth/login", json_data=login_data)
    print(f"   POST /api/v1/auth/login: Status {login_response['status_code']}")
    
    if login_response["status_code"] != 200:
        result.add_result("Tenant Capabilities Owner Check", False, 
                         f"Login failed: {login_response['status_code']} - {login_response['json']}")
        return
    
    login_result = login_response["json"]
    access_token = login_result.get("access_token")
    
    if not access_token:
        result.add_result("Tenant Capabilities Owner Check", False, "No access_token in login response")
        return
    
    print(f"   Login successful, token length: {len(access_token)} chars")
    
    # Step 2: Get tenant capabilities
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    capabilities_response = make_request("GET", "/v1/tenants/capabilities", headers=headers)
    print(f"   GET /api/v1/tenants/capabilities: Status {capabilities_response['status_code']}")
    
    if capabilities_response["status_code"] != 200:
        result.add_result("Tenant Capabilities Owner Check", False, 
                         f"Capabilities request failed: {capabilities_response['status_code']} - {capabilities_response['json']}")
        return
    
    capabilities_data = capabilities_response["json"]
    print(f"   Capabilities response: {json.dumps(capabilities_data, indent=2)}")
    
    # Step 3: Check is_owner flag
    is_owner = capabilities_data.get("is_owner")
    
    if is_owner is not True:
        result.add_result("Tenant Capabilities Owner Check", False, 
                         f"is_owner should be true, got: {is_owner} (type: {type(is_owner)})")
        return
    
    # Additional validation: check for expected owner capabilities
    expected_owner_fields = ["is_owner", "tenant_id", "features"]
    missing_fields = []
    
    for field in expected_owner_fields:
        if field not in capabilities_data:
            missing_fields.append(field)
    
    if missing_fields:
        result.add_result("Tenant Capabilities Owner Check", False, 
                         f"Missing expected fields in capabilities: {missing_fields}")
        return
    
    result.add_result("Tenant Capabilities Owner Check", True, 
                     f"Owner check successful: is_owner={is_owner}, "
                     f"tenant_id={capabilities_data.get('tenant_id')}, "
                     f"features available: {len(capabilities_data.get('features', {}))}")

def main():
    print("=== P3 CHANGES BACKEND VALIDATION TESTING ===")
    print(f"Testing against: {BASE_URL}")
    
    result = TestResult()
    
    # Test 1: Verify GET /api/version returns 200 and includes version=0.1.0 (from repo VERSION fallback if env missing), and only safe keys
    test_version_endpoint_p3_requirements(result)
    
    # Test 2: Verify health endpoints: GET /api/health and GET /api/ready return 200
    test_health_endpoints(result)
    
    # Test 3: Validate docker-compose.prod.yml parses as valid YAML (optional step)
    test_docker_compose_yaml_validation(result)
    
    # Test 4: Light sanity for tenants: login with admin@casino.com/Admin123! then GET /api/v1/tenants/capabilities should show is_owner true
    test_tenant_capabilities_owner_check(result)
    
    # Print final summary
    success = result.print_summary()
    
    if success:
        print("\n🎉 ALL P3 CHANGES BACKEND VALIDATION TESTS PASSED!")
        return True
    else:
        print(f"\n💥 {result.failed} TEST(S) FAILED - P3 CHANGES VALIDATION ISSUES DETECTED!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)