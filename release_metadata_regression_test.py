#!/usr/bin/env python3
"""
Quick Regression Test - Release Metadata Additions
Testing specific requirements:
1) GET /api/version returns JSON with keys service/version/git_sha/build_time and no extra fields
2) GET /api/ready returns 200
"""

import requests
import json
import sys

# Get external API base from frontend/.env
BASE_URL = "https://headers-ops-ready.preview.emergentagent.com"  # Default
try:
    with open("/app/frontend/.env", "r") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip()
                break
except FileNotFoundError:
    pass

API_BASE = f"{BASE_URL}/api"

def test_version_endpoint():
    """Test 1: GET /api/version returns JSON with exact keys and no extra fields"""
    print("1. Testing GET /api/version...")
    
    try:
        response = requests.get(f"{API_BASE}/version", timeout=30)
        print(f"   Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   ❌ FAIL: Expected 200, got {response.status_code}")
            return False
        
        try:
            data = response.json()
        except json.JSONDecodeError:
            print(f"   ❌ FAIL: Response is not valid JSON")
            return False
        
        print(f"   Response: {json.dumps(data, indent=2)}")
        
        # Check exact required keys
        required_keys = {"service", "version", "git_sha", "build_time"}
        actual_keys = set(data.keys())
        
        if actual_keys != required_keys:
            missing = required_keys - actual_keys
            extra = actual_keys - required_keys
            print(f"   ❌ FAIL: Key mismatch")
            if missing:
                print(f"      Missing keys: {missing}")
            if extra:
                print(f"      Extra keys: {extra}")
            return False
        
        # Verify all values are strings
        for key, value in data.items():
            if not isinstance(value, str):
                print(f"   ❌ FAIL: Key '{key}' has non-string value: {type(value).__name__}")
                return False
        
        print(f"   ✅ PASS: Correct keys and types")
        print(f"      service={data['service']}, version={data['version']}")
        print(f"      git_sha={data['git_sha']}, build_time={data['build_time']}")
        return True
        
    except Exception as e:
        print(f"   ❌ FAIL: Exception occurred: {str(e)}")
        return False

def test_ready_endpoint():
    """Test 2: GET /api/ready returns 200"""
    print("\n2. Testing GET /api/ready...")
    
    try:
        response = requests.get(f"{API_BASE}/ready", timeout=30)
        print(f"   Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   ❌ FAIL: Expected 200, got {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error response: {json.dumps(error_data, indent=2)}")
            except:
                print(f"   Error text: {response.text}")
            return False
        
        try:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
        except json.JSONDecodeError:
            print(f"   ❌ FAIL: Response is not valid JSON")
            return False
        
        print(f"   ✅ PASS: Ready endpoint returns 200 OK")
        return True
        
    except Exception as e:
        print(f"   ❌ FAIL: Exception occurred: {str(e)}")
        return False

def main():
    print("=== QUICK REGRESSION - RELEASE METADATA ADDITIONS ===")
    print(f"Testing against: {BASE_URL}")
    
    test1_pass = test_version_endpoint()
    test2_pass = test_ready_endpoint()
    
    print(f"\n=== SUMMARY ===")
    print(f"Test 1 (GET /api/version): {'✅ PASS' if test1_pass else '❌ FAIL'}")
    print(f"Test 2 (GET /api/ready): {'✅ PASS' if test2_pass else '❌ FAIL'}")
    
    if test1_pass and test2_pass:
        print(f"\n🎉 ALL REGRESSION TESTS PASSED!")
        return True
    else:
        failed_count = sum([not test1_pass, not test2_pass])
        print(f"\n💥 {failed_count} TEST(S) FAILED!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)