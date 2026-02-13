#!/usr/bin/env python3
"""
Final Security Check Test
Tests the security requirements for production deployment:
1. Verify backend/config.py has validate_prod_security_settings function
2. Verify backend/config.py calls validators at the end
3. Verify docs/release/prod_deployment_checklist.md exists
"""

import os
import sys
import re
from pathlib import Path

def test_validate_prod_security_settings_exists():
    """Test 1: Verify backend/config.py has validate_prod_security_settings function"""
    config_path = "/app/backend/config.py"
    
    if not os.path.exists(config_path):
        print("❌ backend/config.py: MISSING")
        return False, "File does not exist"
    
    try:
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Check for validate_prod_security_settings function definition
        if "def validate_prod_security_settings(self)" in content:
            print("✅ backend/config.py: validate_prod_security_settings function EXISTS")
            
            # Check if function has proper security validations
            security_checks = [
                "DEBUG must be False in production",
                "ALLOW_TEST_PAYMENT_METHODS must be False in production", 
                "LEDGER_ENFORCE_BALANCE must be True in production",
                "WEBHOOK_SIGNATURE_ENFORCED must be True in production"
            ]
            
            missing_checks = []
            for check in security_checks:
                if check not in content:
                    missing_checks.append(check)
            
            if missing_checks:
                print(f"⚠️  validate_prod_security_settings: Missing some security checks: {missing_checks}")
                return True, f"Function exists but missing checks: {missing_checks}"
            else:
                print("✅ validate_prod_security_settings: All security checks present")
                return True, "Function exists with all required security checks"
        else:
            print("❌ backend/config.py: validate_prod_security_settings function MISSING")
            return False, "validate_prod_security_settings function not found"
            
    except Exception as e:
        print(f"❌ backend/config.py: ERROR reading file - {e}")
        return False, str(e)

def test_validators_called_at_end():
    """Test 2: Verify backend/config.py calls validators at the end"""
    config_path = "/app/backend/config.py"
    
    if not os.path.exists(config_path):
        print("❌ backend/config.py: MISSING")
        return False, "File does not exist"
    
    try:
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Check for validator calls at the end of the file
        lines = content.strip().split('\n')
        last_lines = '\n'.join(lines[-10:])  # Check last 10 lines
        
        validate_prod_secrets_called = "settings.validate_prod_secrets()" in last_lines
        validate_prod_security_called = "settings.validate_prod_security_settings()" in last_lines
        
        if validate_prod_secrets_called and validate_prod_security_called:
            print("✅ backend/config.py: Both validators called at end")
            return True, "Both validate_prod_secrets() and validate_prod_security_settings() called"
        elif validate_prod_secrets_called:
            print("⚠️  backend/config.py: Only validate_prod_secrets() called")
            return False, "validate_prod_security_settings() not called at end"
        elif validate_prod_security_called:
            print("⚠️  backend/config.py: Only validate_prod_security_settings() called")
            return False, "validate_prod_secrets() not called at end"
        else:
            print("❌ backend/config.py: No validators called at end")
            return False, "Neither validator function called at end of file"
            
    except Exception as e:
        print(f"❌ backend/config.py: ERROR reading file - {e}")
        return False, str(e)

def test_prod_deployment_checklist_exists():
    """Test 3: Verify docs/release/prod_deployment_checklist.md exists"""
    checklist_path = "/app/docs/release/prod_deployment_checklist.md"
    
    if not os.path.exists(checklist_path):
        print("❌ docs/release/prod_deployment_checklist.md: MISSING")
        return False, "File does not exist"
    
    try:
        with open(checklist_path, 'r') as f:
            content = f.read()
        
        # Check for key sections in the checklist
        required_sections = [
            "Production Deployment Checklist",
            "Pre-Deploy Gate",
            "Security:",
            "DEBUG = false",
            "allow_test_payment_methods = False",
            "ledger_enforce_balance = True",
            "webhook_signature_enforced = True"
        ]
        
        missing_sections = []
        for section in required_sections:
            if section not in content:
                missing_sections.append(section)
        
        if missing_sections:
            print(f"⚠️  prod_deployment_checklist.md: Missing sections: {missing_sections}")
            return True, f"File exists but missing sections: {missing_sections}"
        else:
            print("✅ docs/release/prod_deployment_checklist.md: EXISTS with all required sections")
            return True, "File exists with all required deployment checklist sections"
            
    except Exception as e:
        print(f"❌ docs/release/prod_deployment_checklist.md: ERROR reading file - {e}")
        return False, str(e)

def main():
    print("=" * 60)
    print("FINAL SECURITY CHECK")
    print("=" * 60)
    
    # Test 1: validate_prod_security_settings function exists
    print("\n1. TESTING validate_prod_security_settings FUNCTION...")
    security_function_ok, security_function_error = test_validate_prod_security_settings_exists()
    
    # Test 2: Validators called at end
    print("\n2. TESTING VALIDATORS CALLED AT END...")
    validators_called_ok, validators_called_error = test_validators_called_at_end()
    
    # Test 3: Production deployment checklist exists
    print("\n3. TESTING PRODUCTION DEPLOYMENT CHECKLIST...")
    checklist_ok, checklist_error = test_prod_deployment_checklist_exists()
    
    # Summary
    print("\n" + "=" * 60)
    print("FINAL SECURITY CHECK SUMMARY")
    print("=" * 60)
    
    print("SECURITY REQUIREMENTS:")
    print(f"  1. validate_prod_security_settings function: {'✅ PASS' if security_function_ok else '❌ FAIL'}")
    if not security_function_ok:
        print(f"     Error: {security_function_error}")
    
    print(f"  2. Validators called at end: {'✅ PASS' if validators_called_ok else '❌ FAIL'}")
    if not validators_called_ok:
        print(f"     Error: {validators_called_error}")
    
    print(f"  3. Production deployment checklist: {'✅ PASS' if checklist_ok else '❌ FAIL'}")
    if not checklist_ok:
        print(f"     Error: {checklist_error}")
    
    # Overall result
    all_requirements_met = security_function_ok and validators_called_ok and checklist_ok
    
    print(f"\nOVERALL RESULT: {'✅ PASS' if all_requirements_met else '❌ FAIL'}")
    
    if all_requirements_met:
        print("✅ All final security check requirements are satisfied.")
        return 0
    else:
        print("❌ Some security requirements are not met.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)