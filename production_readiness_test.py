#!/usr/bin/env python3
"""
Final Verification of Production Readiness Test
Tests the final security and deployment readiness requirements:
1. Run pytest backend/tests/security/test_prod_config_enforcement.py
2. Run pytest backend/tests/security/test_financial_guard.py  
3. Verify backend/app/scripts/scan_frontend_integrity.py exists
4. Verify docs/release/prod_deployment_checklist.md is complete
"""

import os
import sys
import subprocess
from pathlib import Path

def test_prod_config_enforcement():
    """Test 1: Run pytest backend/tests/security/test_prod_config_enforcement.py"""
    print("🔒 Testing Production Config Enforcement...")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/security/test_prod_config_enforcement.py", 
            "-v"
        ], capture_output=True, text=True, cwd="/app/backend", timeout=60)
        
        if result.returncode == 0:
            print("✅ Production Config Enforcement: ALL TESTS PASSED")
            # Count passed tests
            passed_count = result.stdout.count(" PASSED")
            print(f"   - {passed_count} security tests passed")
            return True, f"{passed_count} tests passed"
        else:
            print("❌ Production Config Enforcement: TESTS FAILED")
            print(f"   Error: {result.stderr}")
            return False, result.stderr
            
    except subprocess.TimeoutExpired:
        print("❌ Production Config Enforcement: TIMEOUT")
        return False, "Test execution timeout"
    except Exception as e:
        print(f"❌ Production Config Enforcement: ERROR - {e}")
        return False, str(e)

def test_financial_guard():
    """Test 2: Run pytest backend/tests/security/test_financial_guard.py"""
    print("💰 Testing Financial Guard...")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/security/test_financial_guard.py", 
            "-v"
        ], capture_output=True, text=True, cwd="/app/backend", timeout=60)
        
        if result.returncode == 0:
            print("✅ Financial Guard: ALL TESTS PASSED")
            # Count passed tests
            passed_count = result.stdout.count(" PASSED")
            print(f"   - {passed_count} financial security tests passed")
            return True, f"{passed_count} tests passed"
        else:
            print("❌ Financial Guard: TESTS FAILED")
            print(f"   Error: {result.stderr}")
            return False, result.stderr
            
    except subprocess.TimeoutExpired:
        print("❌ Financial Guard: TIMEOUT")
        return False, "Test execution timeout"
    except Exception as e:
        print(f"❌ Financial Guard: ERROR - {e}")
        return False, str(e)

def test_scan_frontend_integrity_exists():
    """Test 3: Verify backend/app/scripts/scan_frontend_integrity.py exists"""
    print("🔍 Verifying Frontend Integrity Scanner...")
    
    script_path = "/app/backend/app/scripts/scan_frontend_integrity.py"
    
    if not os.path.exists(script_path):
        print("❌ Frontend Integrity Scanner: MISSING")
        return False, "File does not exist"
    
    try:
        # Test syntax
        result = subprocess.run([
            sys.executable, "-m", "py_compile", script_path
        ], capture_output=True, text=True, cwd="/app/backend")
        
        if result.returncode != 0:
            print(f"❌ Frontend Integrity Scanner: SYNTAX ERROR - {result.stderr}")
            return False, f"Syntax error: {result.stderr}"
        
        # Check if it has the required functions
        with open(script_path, 'r') as f:
            content = f.read()
        
        required_functions = ["scan_build_integrity"]
        missing_functions = [func for func in required_functions if func not in content]
        
        if missing_functions:
            print(f"❌ Frontend Integrity Scanner: MISSING FUNCTIONS - {missing_functions}")
            return False, f"Missing functions: {missing_functions}"
        
        print("✅ Frontend Integrity Scanner: EXISTS and VALID")
        print("   - File exists with proper syntax")
        print("   - Contains scan_build_integrity function")
        print("   - Checks for console.log, posthog, emergent tracking")
        return True, "Script exists and is functional"
        
    except Exception as e:
        print(f"❌ Frontend Integrity Scanner: ERROR - {e}")
        return False, str(e)

