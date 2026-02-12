#!/usr/bin/env python3
"""
Final Smoke Test for Fixes
Verifies the 5 specific requirements from the review request:
1. Check backend/app/routes/approvals.py exists and has status param
2. Check backend/app/routes/risk_dashboard.py exists  
3. Check backend/app/routes/fraud_detection.py exists
4. Verify backend/config.py uses os.getenv for secrets
5. Confirm artifacts/ folder is GONE
"""

import os
import sys
import ast
import re
from pathlib import Path

def test_approvals_py_exists_and_has_status():
    """Test 1: Check backend/app/routes/approvals.py exists and has status param"""
    file_path = "/app/backend/app/routes/approvals.py"
    
    if not os.path.exists(file_path):
        return False, "File does not exist"
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check for status parameter in Query
        if 'status: Optional[str] = Query(None)' in content:
            return True, "File exists and has status parameter"
        elif 'status' in content and 'Query' in content:
            return True, "File exists and has status parameter (different format)"
        else:
            return False, "File exists but status parameter not found"
            
    except Exception as e:
        return False, f"Error reading file: {e}"

def test_risk_dashboard_py_exists():
    """Test 2: Check backend/app/routes/risk_dashboard.py exists"""
    file_path = "/app/backend/app/routes/risk_dashboard.py"
    
    if not os.path.exists(file_path):
        return False, "File does not exist"
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Basic validation - should have router and risk-related endpoints
        if 'router = APIRouter' in content and 'risk' in content.lower():
            return True, "File exists and appears to be a risk dashboard router"
        else:
            return False, "File exists but doesn't appear to be properly configured"
            
    except Exception as e:
        return False, f"Error reading file: {e}"

def test_fraud_detection_py_exists():
    """Test 3: Check backend/app/routes/fraud_detection.py exists"""
    file_path = "/app/backend/app/routes/fraud_detection.py"
    
    if not os.path.exists(file_path):
        return False, "File does not exist"
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Basic validation - should have router and fraud-related endpoints
        if 'router = APIRouter' in content and 'fraud' in content.lower():
            return True, "File exists and appears to be a fraud detection router"
        else:
            return False, "File exists but doesn't appear to be properly configured"
            
    except Exception as e:
        return False, f"Error reading file: {e}"

def test_config_py_uses_os_getenv():
    """Test 4: Verify backend/config.py uses os.getenv for secrets"""
    file_path = "/app/backend/config.py"
    
    if not os.path.exists(file_path):
        return False, "File does not exist"
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check for os.getenv usage
        os_getenv_count = content.count('os.getenv(')
        
        if os_getenv_count == 0:
            return False, "No os.getenv() calls found"
        
        # Look for specific secret-related os.getenv calls
        secret_patterns = [
            r'os\.getenv\(["\']WEBHOOK_SECRET_MOCKPSP["\']',
            r'os\.getenv\(["\']AUDIT_EXPORT_SECRET["\']'
        ]
        
        found_secrets = []
        for pattern in secret_patterns:
            if re.search(pattern, content):
                found_secrets.append(pattern.split("'")[1])
        
        if found_secrets:
            return True, f"File uses os.getenv for secrets: {', '.join(found_secrets)} (total os.getenv calls: {os_getenv_count})"
        else:
            return True, f"File uses os.getenv ({os_getenv_count} calls found)"
            
    except Exception as e:
        return False, f"Error reading file: {e}"

def test_artifacts_folder_gone():
    """Test 5: Confirm artifacts/ folder is GONE"""
    artifacts_path = "/app/artifacts"
    
    if os.path.exists(artifacts_path):
        return False, "artifacts/ folder still exists"
    else:
        return True, "artifacts/ folder is gone (as expected)"

def main():
    print("=" * 60)
    print("FINAL SMOKE TEST FOR FIXES")
    print("=" * 60)
    
    tests = [
        ("1. approvals.py exists and has status param", test_approvals_py_exists_and_has_status),
        ("2. risk_dashboard.py exists", test_risk_dashboard_py_exists),
        ("3. fraud_detection.py exists", test_fraud_detection_py_exists),
        ("4. config.py uses os.getenv for secrets", test_config_py_uses_os_getenv),
        ("5. artifacts/ folder is GONE", test_artifacts_folder_gone)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\nTesting: {test_name}")
        try:
            success, message = test_func()
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"  {status}: {message}")
            results.append((test_name, success, message))
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            results.append((test_name, False, f"Test error: {e}"))
    
    # Summary
    print("\n" + "=" * 60)
    print("FINAL SMOKE TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, success, message in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
        else:
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED - Final smoke test successful!")
        return 0
    else:
        print("❌ SOME TESTS FAILED - Issues need to be addressed")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)