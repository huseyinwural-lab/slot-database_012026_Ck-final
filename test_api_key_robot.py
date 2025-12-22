#!/usr/bin/env python3
"""
Test API Key Auth Layer and Robot Backend Endpoint - Turkish Review Request

Base URL: REACT_APP_BACKEND_URL + /api

Hazırlık:
1) POST /api/v1/admin/seed
2) POST /api/v1/auth/login (admin@casino.com / Admin123!) ile JWT al.
3) POST /api/v1/api-keys ile geçerli bir key oluştur:
   Body: {"name":"Robot Key #Test","scopes":["robot.run","games.read"]}
   - Dönen response.api_key değerini testlerde kullan.

Test 1 – API key ile robot endpoint (mutlu path)
Test 2 – Scope eksik (robot.run yok)
Test 3 – Tenant mismatch
Test 4 – API key eksik / geçersiz
Test 5 – Game client upload: launch_url + min_version support
"""

import requests
import sys
import json
import subprocess
from datetime import datetime

class APIKeyRobotTester:
    def __init__(self, base_url="https://pspreconcile.preview.emergentagent.com"):
        self.base_url = base_url
        self.access_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30, auth_token=None, custom_headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        # Add Authorization header if token provided
        if auth_token:
            headers['Authorization'] = f'Bearer {auth_token}'
        
        # Add custom headers if provided
        if custom_headers:
            headers.update(custom_headers)

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

    def prepare_tests(self):
        """Hazırlık: Admin seed ve JWT token alma"""
        print("🔧 Hazırlık: Admin seed ve JWT token alma...")
        
        # Step 1: Seed admin data
        success1, seed_response = self.run_test("Admin Seed", "POST", "api/v1/admin/seed", 200)
        if not success1:
            print("❌ Admin seed başarısız")
            return False
        
        print("✅ Admin seed başarılı")
        
        # Step 2: Login to get JWT token
        login_data = {
            "email": "admin@casino.com",
            "password": "Admin123!"
        }
        success2, login_response = self.run_test("Admin Login", "POST", "api/v1/auth/login", 200, login_data)
        if not success2 or not isinstance(login_response, dict):
            print("❌ Admin login başarısız")
            return False
        
        # Store JWT token for authenticated requests
        self.access_token = login_response.get('access_token')
        if not self.access_token:
            print("❌ JWT token alınamadı")
            return False
        
        print(f"✅ JWT token alındı: {self.access_token[:20]}...")
        return True

    def test_1_robot_endpoint_happy_path(self):
        """Test 1: API key ile robot endpoint (mutlu path)"""
        print("\n🎯 Test 1: API key ile robot endpoint (mutlu path)")
        
        # Create API key with robot.run and games.read scopes
        api_key_data = {
            "name": "Robot Key #Test",
            "scopes": ["robot.run", "games.read"]
        }
        success1, create_response = self.run_test("Create API Key for Robot", "POST", "api/v1/api-keys", 201, api_key_data, auth_token=self.access_token)
        
        if not success1 or not isinstance(create_response, dict):
            print("❌ API key oluşturulamadı")
            return False, None
        
        api_key = create_response.get('api_key')
        if not api_key:
            print("❌ API key response'da bulunamadı")
            return False, None
        
        print(f"✅ API key oluşturuldu: {api_key[:20]}...")
        
        # Test robot endpoint with API key
        robot_data = {
            "game_types": ["slot", "crash"],
            "rounds": 10
        }
        
        success2, robot_response = self.run_test("Robot Round with API Key", "POST", "api/v1/robot/round", 200, robot_data, auth_token=api_key)
        
        if success2 and isinstance(robot_response, dict):
            # Validate response structure
            expected_fields = ['status', 'tenant_id', 'scopes']
            missing_fields = [field for field in expected_fields if field not in robot_response]
            
            if not missing_fields:
                print(f"✅ Response yapısı tam:")
                print(f"   - status: {robot_response.get('status')}")
                print(f"   - tenant_id: {robot_response.get('tenant_id')}")
                print(f"   - scopes: {robot_response.get('scopes')}")
                
                # Check expected values
                if (robot_response.get('status') == 'ok' and 
                    robot_response.get('tenant_id') == 'default_casino' and
                    'robot.run' in robot_response.get('scopes', [])):
                    print("✅ Tüm beklenen değerler doğru")
                    return True, api_key
                else:
                    print("❌ Beklenen değerler yanlış")
                    return False, api_key
            else:
                print(f"❌ Response eksik alanlar: {missing_fields}")
                return False, api_key
        else:
            print("❌ Robot endpoint başarısız")
            return False, api_key

    def test_2_scope_missing(self):
        """Test 2: Scope eksik (robot.run yok)"""
        print("\n🎯 Test 2: Scope eksik (robot.run yok)")
        
        # Create API key with only games.read scope (missing robot.run)
        api_key_data = {
            "name": "Limited Key #Test",
            "scopes": ["games.read"]
        }
        success1, create_response = self.run_test("Create Limited API Key", "POST", "api/v1/api-keys", 201, api_key_data, auth_token=self.access_token)
        
        if not success1 or not isinstance(create_response, dict):
            print("❌ Limited API key oluşturulamadı")
            return False
        
        limited_api_key = create_response.get('api_key')
        if not limited_api_key:
            print("❌ Limited API key response'da bulunamadı")
            return False
        
        print(f"✅ Limited API key oluşturuldu: {limited_api_key[:20]}...")
        
        # Test robot endpoint with limited API key (should fail with 403)
        robot_data = {
            "game_types": ["slot", "crash"],
            "rounds": 10
        }
        
        success2, error_response = self.run_test("Robot Round with Limited Key", "POST", "api/v1/robot/round", 403, robot_data, auth_token=limited_api_key)
        
        if success2:
            print("✅ Scope eksik validation başarılı - 403 döndü")
            
            # Parse and check error structure
            try:
                if isinstance(error_response, str):
                    error_data = json.loads(error_response)
                else:
                    error_data = error_response
                
                if isinstance(error_data, dict) and 'detail' in error_data:
                    detail = error_data['detail']
                    if isinstance(detail, dict):
                        error_code = detail.get('error_code')
                        scope = detail.get('scope')
                        
                        if error_code == 'API_KEY_SCOPE_FORBIDDEN' and scope == 'robot.run':
                            print(f"✅ Doğru hata yapısı: error_code={error_code}, scope={scope}")
                            return True
                        else:
                            print(f"❌ Beklenmeyen hata yapısı: error_code={error_code}, scope={scope}")
                            return False
                    else:
                        print(f"❌ Detail dict değil: {detail}")
                        return False
                else:
                    print(f"❌ Response yapısı beklenmeyen: {error_data}")
                    return False
            except Exception as e:
                print(f"❌ Error response parse hatası: {str(e)}")
                return False
        else:
            print("❌ Scope validation başarısız")
            return False

    def test_3_tenant_mismatch(self, api_key):
        """Test 3: Tenant mismatch"""
        print("\n🎯 Test 3: Tenant mismatch")
        
        if not api_key:
            print("❌ API key mevcut değil")
            return False
        
        # Test robot endpoint with different tenant_id in body
        robot_data = {
            "game_types": ["slot", "crash"],
            "rounds": 10,
            "tenant_id": "some_other_tenant"  # Different from API key's tenant_id
        }
        
        success, error_response = self.run_test("Robot Round with Tenant Mismatch", "POST", "api/v1/robot/round", 403, robot_data, auth_token=api_key)
        
        if success:
            print("✅ Tenant mismatch validation başarılı - 403 döndü")
            
            # Parse and check error structure
            try:
                if isinstance(error_response, str):
                    error_data = json.loads(error_response)
                else:
                    error_data = error_response
                
                if isinstance(error_data, dict) and 'detail' in error_data:
                    detail = error_data['detail']
                    if isinstance(detail, dict):
                        error_code = detail.get('error_code')
                        api_key_tenant = detail.get('api_key_tenant')
                        requested_tenant = detail.get('requested_tenant')
                        
                        if (error_code == 'TENANT_MISMATCH' and 
                            api_key_tenant == 'default_casino' and 
                            requested_tenant == 'some_other_tenant'):
                            print(f"✅ Doğru hata yapısı:")
                            print(f"   - error_code: {error_code}")
                            print(f"   - api_key_tenant: {api_key_tenant}")
                            print(f"   - requested_tenant: {requested_tenant}")
                            return True
                        else:
                            print(f"❌ Beklenmeyen hata yapısı: error_code={error_code}")
                            print(f"   api_key_tenant={api_key_tenant}, requested_tenant={requested_tenant}")
                            return False
                    else:
                        print(f"❌ Detail dict değil: {detail}")
                        return False
                else:
                    print(f"❌ Response yapısı beklenmeyen: {error_data}")
                    return False
            except Exception as e:
                print(f"❌ Error response parse hatası: {str(e)}")
                return False
        else:
            print("❌ Tenant mismatch validation başarısız")
            return False

    def test_4_missing_invalid_key(self):
        """Test 4: API key eksik / geçersiz"""
        print("\n🎯 Test 4: API key eksik / geçersiz")
        
        robot_data = {
            "game_types": ["slot", "crash"],
            "rounds": 10
        }
        
        # Test 1: No Authorization header
        success1, error_response1 = self.run_test("Robot Round without Auth", "POST", "api/v1/robot/round", 401, robot_data)
        
        if success1:
            print("✅ API key eksik validation başarılı - 401 döndü")
            
            # Check error structure
            try:
                if isinstance(error_response1, str):
                    error_data1 = json.loads(error_response1)
                else:
                    error_data1 = error_response1
                
                if isinstance(error_data1, dict) and 'detail' in error_data1:
                    detail = error_data1['detail']
                    if isinstance(detail, dict) and detail.get('error_code') == 'API_KEY_MISSING':
                        print(f"✅ Doğru hata kodu: {detail.get('error_code')}")
                    else:
                        print(f"❌ Beklenmeyen hata yapısı: {detail}")
                        success1 = False
                else:
                    print(f"❌ Response yapısı beklenmeyen: {error_data1}")
                    success1 = False
            except Exception as e:
                print(f"❌ Error response parse hatası: {str(e)}")
                success1 = False
        else:
            print("❌ API key eksik validation başarısız")
            success1 = False
        
        # Test 2: Invalid API key
        success2, error_response2 = self.run_test("Robot Round with Invalid Key", "POST", "api/v1/robot/round", 401, robot_data, auth_token="random_invalid_string")
        
        if success2:
            print("✅ API key geçersiz validation başarılı - 401 döndü")
            
            # Check error structure
            try:
                if isinstance(error_response2, str):
                    error_data2 = json.loads(error_response2)
                else:
                    error_data2 = error_response2
                
                if isinstance(error_data2, dict) and 'detail' in error_data2:
                    detail = error_data2['detail']
                    if isinstance(detail, dict) and detail.get('error_code') == 'API_KEY_INVALID':
                        print(f"✅ Doğru hata kodu: {detail.get('error_code')}")
                    else:
                        print(f"❌ Beklenmeyen hata yapısı: {detail}")
                        success2 = False
                else:
                    print(f"❌ Response yapısı beklenmeyen: {error_data2}")
                    success2 = False
            except Exception as e:
                print(f"❌ Error response parse hatası: {str(e)}")
                success2 = False
        else:
            print("❌ API key geçersiz validation başarısız")
            success2 = False
        
        return success1 and success2

    def test_5_cli_api_key_required(self):
        """Test 5: Game Robot CLI argüman zorunluluğu"""
        print("\n🎯 Test 5: Game Robot CLI argüman zorunluluğu")
        
        # Test CLI without --api-key argument
        try:
            # Run the game robot CLI without --api-key
            cmd = [
                "python", "-m", "backend.app.bots.game_robot",
                "--tenant-id", "default_casino",
                "--rounds", "1",
                "--game-types", "slot"
            ]
            
            result = subprocess.run(
                cmd,
                cwd="/app",
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Should fail with non-zero exit code
            if result.returncode != 0:
                print(f"✅ CLI API key zorunluluğu başarılı - Exit code: {result.returncode}")
                
                # Check if error message mentions --api-key is required
                stderr_output = result.stderr.lower()
                if 'api-key' in stderr_output and ('required' in stderr_output or 'argument' in stderr_output):
                    print(f"✅ Doğru hata mesajı: --api-key is required")
                    return True
                else:
                    print(f"❌ Beklenmeyen hata mesajı: {result.stderr}")
                    return False
            else:
                print(f"❌ CLI API key zorunluluğu başarısız - Expected non-zero exit code, got {result.returncode}")
                print(f"   Stdout: {result.stdout}")
                print(f"   Stderr: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ CLI test timeout")
            return False
        except Exception as e:
            print(f"❌ CLI test hatası: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all API key auth layer and robot endpoint tests"""
        print("🔑 API KEY AUTH LAYER & ROBOT ENDPOINT TESTS - Turkish Review Request")
        print("=" * 70)
        
        # Preparation
        if not self.prepare_tests():
            print("❌ Hazırlık başarısız. Testlere devam edilemiyor.")
            return False
        
        # Test 1: Happy path
        success1, api_key = self.test_1_robot_endpoint_happy_path()
        
        # Test 2: Scope missing
        success2 = self.test_2_scope_missing()
        
        # Test 3: Tenant mismatch
        success3 = self.test_3_tenant_mismatch(api_key)
        
        # Test 4: Missing/invalid key
        success4 = self.test_4_missing_invalid_key()
        
        # Test 5: CLI API key required
        success5 = self.test_5_cli_api_key_required()
        
        # Overall result
        overall_success = success1 and success2 and success3 and success4 and success5
        
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        
        tests = [
            ("Test 1: API key ile robot endpoint (mutlu path)", success1),
            ("Test 2: Scope eksik (robot.run yok)", success2),
            ("Test 3: Tenant mismatch", success3),
            ("Test 4: API key eksik / geçersiz", success4),
            ("Test 5: Game Robot CLI argüman zorunluluğu", success5)
        ]
        
        for test_name, result in tests:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name:<50} {status}")
        
        print(f"\nTotal Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if overall_success:
            print("\n✅ TÜM TESTLER BAŞARILI - API Key Auth Layer & Robot Endpoint çalışıyor!")
        else:
            print("\n❌ BAZI TESTLER BAŞARISIZ - Detaylar yukarıda")
            
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
    """Run the API key auth layer and robot endpoint tests"""
    tester = APIKeyRobotTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())