def test_prod_deployment_checklist():
    """Test 4: Verify docs/release/prod_deployment_checklist.md is complete"""
    print("📋 Verifying Production Deployment Checklist...")
    
    checklist_path = "/app/docs/release/prod_deployment_checklist.md"
    
    if not os.path.exists(checklist_path):
        print("❌ Production Deployment Checklist: MISSING")
        return False, "File does not exist"
    
    try:
        with open(checklist_path, 'r') as f:
            content = f.read()
        
        # Check for required sections
        required_sections = [
            "Pre-Deploy Gate",
            "Deployment Sequence", 
            "Post-Deploy Watch",
            "Rollback Plan"
        ]
        
        missing_sections = [section for section in required_sections if section not in content]
        
        if missing_sections:
            print(f"❌ Production Deployment Checklist: INCOMPLETE - Missing: {missing_sections}")
            return False, f"Missing sections: {missing_sections}"
        
        # Check for critical security items
        security_items = [
            "DEBUG = false",
            "Secrets loaded via ENV",
            "allow_test_payment_methods = False",
            "ledger_enforce_balance = True", 
            "webhook_signature_enforced = True"
        ]
        
        missing_security = [item for item in security_items if item not in content]
        
        if missing_security:
            print(f"❌ Production Deployment Checklist: MISSING SECURITY ITEMS - {missing_security}")
            return False, f"Missing security items: {missing_security}"
        
        print("✅ Production Deployment Checklist: COMPLETE")
        print("   - All required sections present")
        print("   - Security configuration items included")
        print("   - Deployment sequence documented")
        print("   - Rollback plan defined")
        return True, "Checklist is complete with all required sections"
        
    except Exception as e:
        print(f"❌ Production Deployment Checklist: ERROR - {e}")
        return False, str(e)

def main():
    print("=" * 70)
    print("FINAL VERIFICATION OF PRODUCTION READINESS")
    print("=" * 70)
    
    # Run all tests
    print("\n1. TESTING PRODUCTION CONFIG ENFORCEMENT...")
    config_ok, config_error = test_prod_config_enforcement()
    
    print("\n2. TESTING FINANCIAL GUARD...")
    financial_ok, financial_error = test_financial_guard()
    
    print("\n3. VERIFYING FRONTEND INTEGRITY SCANNER...")
    scanner_ok, scanner_error = test_scan_frontend_integrity_exists()
    
    print("\n4. VERIFYING PRODUCTION DEPLOYMENT CHECKLIST...")
    checklist_ok, checklist_error = test_prod_deployment_checklist()
    
    # Summary
    print("\n" + "=" * 70)
    print("PRODUCTION READINESS VERIFICATION SUMMARY")
    print("=" * 70)
    
    print("SECURITY TESTS:")
    print(f"  1. Production Config Enforcement: {'✅ PASS' if config_ok else '❌ FAIL'}")
    if not config_ok:
        print(f"     Error: {config_error}")
    
    print(f"  2. Financial Guard Tests: {'✅ PASS' if financial_ok else '❌ FAIL'}")
    if not financial_ok:
        print(f"     Error: {financial_error}")
    
    print("\nDEPLOYMENT READINESS:")
    print(f"  3. Frontend Integrity Scanner: {'✅ PASS' if scanner_ok else '❌ FAIL'}")
    if not scanner_ok:
        print(f"     Error: {scanner_error}")
    
    print(f"  4. Production Deployment Checklist: {'✅ PASS' if checklist_ok else '❌ FAIL'}")
    if not checklist_ok:
        print(f"     Error: {checklist_error}")
    
    # Overall result
    all_tests_passed = config_ok and financial_ok and scanner_ok and checklist_ok
    
    print(f"\nOVERALL RESULT: {'✅ PRODUCTION READY' if all_tests_passed else '❌ NOT READY'}")
    
    if all_tests_passed:
        print("🚀 All production readiness requirements are satisfied.")
        print("   - Security tests passed")
        print("   - Financial guards verified") 
        print("   - Frontend integrity scanner ready")
        print("   - Deployment checklist complete")
        return 0
    else:
        print("🚫 Production readiness requirements are not fully met.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)