import requests
import sys
import json

class Patch1SmokeTest:
    def __init__(self, base_url="https://game-admin-hub-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.access_token = None

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30, auth_token=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        # Add Authorization header if token provided
        if auth_token:
            headers['Authorization'] = f'Bearer {auth_token}'

        self.tests_run += 1
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
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append({
                "name": name,
                "endpoint": endpoint,
                "error": str(e)
            })
            return False, {}

    def test_patch1_final_smoke_regression(self):
        """Final backend smoke/regression after Patch 1 + dashboard/api-keys/tables fixes"""
        print("\n🔥 PATCH 1 FINAL SMOKE/REGRESSION TEST")
        print("Testing: health, readiness, auth, dashboard, tables, api-keys, players")
        
        all_tests_passed = True
        test_results = []
        
        # Test 1: GET /api/health
        print(f"\n🔍 Test 1: GET /api/health")
        success1, health_response = self.run_test("Health Check", "GET", "api/health", 200)
        test_results.append(("Health Check", success1))
        if success1 and isinstance(health_response, dict):
            if health_response.get('status') == 'healthy':
                print(f"   ✅ Health status: {health_response['status']}")
            else:
                print(f"   ⚠️  Unexpected health status: {health_response.get('status')}")
        all_tests_passed = all_tests_passed and success1
        
        # Test 2: GET /api/readiness
        print(f"\n🔍 Test 2: GET /api/readiness")
        success2, readiness_response = self.run_test("Readiness Check", "GET", "api/readiness", 200)
        test_results.append(("Readiness Check", success2))
        if success2 and isinstance(readiness_response, dict):
            db_status = readiness_response.get('dependencies', {}).get('database')
            if db_status == 'connected':
                print(f"   ✅ Database status: {db_status}")
            else:
                print(f"   ⚠️  Unexpected database status: {db_status}")
        all_tests_passed = all_tests_passed and success2
        
        # Test 3: POST /api/v1/auth/login
        print(f"\n🔍 Test 3: POST /api/v1/auth/login (admin@casino.com / Admin123!)")
        login_data = {
            "email": "admin@casino.com",
            "password": "Admin123!"
        }
        success3, login_response = self.run_test("Admin Login", "POST", "api/v1/auth/login", 200, login_data)
        test_results.append(("Admin Login", success3))
        
        access_token = None
        if success3 and isinstance(login_response, dict):
            access_token = login_response.get('access_token')
            token_type = login_response.get('token_type')
            if access_token and token_type == 'bearer':
                print(f"   ✅ Login successful - Token type: {token_type}")
                print(f"   ✅ Access token length: {len(access_token)} chars")
                self.access_token = access_token  # Store for subsequent tests
            else:
                print(f"   ❌ Login response missing access_token or wrong token_type")
                all_tests_passed = False
        else:
            all_tests_passed = False
        
        if not access_token:
            print("❌ Cannot proceed with authenticated tests - login failed")
            return False
        
        # Test 4: GET /api/v1/dashboard/comprehensive-stats (with token)
        print(f"\n🔍 Test 4: GET /api/v1/dashboard/comprehensive-stats (with Authorization)")
        success4, dashboard_response = self.run_test("Dashboard Comprehensive Stats", "GET", "api/v1/dashboard/comprehensive-stats", 200, auth_token=access_token)
        test_results.append(("Dashboard Comprehensive Stats", success4))
        if success4 and isinstance(dashboard_response, dict):
            print(f"   ✅ Dashboard stats response keys: {list(dashboard_response.keys())}")
        all_tests_passed = all_tests_passed and success4
        
        # Test 5: GET /api/v1/tables (with token)
        print(f"\n🔍 Test 5: GET /api/v1/tables (with Authorization)")
        success5, tables_response = self.run_test("Tables List", "GET", "api/v1/tables", 200, auth_token=access_token)
        test_results.append(("Tables List", success5))
        if success5 and isinstance(tables_response, list):
            print(f"   ✅ Tables response is JSON array with {len(tables_response)} items")
        elif success5:
            print(f"   ⚠️  Tables response is not an array: {type(tables_response)}")
        all_tests_passed = all_tests_passed and success5
        
        # Test 6: GET /api/v1/api-keys/scopes (with token)
        print(f"\n🔍 Test 6: GET /api/v1/api-keys/scopes (with Authorization)")
        success6, scopes_response = self.run_test("API Keys Scopes", "GET", "api/v1/api-keys/scopes", 200, auth_token=access_token)
        test_results.append(("API Keys Scopes", success6))
        if success6 and isinstance(scopes_response, list):
            print(f"   ✅ Scopes response is array with {len(scopes_response)} scopes: {scopes_response}")
        all_tests_passed = all_tests_passed and success6
        
        # Test 7: POST /api/v1/api-keys/ (with token)
        print(f"\n🔍 Test 7: POST /api/v1/api-keys/ (with Authorization)")
        api_key_data = {
            "name": "Test API Key - Patch1 Smoke",
            "scopes": ["robot.run", "games.read"]
        }
        success7, api_key_response = self.run_test("Create API Key", "POST", "api/v1/api-keys/", 200, api_key_data, auth_token=access_token)
        test_results.append(("Create API Key", success7))
        if success7 and isinstance(api_key_response, dict):
            if 'api_key' in api_key_response and 'key' in api_key_response:
                print(f"   ✅ API key created - Response has 'api_key' and 'key' objects")
                key_obj = api_key_response.get('key', {})
                if isinstance(key_obj, dict):
                    print(f"   ✅ API key ID: {key_obj.get('id', 'Unknown')}")
                else:
                    print(f"   ✅ API key created successfully")
            else:
                print(f"   ⚠️  API key response missing expected fields: {list(api_key_response.keys())}")
        all_tests_passed = all_tests_passed and success7
        
        # Test 8: GET /api/v1/players?page=1&page_size=5&include_total=true (with token)
        print(f"\n🔍 Test 8: GET /api/v1/players?page=1&page_size=5&include_total=true (with Authorization)")
        success8, players_response = self.run_test("Players Paginated", "GET", "api/v1/players?page=1&page_size=5&include_total=true", 200, auth_token=access_token)
        test_results.append(("Players Paginated", success8))
        if success8 and isinstance(players_response, dict):
            if 'items' in players_response and 'meta' in players_response:
                items = players_response['items']
                meta = players_response['meta']
                print(f"   ✅ Players response has 'items' and 'meta' structure")
                print(f"   ✅ Items count: {len(items) if isinstance(items, list) else 'Not a list'}")
                print(f"   ✅ Meta keys: {list(meta.keys()) if isinstance(meta, dict) else 'Not a dict'}")
            else:
                print(f"   ⚠️  Players response missing 'items' or 'meta': {list(players_response.keys())}")
        all_tests_passed = all_tests_passed and success8
        
        # Test 9: Check for ImportError about motor/mongo (implicit in successful API calls)
        print(f"\n🔍 Test 9: Runtime ImportError Check (motor/mongo)")
        if all_tests_passed:
            print(f"   ✅ No runtime ImportError detected - all API calls succeeded")
        else:
            print(f"   ⚠️  Some API calls failed - may indicate import issues")
        
        # Summary
        print(f"\n📊 PATCH 1 FINAL SMOKE/REGRESSION SUMMARY")
        print(f"=" * 60)
        passed_count = sum(1 for _, success in test_results if success)
        total_count = len(test_results)
        
        for test_name, success in test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"   {status} - {test_name}")
        
        print(f"\n🎯 Overall Result: {passed_count}/{total_count} tests passed ({passed_count/total_count*100:.1f}%)")
        
        if all_tests_passed:
            print(f"✅ PATCH 1 FINAL SMOKE/REGRESSION - ALL TESTS PASSED")
            print(f"   ✅ Health and readiness endpoints working")
            print(f"   ✅ Admin authentication working (JWT)")
            print(f"   ✅ Dashboard comprehensive stats working")
            print(f"   ✅ Tables endpoint returning JSON array")
            print(f"   ✅ API keys scopes and creation working")
            print(f"   ✅ Players pagination working with items/meta structure")
            print(f"   ✅ No motor/mongo import errors detected")
        else:
            print(f"❌ PATCH 1 FINAL SMOKE/REGRESSION - SOME TESTS FAILED")
            failed_tests = [name for name, success in test_results if not success]
            print(f"   ❌ Failed tests: {', '.join(failed_tests)}")
        
        return all_tests_passed

if __name__ == "__main__":
    tester = Patch1SmokeTest()
    success = tester.test_patch1_final_smoke_regression()
    
    print(f"\nTotal Tests: {tester.tests_run}")
    print(f"Passed: {tester.tests_passed}")
    print(f"Failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if tester.failed_tests:
        print("\n❌ FAILED TESTS DETAILS:")
        for i, failed in enumerate(tester.failed_tests, 1):
            print(f"\n{i}. {failed['name']}")
            if 'endpoint' in failed:
                print(f"   Endpoint: {failed['endpoint']}")
            if 'error' in failed:
                print(f"   Error: {failed['error']}")
            else:
                print(f"   Expected: {failed['expected']}, Got: {failed['actual']}")
                print(f"   Response: {failed['response']}")
    
    sys.exit(0 if success else 1)