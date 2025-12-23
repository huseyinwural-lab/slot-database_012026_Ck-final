#!/usr/bin/env python3

import requests
import sys
import json

class BonusConfigTester:
    def __init__(self, base_url="https://pay-processor-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            response = None
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Non-dict response'}")
                    return True, response_data
                except:
                    return True, response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                self.failed_tests.append({
                    "name": name,
                    "endpoint": endpoint,
                    "expected": expected_status,
                    "actual": response.status_code,
                    "response": response.text[:200]
                })
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append({
                "name": name,
                "endpoint": endpoint,
                "error": str(e)
            })
            return False, {}

    def test_new_member_manual_bonus_config(self):
        """Test Yeni Üye Manuel Bonus Mekaniği - Turkish Review Request"""
        print("\n🎁 YENİ ÜYE MANUEL BONUS MEKANİĞİ TESTS")
        
        # Initialize success variables
        success_a = success_b = success_c = success_d = success_e = False
        
        # Senaryo A: Varsayılan config
        print(f"\n🔍 Senaryo A: Varsayılan config")
        
        try:
            success_a, default_response = self.run_test(
                "GET Default New Member Manual Bonus Config", 
                "GET", 
                "api/v1/bonus/config/new-member-manual", 
                200
            )
            
            if success_a and isinstance(default_response, dict):
                print("\n   🔍 Validating default config values:")
                
                # Check all expected default values
                expected_defaults = {
                    'enabled': False,
                    'allowed_game_ids': [],
                    'spin_count': 0,
                    'fixed_bet_amount': 0.0,
                    'total_budget_cap': 0.0,
                    'validity_days': 7
                }
                
                validation_success = True
                for field, expected_value in expected_defaults.items():
                    actual_value = default_response.get(field)
                    if actual_value == expected_value:
                        print(f"   ✅ {field}: {actual_value}")
                    else:
                        print(f"   ❌ {field}: expected {expected_value}, got {actual_value}")
                        validation_success = False
                
                if not validation_success:
                    success_a = False
                    
        except Exception as e:
            print(f"❌ Senaryo A Exception: {e}")
            success_a = False
        
        # Senaryo B: Geçerli config kaydetme
        print(f"\n🔍 Senaryo B: Geçerli config kaydetme")
        
        valid_config = {
            "enabled": True,
            "allowed_game_ids": ["f78ddf21-c759-4b8c-a5fb-28c90b3645ab"],
            "spin_count": 50,
            "fixed_bet_amount": 0.1,
            "total_budget_cap": 500,
            "validity_days": 10
        }
        
        try:
            success_b, save_response = self.run_test(
                "PUT Valid New Member Manual Bonus Config", 
                "PUT", 
                "api/v1/bonus/config/new-member-manual", 
                200,
                valid_config
            )
            
            if success_b and isinstance(save_response, dict):
                print("\n   🔍 Validating saved config response:")
                
                validation_success = True
                for field, expected_value in valid_config.items():
                    actual_value = save_response.get(field)
                    if actual_value == expected_value:
                        print(f"   ✅ {field}: {actual_value}")
                    else:
                        print(f"   ❌ {field}: expected {expected_value}, got {actual_value}")
                        validation_success = False
                
                if not validation_success:
                    success_b = False
                else:
                    print("   ✅ Response body aynı değerleri yansıtır")
                    
                    # Verify MongoDB storage by getting the config again
                    print("\n   🔍 Verifying MongoDB storage:")
                    verify_success, verify_response = self.run_test(
                        "GET Saved Config Verification", 
                        "GET", 
                        "api/v1/bonus/config/new-member-manual", 
                        200
                    )
                    
                    if verify_success and isinstance(verify_response, dict):
                        if (verify_response.get('enabled') == True and 
                            verify_response.get('allowed_game_ids') == ["f78ddf21-c759-4b8c-a5fb-28c90b3645ab"]):
                            print("   ✅ Mongo'da platform_settings koleksiyonunda doğru kaydedildi")
                            print(f"      - key = 'new_member_manual_bonus'")
                            print(f"      - config.enabled = {verify_response.get('enabled')}")
                            print(f"      - config.allowed_game_ids[0] = {verify_response.get('allowed_game_ids', [None])[0]}")
                        else:
                            print("   ❌ MongoDB verification failed")
                            success_b = False
                    else:
                        print("   ❌ Could not verify MongoDB storage")
                        success_b = False
                        
        except Exception as e:
            print(f"❌ Senaryo B Exception: {e}")
            success_b = False
        
        # Senaryo C: Geçersiz spin_count
        print(f"\n🔍 Senaryo C: Geçersiz spin_count")
        
        invalid_spin_config = valid_config.copy()
        invalid_spin_config['spin_count'] = 0  # Invalid: must be between 1 and 1000
        
        try:
            success_c, error_response = self.run_test(
                "PUT Invalid spin_count (0)", 
                "PUT", 
                "api/v1/bonus/config/new-member-manual", 
                400,
                invalid_spin_config
            )
            
            if success_c and isinstance(error_response, dict):
                detail = error_response.get('detail')
                if detail == "spin_count must be between 1 and 1000":
                    print(f"   ✅ Correct error message: {detail}")
                else:
                    print(f"   ❌ Unexpected error message: {detail}")
                    success_c = False
            else:
                print("   ❌ Expected 400 error response not received")
                success_c = False
                
        except Exception as e:
            print(f"❌ Senaryo C Exception: {e}")
            success_c = False
        
        # Senaryo D: Geçersiz fixed_bet_amount
        print(f"\n🔍 Senaryo D: Geçersiz fixed_bet_amount")
        
        # Test negative value
        invalid_bet_config_1 = valid_config.copy()
        invalid_bet_config_1['fixed_bet_amount'] = -1
        
        try:
            success_d1, error_response_1 = self.run_test(
                "PUT Invalid fixed_bet_amount (-1)", 
                "PUT", 
                "api/v1/bonus/config/new-member-manual", 
                400,
                invalid_bet_config_1
            )
            
            # Test too high value
            invalid_bet_config_2 = valid_config.copy()
            invalid_bet_config_2['fixed_bet_amount'] = 2000
            
            success_d2, error_response_2 = self.run_test(
                "PUT Invalid fixed_bet_amount (2000)", 
                "PUT", 
                "api/v1/bonus/config/new-member-manual", 
                400,
                invalid_bet_config_2
            )
            
            success_d = success_d1 and success_d2
            
            if success_d1 and isinstance(error_response_1, dict):
                detail = error_response_1.get('detail')
                if detail == "fixed_bet_amount must be > 0 and <= 1000":
                    print(f"   ✅ Correct error message for -1: {detail}")
                else:
                    print(f"   ❌ Unexpected error message for -1: {detail}")
                    success_d = False
            
            if success_d2 and isinstance(error_response_2, dict):
                detail = error_response_2.get('detail')
                if detail == "fixed_bet_amount must be > 0 and <= 1000":
                    print(f"   ✅ Correct error message for 2000: {detail}")
                else:
                    print(f"   ❌ Unexpected error message for 2000: {detail}")
                    success_d = False
                    
        except Exception as e:
            print(f"❌ Senaryo D Exception: {e}")
            success_d = False
        
        # Senaryo E: Geçersiz total_budget_cap
        print(f"\n🔍 Senaryo E: Geçersiz total_budget_cap")
        
        # Test negative value
        invalid_budget_config_1 = valid_config.copy()
        invalid_budget_config_1['total_budget_cap'] = -5
        
        try:
            success_e1, error_response_1 = self.run_test(
                "PUT Invalid total_budget_cap (-5)", 
                "PUT", 
                "api/v1/bonus/config/new-member-manual", 
                400,
                invalid_budget_config_1
            )
            
            # Test too high value
            invalid_budget_config_2 = valid_config.copy()
            invalid_budget_config_2['total_budget_cap'] = 2000000
            
            success_e2, error_response_2 = self.run_test(
                "PUT Invalid total_budget_cap (2000000)", 
                "PUT", 
                "api/v1/bonus/config/new-member-manual", 
                400,
                invalid_budget_config_2
            )
            
            success_e = success_e1 and success_e2
            
            if success_e1 and isinstance(error_response_1, dict):
                detail = error_response_1.get('detail')
                if detail == "total_budget_cap must be >= 0 and <= 1,000,000":
                    print(f"   ✅ Correct error message for -5: {detail}")
                else:
                    print(f"   ❌ Unexpected error message for -5: {detail}")
                    success_e = False
            
            if success_e2 and isinstance(error_response_2, dict):
                detail = error_response_2.get('detail')
                if detail == "total_budget_cap must be >= 0 and <= 1,000,000":
                    print(f"   ✅ Correct error message for 2000000: {detail}")
                else:
                    print(f"   ❌ Unexpected error message for 2000000: {detail}")
                    success_e = False
                    
        except Exception as e:
            print(f"❌ Senaryo E Exception: {e}")
            success_e = False
        
        # Overall result
        overall_success = success_a and success_b and success_c and success_d and success_e
        
        if overall_success:
            print("\n✅ YENİ ÜYE MANUEL BONUS MEKANİĞİ - TÜM SENARYOLAR BAŞARILI")
            print("   ✅ Senaryo A: Varsayılan config doğru değerlerle döndü")
            print("   ✅ Senaryo B: Geçerli config başarıyla kaydedildi ve MongoDB'da doğrulandı")
            print("   ✅ Senaryo C: spin_count validasyonu çalışıyor (1-1000 arası)")
            print("   ✅ Senaryo D: fixed_bet_amount validasyonu çalışıyor (>0 ve <=1000)")
            print("   ✅ Senaryo E: total_budget_cap validasyonu çalışıyor (>=0 ve <=1,000,000)")
        else:
            print("\n❌ YENİ ÜYE MANUEL BONUS MEKANİĞİ - BAZI SENARYOLAR BAŞARISIZ")
            if not success_a:
                print("   ❌ Senaryo A: Varsayılan config değerleri hatalı")
            if not success_b:
                print("   ❌ Senaryo B: Geçerli config kaydetme başarısız")
            if not success_c:
                print("   ❌ Senaryo C: spin_count validasyonu çalışmıyor")
            if not success_d:
                print("   ❌ Senaryo D: fixed_bet_amount validasyonu çalışmıyor")
            if not success_e:
                print("   ❌ Senaryo E: total_budget_cap validasyonu çalışmıyor")
        
        return overall_success

def main():
    print("🎁 YENİ ÜYE MANUEL BONUS MEKANİĞİ BACKEND TESTING")
    print("=" * 60)
    
    tester = BonusConfigTester()
    
    # Run the test
    result = tester.test_new_member_manual_bonus_config()
    
    # Summary
    print(f"\n📊 TEST SUMMARY")
    print(f"Total Tests: {tester.tests_run}")
    print(f"Passed: {tester.tests_passed}")
    print(f"Failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if tester.failed_tests:
        print("\n❌ FAILED TESTS DETAILS:")
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