#!/usr/bin/env python3
"""
Tenant Kill Switch Test - Verify 503 MODULE_TEMPORARILY_DISABLED response
"""

import requests
import json
import sys

class TenantKillSwitchTester:
    def __init__(self, base_url="https://casino-platform-16.preview.emergentagent.com"):
        self.base_url = base_url
        self.access_token = None

    def setup_auth(self):
        """Setup authentication"""
        print("🔍 Setup: Login as admin@casino.com/Admin123!")
        
        try:
            # Login as admin@casino.com/Admin123!
            login_url = f"{self.base_url}/api/v1/auth/login"
            login_data = {
                "email": "admin@casino.com",
                "password": "Admin123!"
            }
            login_response = requests.post(login_url, json=login_data, timeout=30)
            
            if login_response.status_code == 200:
                login_json = login_response.json()
                if 'access_token' in login_json:
                    self.access_token = login_json['access_token']
                    print(f"   ✅ Authentication successful")
                    return True
                else:
                    print("   ❌ Login response missing access_token")
                    return False
            else:
                print(f"   ❌ Login failed: {login_response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Authentication setup error: {str(e)}")
            return False

    def test_tenant_kill_switch(self):
        """Test tenant kill switch functionality"""
        if not self.access_token:
            print("   ❌ No access token available")
            return False
        
        print("\n🔍 Test: Tenant Kill Switch - Set and Verify 503 Response")
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-Tenant-ID': 'default_casino',
            'Content-Type': 'application/json'
        }
        
        try:
            # Step 1: Set tenant kill switch for experiments module
            print("\n   🔧 Step 1: Set tenant kill switch for experiments module")
            kill_switch_url = f"{self.base_url}/api/v1/kill-switch/tenant"
            kill_switch_data = {
                "tenant_id": "default_casino",
                "module_key": "experiments",
                "disabled": True
            }
            
            response = requests.post(kill_switch_url, json=kill_switch_data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                response_data = response.json()
                print(f"   ✅ Kill switch set successfully")
                print(f"      Response: {response_data}")
            else:
                print(f"   ❌ Failed to set kill switch: {response.status_code}")
                print(f"      Response: {response.text}")
                return False
            
            # Step 2: Test that feature flags endpoint now returns 503
            print("\n   🔍 Step 2: Test feature flags endpoint - expect 503 MODULE_TEMPORARILY_DISABLED")
            features_url = f"{self.base_url}/api/v1/features/"
            
            response = requests.get(features_url, headers=headers, timeout=30)
            
            if response.status_code == 503:
                try:
                    response_data = response.json()
                    error_code = response_data.get('error_code')
                    detail = response_data.get('detail')
                    module = response_data.get('module')
                    reason = response_data.get('reason')
                    
                    print(f"   ✅ Tenant kill switch working - 503 MODULE_TEMPORARILY_DISABLED")
                    print(f"      error_code: {error_code}")
                    print(f"      detail: {detail}")
                    print(f"      module: {module}")
                    print(f"      reason: {reason}")
                    
                    if (error_code == 'MODULE_TEMPORARILY_DISABLED' and 
                        module == 'experiments' and 
                        reason == 'tenant_kill_switch'):
                        print(f"   ✅ AppError structure validated for tenant kill switch")
                        success_503 = True
                    else:
                        print(f"   ❌ Unexpected AppError structure")
                        success_503 = False
                        
                except Exception as e:
                    print(f"   ❌ Failed to parse 503 response: {str(e)}")
                    success_503 = False
            else:
                print(f"   ❌ Expected 503, got {response.status_code}")
                print(f"      Response: {response.text}")
                success_503 = False
            
            # Step 3: Disable kill switch
            print("\n   🔧 Step 3: Disable tenant kill switch")
            kill_switch_data["disabled"] = False
            
            response = requests.post(kill_switch_url, json=kill_switch_data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                print(f"   ✅ Kill switch disabled successfully")
            else:
                print(f"   ❌ Failed to disable kill switch: {response.status_code}")
                return False
            
            # Step 4: Verify feature flags endpoint works again
            print("\n   🔍 Step 4: Verify feature flags endpoint works again - expect 200")
            response = requests.get(features_url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                print(f"   ✅ Feature flags endpoint restored - 200 OK")
                success_restore = True
            else:
                print(f"   ❌ Feature flags endpoint still not working: {response.status_code}")
                success_restore = False
            
            return success_503 and success_restore
            
        except Exception as e:
            print(f"   ❌ Tenant kill switch test error: {str(e)}")
            return False

    def run_test(self):
        """Run tenant kill switch test"""
        print("🚫 TENANT KILL SWITCH VALIDATION TEST")
        print("=" * 60)
        
        # Setup authentication
        success_login = self.setup_auth()
        if not success_login:
            print("❌ Authentication setup failed - cannot proceed with tests")
            return False
        
        # Test tenant kill switch
        success_kill_switch = self.test_tenant_kill_switch()
        
        print("\n" + "=" * 60)
        if success_kill_switch:
            print("✅ TENANT KILL SWITCH VALIDATION - TEST PASSED")
            print("   ✅ Tenant kill switch can be enabled/disabled")
            print("   ✅ 503 MODULE_TEMPORARILY_DISABLED response working")
            print("   ✅ AppError structure validated for tenant kill switch")
            print("   ✅ Module access restored after disabling kill switch")
        else:
            print("❌ TENANT KILL SWITCH VALIDATION - TEST FAILED")
        
        return success_kill_switch

def main():
    tester = TenantKillSwitchTester()
    success = tester.run_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())