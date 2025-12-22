#!/usr/bin/env python3
"""
FAZ 5 – Robot Orchestrator Backend Endpoint Tests
Turkish Review Request Implementation
"""

import requests
import json
import sys
from datetime import datetime

class RobotOrchestratorTester:
    def __init__(self, base_url="https://casino-finance-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.access_token = None
        self.api_key_a = None  # Key with robot.run + games.read
        self.api_key_b = None  # Key with only games.read

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30, auth_token=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        # Add Authorization header if token provided
        if auth_token:
            headers['Authorization'] = f'Bearer {auth_token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        if auth_token:
            print(f"   Auth: Bearer {auth_token[:20]}...")
        
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
                return False, response.text

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append({
                "name": name,
                "endpoint": endpoint,
                "error": str(e)
            })
            return False, {}

    def prepare_robot_orchestrator_tests(self):
        """Prepare Robot Orchestrator tests by seeding admin and creating API keys"""
        print("\n🔍 Hazırlık: Admin seed ve API key oluşturma")
        
        try:
            # Step 1: Seed admin data
            success1, _ = self.run_test("Seed Admin Data", "POST", "api/v1/admin/seed", 200)
            if not success1:
                print("   ❌ Admin seed başarısız")
                return False
            
            # Step 2: Login and get JWT token
            login_payload = {
                "email": "admin@casino.com",
                "password": "Admin123!"
            }
            success2, login_response = self.run_test("Admin Login", "POST", "api/v1/auth/login", 200, login_payload)
            if not success2 or not isinstance(login_response, dict) or 'access_token' not in login_response:
                print("   ❌ Admin login başarısız")
                return False
            
            self.access_token = login_response['access_token']
            print(f"   ✅ JWT token alındı: {self.access_token[:20]}...")
            
            # Step 3: Create API Key A with robot.run and games.read scopes
            api_key_a_payload = {
                "name": "Robot Test Key A",
                "scopes": ["robot.run", "games.read"]
            }
            success3, key_a_response = self.run_test("Create API Key A", "POST", "api/v1/api-keys", 201, api_key_a_payload, auth_token=self.access_token)
            if not success3 or not isinstance(key_a_response, dict) or 'api_key' not in key_a_response:
                print("   ❌ API Key A oluşturma başarısız")
                return False
            
            self.api_key_a = key_a_response['api_key']
            print(f"   ✅ API Key A oluşturuldu: {self.api_key_a[:20]}...")
            
            # Step 4: Create API Key B with only games.read scope (no robot.run)
            api_key_b_payload = {
                "name": "Robot Test Key B",
                "scopes": ["games.read"]
            }
            success4, key_b_response = self.run_test("Create API Key B", "POST", "api/v1/api-keys", 201, api_key_b_payload, auth_token=self.access_token)
            if not success4 or not isinstance(key_b_response, dict) or 'api_key' not in key_b_response:
                print("   ❌ API Key B oluşturma başarısız")
                return False
            
            self.api_key_b = key_b_response['api_key']
            print(f"   ✅ API Key B oluşturuldu: {self.api_key_b[:20]}...")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Hazırlık hatası: {str(e)}")
            return False

    def test_robot_orchestrator_happy_path(self):
        """Test 1 – Mutlu path (geçerli API key + robot.run scope)"""
        print("\n🔍 Test 1 – Mutlu path (geçerli API key + robot.run scope)")
        
        try:
            payload = {
                "game_types": ["slot", "crash"],
                "rounds": 10
            }
            
            success, response = self.run_test("Robot Round Happy Path", "POST", "api/v1/robot/round", 200, payload, auth_token=self.api_key_a)
            
            if success and isinstance(response, dict):
                # Validate response structure
                required_fields = ['status', 'tenant_id', 'total_rounds', 'results']
                missing_fields = [field for field in required_fields if field not in response]
                
                if not missing_fields:
                    print(f"   ✅ Response structure complete")
                    print(f"   📊 Status: {response['status']}")
                    print(f"   🏢 Tenant ID: {response['tenant_id']}")
                    print(f"   🎯 Total Rounds: {response['total_rounds']}")
                    
                    # Validate results array
                    results = response.get('results', [])
                    if isinstance(results, list) and len(results) == 2:  # slot and crash
                        print(f"   ✅ Results array has {len(results)} summaries")
                        for result in results:
                            if isinstance(result, dict):
                                game_type = result.get('game_type')
                                rounds = result.get('rounds', 0)
                                errors = result.get('errors', 0)
                                print(f"      - {game_type}: rounds={rounds}, errors={errors}")
                        
                        # Check expected values
                        if response['status'] == 'ok' and response['tenant_id'] == 'default_casino':
                            print(f"   ✅ Expected values confirmed")
                            return True
                        else:
                            print(f"   ❌ Unexpected values: status={response['status']}, tenant_id={response['tenant_id']}")
                    else:
                        print(f"   ❌ Results array invalid: expected 2 items, got {len(results) if isinstance(results, list) else 'non-list'}")
                else:
                    print(f"   ❌ Response missing fields: {missing_fields}")
            else:
                print(f"   ❌ Invalid response or request failed")
            
            return False
            
        except Exception as e:
            print(f"   ❌ Test error: {str(e)}")
            return False

    def test_robot_orchestrator_rounds_limits(self):
        """Test 2 – rounds limitleri"""
        print("\n🔍 Test 2 – rounds limitleri")
        
        try:
            # Test rounds=0 (should fail)
            payload1 = {
                "game_types": ["slot"],
                "rounds": 0
            }
            success1, response1 = self.run_test("Robot Round - rounds=0", "POST", "api/v1/robot/round", 400, payload1, auth_token=self.api_key_a)
            
            rounds_0_valid = False
            if success1:  # Expecting 400 - success means we got the expected status code
                try:
                    error_data = json.loads(response1) if isinstance(response1, str) else response1
                    if isinstance(error_data, dict) and error_data.get('detail', {}).get('error_code') == 'ROBOT_ROUNDS_LIMIT_EXCEEDED':
                        print(f"   ✅ rounds=0 correctly rejected with ROBOT_ROUNDS_LIMIT_EXCEEDED")
                        rounds_0_valid = True
                    else:
                        print(f"   ❌ rounds=0 rejected but wrong error_code: {error_data}")
                except:
                    print(f"   ❌ rounds=0 rejected but couldn't parse error: {response1}")
            else:
                print(f"   ❌ rounds=0 should have been rejected but got unexpected status")
            
            # Test rounds=2000 (should fail)
            payload2 = {
                "game_types": ["slot"],
                "rounds": 2000
            }
            success2, response2 = self.run_test("Robot Round - rounds=2000", "POST", "api/v1/robot/round", 400, payload2, auth_token=self.api_key_a)
            
            rounds_2000_valid = False
            if success2:  # Expecting 400 - success means we got the expected status code
                try:
                    error_data = json.loads(response2) if isinstance(response2, str) else response2
                    if isinstance(error_data, dict) and error_data.get('detail', {}).get('error_code') == 'ROBOT_ROUNDS_LIMIT_EXCEEDED':
                        print(f"   ✅ rounds=2000 correctly rejected with ROBOT_ROUNDS_LIMIT_EXCEEDED")
                        rounds_2000_valid = True
                    else:
                        print(f"   ❌ rounds=2000 rejected but wrong error_code: {error_data}")
                except:
                    print(f"   ❌ rounds=2000 rejected but couldn't parse error: {response2}")
            else:
                print(f"   ❌ rounds=2000 should have been rejected but got unexpected status")
            
            return rounds_0_valid and rounds_2000_valid
            
        except Exception as e:
            print(f"   ❌ Test error: {str(e)}")
            return False

    def test_robot_orchestrator_game_types_limits(self):
        """Test 3 – game_types whitelist & toplam iş yükü"""
        print("\n🔍 Test 3 – game_types whitelist & toplam iş yükü")
        
        try:
            # Test unsupported game type (blackjack)
            payload1 = {
                "game_types": ["slot", "blackjack"],
                "rounds": 10
            }
            success1, response1 = self.run_test("Robot Round - unsupported game type", "POST", "api/v1/robot/round", 400, payload1, auth_token=self.api_key_a)
            
            unsupported_game_valid = False
            if success1:  # Expecting 400 - success means we got the expected status code
                try:
                    error_data = json.loads(response1) if isinstance(response1, str) else response1
                    if isinstance(error_data, dict):
                        detail = error_data.get('detail', {})
                        if detail.get('error_code') == 'ROBOT_GAME_TYPE_UNSUPPORTED' and detail.get('game_type') == 'blackjack':
                            print(f"   ✅ Unsupported game type correctly rejected: blackjack")
                            unsupported_game_valid = True
                        else:
                            print(f"   ❌ Unsupported game type rejected but wrong error: {detail}")
                except:
                    print(f"   ❌ Unsupported game type rejected but couldn't parse error: {response1}")
            else:
                print(f"   ❌ Unsupported game type should have been rejected but got unexpected status")
            
            # Test total work exceeded (6 types * 900 rounds = 5400 > 5000)
            # The backend doesn't deduplicate, so 6 game types * 900 rounds = 5400 > 5000
            payload2 = {
                "game_types": ["slot", "crash", "dice", "slot", "crash", "dice"],  # 6 types (duplicates allowed)
                "rounds": 900  # 6 * 900 = 5400 > 5000 (MAX_TOTAL_WORK)
            }
            success2, response2 = self.run_test("Robot Round - total work exceeded", "POST", "api/v1/robot/round", 400, payload2, auth_token=self.api_key_a)
            
            total_work_valid = False
            if success2:  # Expecting 400 - success means we got the expected status code
                try:
                    error_data = json.loads(response2) if isinstance(response2, str) else response2
                    if isinstance(error_data, dict) and error_data.get('detail', {}).get('error_code') == 'ROBOT_TOTAL_WORK_EXCEEDED':
                        print(f"   ✅ Total work exceeded correctly rejected")
                        total_work_valid = True
                    else:
                        print(f"   ❌ Total work exceeded rejected but wrong error_code: {error_data}")
                except:
                    print(f"   ❌ Total work exceeded rejected but couldn't parse error: {response2}")
            else:
                print(f"   ❌ Total work exceeded should have been rejected but got unexpected status")
            
            return unsupported_game_valid and total_work_valid
            
        except Exception as e:
            print(f"   ❌ Test error: {str(e)}")
            return False

    def test_robot_orchestrator_scope_missing(self):
        """Test 4 – Scope eksik"""
        print("\n🔍 Test 4 – Scope eksik")
        
        try:
            payload = {
                "game_types": ["slot"],
                "rounds": 10
            }
            
            success, response = self.run_test("Robot Round - scope missing", "POST", "api/v1/robot/round", 403, payload, auth_token=self.api_key_b)
            
            if success:  # Expecting 403 - success means we got the expected status code
                try:
                    error_data = json.loads(response) if isinstance(response, str) else response
                    if isinstance(error_data, dict) and error_data.get('detail', {}).get('error_code') == 'API_KEY_SCOPE_FORBIDDEN':
                        print(f"   ✅ Scope missing correctly rejected with API_KEY_SCOPE_FORBIDDEN")
                        return True
                    else:
                        print(f"   ❌ Scope missing rejected but wrong error_code: {error_data}")
                except:
                    print(f"   ❌ Scope missing rejected but couldn't parse error: {response}")
            else:
                print(f"   ❌ Scope missing should have been rejected but got unexpected status")
            
            return False
            
        except Exception as e:
            print(f"   ❌ Test error: {str(e)}")
            return False

    def test_robot_orchestrator_tenant_mismatch(self):
        """Test 5 – Tenant mismatch"""
        print("\n🔍 Test 5 – Tenant mismatch")
        
        try:
            payload = {
                "game_types": ["slot"],
                "rounds": 10,
                "tenant_id": "some_other_tenant"
            }
            
            success, response = self.run_test("Robot Round - tenant mismatch", "POST", "api/v1/robot/round", 403, payload, auth_token=self.api_key_a)
            
            if success:  # Expecting 403 - success means we got the expected status code
                try:
                    error_data = json.loads(response) if isinstance(response, str) else response
                    if isinstance(error_data, dict):
                        detail = error_data.get('detail', {})
                        if (detail.get('error_code') == 'TENANT_MISMATCH' and 
                            detail.get('api_key_tenant') == 'default_casino' and 
                            detail.get('requested_tenant') == 'some_other_tenant'):
                            print(f"   ✅ Tenant mismatch correctly rejected")
                            print(f"      - API key tenant: {detail.get('api_key_tenant')}")
                            print(f"      - Requested tenant: {detail.get('requested_tenant')}")
                            return True
                        else:
                            print(f"   ❌ Tenant mismatch rejected but wrong error details: {detail}")
                except:
                    print(f"   ❌ Tenant mismatch rejected but couldn't parse error: {response}")
            else:
                print(f"   ❌ Tenant mismatch should have been rejected but got unexpected status")
            
            return False
            
        except Exception as e:
            print(f"   ❌ Test error: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all Robot Orchestrator tests"""
        print("🤖 FAZ 5 – ROBOT ORCHESTRATOR BACKEND ENDPOINT TESTS")
        print("=" * 60)
        
        # Hazırlık: Seed admin data and create API keys
        success_prep = self.prepare_robot_orchestrator_tests()
        if not success_prep:
            print("❌ Hazırlık başarısız. Testlere devam edilemiyor.")
            return False
        
        # Test 1 – Mutlu path (geçerli API key + robot.run scope)
        success_test1 = self.test_robot_orchestrator_happy_path()
        
        # Test 2 – rounds limitleri
        success_test2 = self.test_robot_orchestrator_rounds_limits()
        
        # Test 3 – game_types whitelist & toplam iş yükü
        success_test3 = self.test_robot_orchestrator_game_types_limits()
        
        # Test 4 – Scope eksik
        success_test4 = self.test_robot_orchestrator_scope_missing()
        
        # Test 5 – Tenant mismatch
        success_test5 = self.test_robot_orchestrator_tenant_mismatch()
        
        # Overall result
        overall_success = success_prep and success_test1 and success_test2 and success_test3 and success_test4 and success_test5
        
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        if overall_success:
            print("✅ FAZ 5 – ROBOT ORCHESTRATOR BACKEND ENDPOINT - TÜM TESTLER BAŞARILI")
            print("   ✅ Hazırlık: Admin seed ve API key oluşturma başarılı")
            print("   ✅ Test 1: Mutlu path başarılı")
            print("   ✅ Test 2: Rounds limitleri başarılı")
            print("   ✅ Test 3: Game types whitelist & toplam iş yükü başarılı")
            print("   ✅ Test 4: Scope eksik validation başarılı")
            print("   ✅ Test 5: Tenant mismatch validation başarılı")
        else:
            print("❌ FAZ 5 – ROBOT ORCHESTRATOR BACKEND ENDPOINT - BAZI TESTLER BAŞARISIZ")
            if not success_prep:
                print("   ❌ Hazırlık başarısız")
            if not success_test1:
                print("   ❌ Test 1: Mutlu path başarısız")
            if not success_test2:
                print("   ❌ Test 2: Rounds limitleri başarısız")
            if not success_test3:
                print("   ❌ Test 3: Game types whitelist & toplam iş yükü başarısız")
            if not success_test4:
                print("   ❌ Test 4: Scope eksik validation başarısız")
            if not success_test5:
                print("   ❌ Test 5: Tenant mismatch validation başarısız")
        
        print(f"\nTotal Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.failed_tests:
            print("\n❌ FAILED TESTS DETAILS:")
            for i, failed in enumerate(self.failed_tests, 1):
                print(f"\n{i}. {failed['name']}")
                print(f"   Endpoint: {failed['endpoint']}")
                if 'error' in failed:
                    print(f"   Error: {failed['error']}")
                else:
                    print(f"   Expected: {failed['expected']}, Got: {failed['actual']}")
                    print(f"   Response: {failed['response']}")
        
        return overall_success


def main():
    """Main test runner"""
    tester = RobotOrchestratorTester()
    success = tester.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())