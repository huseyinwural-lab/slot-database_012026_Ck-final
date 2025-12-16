#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend_test import CasinoAdminAPITester

def main():
    print("🎲 DICE ADVANCED LIMITS BACKEND VALIDATION TEST")
    print("=" * 60)
    
    tester = CasinoAdminAPITester()
    
    # Run only the dice advanced limits test
    result = tester.test_dice_advanced_limits_backend_validation()
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    status = "✅ PASS" if result else "❌ FAIL"
    print(f"Dice Advanced Limits Backend Validation: {status}")
    
    print(f"\nTotal API Calls: {tester.tests_run}")
    print(f"Passed: {tester.tests_passed}")
    print(f"Failed: {tester.tests_run - tester.tests_passed}")
    
    if tester.failed_tests:
        print("\n❌ FAILED API CALLS:")
        for i, failed in enumerate(tester.failed_tests, 1):
            print(f"\n{i}. {failed['name']}")
            print(f"   Endpoint: {failed['endpoint']}")
            if 'error' in failed:
                print(f"   Error: {failed['error']}")
            else:
                print(f"   Expected: {failed['expected']}, Got: {failed['actual']}")
                print(f"   Response: {failed['response']}")
    
    return 0 if result else 1

if __name__ == "__main__":
    sys.exit(main())