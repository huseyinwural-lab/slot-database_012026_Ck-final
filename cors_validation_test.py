#!/usr/bin/env python3
"""
CORS Wildcard Validation Test
Validates that CORS wildcard is removed in CI workflow after recent change.
"""

import requests
import yaml
import os
import sys
from typing import Dict, Any

def parse_ci_workflow():
    """Parse the CI workflow file and check CORS_ORIGINS configuration"""
    workflow_path = "/app/.github/workflows/prod-compose-acceptance.yml"
    
    print("=== PARSING CI WORKFLOW FILE ===")
    print(f"File: {workflow_path}")
    
    try:
        with open(workflow_path, 'r') as f:
            workflow = yaml.safe_load(f)
        
        # Extract CORS_ORIGINS from env section
        cors_origins = None
        if 'jobs' in workflow:
            for job_name, job_config in workflow['jobs'].items():
                if 'env' in job_config and 'CORS_ORIGINS' in job_config['env']:
                    cors_origins = job_config['env']['CORS_ORIGINS']
                    break
        
        print(f"Found CORS_ORIGINS: {cors_origins}")
        
        # Validate requirements
        results = []
        
        # 1. Check it's not '*'
        if cors_origins != '*':
            results.append(("CORS_ORIGINS is not wildcard '*'", True, f"Value: {cors_origins}"))
        else:
            results.append(("CORS_ORIGINS is not wildcard '*'", False, f"Found wildcard: {cors_origins}"))
        
        # 2. Check it contains localhost:3000
        if cors_origins and 'localhost:3000' in cors_origins:
            results.append(("Contains localhost:3000", True, f"Found in: {cors_origins}"))
        else:
            results.append(("Contains localhost:3000", False, f"Not found in: {cors_origins}"))
        
        # 3. Check it contains localhost:3001
        if cors_origins and 'localhost:3001' in cors_origins:
            results.append(("Contains localhost:3001", True, f"Found in: {cors_origins}"))
        else:
            results.append(("Contains localhost:3001", False, f"Not found in: {cors_origins}"))
        
        return results, cors_origins
        
    except Exception as e:
        return [("Parse CI workflow", False, f"Error: {str(e)}")], None

def test_cors_preflight():
    """Test CORS preflight request if backend is running"""
    print("\n=== TESTING CORS PREFLIGHT (OPTIONAL) ===")
    
    # Try to determine backend URL
    backend_url = None
    
    # Check frontend .env for backend URL
    try:
        with open("/app/frontend/.env", 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    backend_url = line.split('=', 1)[1].strip()
                    break
    except:
        pass
    
    # Fallback to localhost
    if not backend_url:
        backend_url = "http://localhost:8001"
    
    print(f"Testing against backend: {backend_url}")
    
    results = []
    
    try:
        # Send OPTIONS preflight request with Origin: http://localhost:3000
        headers = {"Origin": "http://localhost:3000"}
        
        response = requests.options(
            f"{backend_url}/api/v1/auth/login",
            headers=headers,
            timeout=10
        )
        
        access_control_origin = response.headers.get("Access-Control-Allow-Origin")
        
        print(f"Response status: {response.status_code}")
        print(f"Access-Control-Allow-Origin: {access_control_origin}")
        
        # Check if localhost:3000 is allowed
        if access_control_origin == "http://localhost:3000":
            results.append(("CORS allows localhost:3000", True, f"Access-Control-Allow-Origin: {access_control_origin}"))
        else:
            results.append(("CORS allows localhost:3000", False, f"Expected 'http://localhost:3000', got: {access_control_origin}"))
        
        # Check that backend is responding
        results.append(("Backend is running", True, f"Status: {response.status_code}"))
        
    except requests.exceptions.ConnectionError:
        results.append(("Backend is running", False, "Connection refused - backend not running"))
    except Exception as e:
        results.append(("CORS preflight test", False, f"Error: {str(e)}"))
    
    return results

def main():
    print("=== CORS WILDCARD VALIDATION TEST ===")
    
    all_results = []
    
    # 1. Parse CI workflow file
    workflow_results, cors_origins = parse_ci_workflow()
    all_results.extend(workflow_results)
    
    # 2. Test CORS preflight (optional)
    preflight_results = test_cors_preflight()
    all_results.extend(preflight_results)
    
    # Print results
    print("\n=== VALIDATION RESULTS ===")
    passed = 0
    failed = 0
    
    for test_name, success, details in all_results:
        status_icon = "✅" if success else "❌"
        status_text = "PASS" if success else "FAIL"
        print(f"{status_icon} {test_name}: {status_text}")
        if details:
            print(f"   Details: {details}")
        
        if success:
            passed += 1
        else:
            failed += 1
    
    print(f"\nSummary: {passed} passed, {failed} failed")
    
    # Overall result
    if failed == 0:
        print("\n🎉 ALL CORS VALIDATION TESTS PASSED!")
        return True
    else:
        print(f"\n💥 {failed} TEST(S) FAILED!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)