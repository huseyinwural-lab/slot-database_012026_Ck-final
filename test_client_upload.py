#!/usr/bin/env python3

import sys
import os
sys.path.append('/app')

from backend_test import CasinoAdminAPITester

def main():
    # Use the production URL from frontend/.env
    base_url = "https://casino-admin-panel-3.preview.emergentagent.com"
    
    tester = CasinoAdminAPITester(base_url)
    
    print("🚀 Starting Client Upload Flow Tests...")
    print(f"🌐 Base URL: {base_url}")
    
    # Run the client upload flow test
    success = tester.test_client_upload_flow()
    
    # Print summary
    print(f"\n📊 TEST SUMMARY")
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Tests Failed: {len(tester.failed_tests)}")
    
    if tester.failed_tests:
        print(f"\n❌ FAILED TESTS:")
        for failed in tester.failed_tests:
            print(f"  - {failed['name']}: Expected {failed.get('expected', 'N/A')}, Got {failed.get('actual', 'N/A')}")
    
    if success:
        print(f"\n✅ ALL CLIENT UPLOAD TESTS PASSED!")
        return 0
    else:
        print(f"\n❌ SOME CLIENT UPLOAD TESTS FAILED!")
        return 1

if __name__ == "__main__":
    sys.exit(main())