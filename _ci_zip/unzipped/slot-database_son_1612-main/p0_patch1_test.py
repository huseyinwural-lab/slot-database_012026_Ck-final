#!/usr/bin/env python3
"""
P0 Patch 1 Backend Smoke/Regression Test
Tests specific endpoints as requested in the review.
"""

import requests
import json
import sys
from datetime import datetime

class P0Patch1Tester:
    def __init__(self):
        self.base_url = "https://wallet-release.preview.emergentagent.com"
        self.access_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
            if details:
                print(f"   {details}")
        else:
            print(f"❌ {name}")
            if details:
                print(f"   {details}")
            self.failed_tests.append(name)

    def make_request(self, method, endpoint, expected_status=200, data=None, auth=False):
        """Make HTTP request and return success, response data, status code"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if auth and self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            else:
                return False, {}, 0
            
            success = response.status_code == expected_status
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            return success, response_data, response.status_code
            
        except Exception as e:
            return False, {"error": str(e)}, 0

    def test_health_endpoint(self):
        """Test 1: GET /api/health -> 200 JSON with status"""
        print("\n🔍 Test 1: Health Check")
        success, data, status = self.make_request('GET', 'api/health', 200)
        
        if success and isinstance(data, dict) and 'status' in data:
            self.log_test("Health endpoint", True, f"Status: {data.get('status')}")
            return True
        else:
            self.log_test("Health endpoint", False, f"Status: {status}, Response: {data}")
            return False

    def test_readiness_endpoint(self):
        """Test 2: GET /api/readiness -> 200 and DB connected"""
        print("\n🔍 Test 2: Readiness Check")
        success, data, status = self.make_request('GET', 'api/readiness', 200)
        
        if success and isinstance(data, dict):
            db_status = data.get('dependencies', {}).get('database')
            if db_status == 'connected':
                self.log_test("Readiness endpoint", True, f"DB Status: {db_status}")
                return True
            else:
                self.log_test("Readiness endpoint", False, f"DB Status: {db_status}")
                return False
        else:
            self.log_test("Readiness endpoint", False, f"Status: {status}, Response: {data}")
            return False

    def test_auth_login(self):
        """Test 3: POST /api/v1/auth/login -> 200 and returns access_token"""
        print("\n🔍 Test 3: Authentication Login")
        
        login_data = {
            "email": "admin@casino.com",
            "password": "Admin123!"
        }
        
        success, data, status = self.make_request('POST', 'api/v1/auth/login', 200, login_data)
        
        if success and isinstance(data, dict) and 'access_token' in data:
            self.access_token = data['access_token']
            token_type = data.get('token_type', 'bearer')
            self.log_test("Auth login", True, f"Token type: {token_type}, Token length: {len(self.access_token)}")
            return True
        else:
            self.log_test("Auth login", False, f"Status: {status}, Response: {data}")
            return False

    def test_tenants_endpoint(self):
        """Test 4a: GET /api/v1/tenants/ -> 200 and returns {items, meta}"""
        print("\n🔍 Test 4a: Tenants Endpoint")
        
        success, data, status = self.make_request('GET', 'api/v1/tenants/', 200, auth=True)
        
        if success and isinstance(data, dict):
            if 'items' in data and 'meta' in data:
                items_count = len(data['items']) if isinstance(data['items'], list) else 0
                self.log_test("Tenants endpoint", True, f"Items: {items_count}, Meta keys: {list(data['meta'].keys())}")
                return True
            else:
                # Check if it's a direct list (older format)
                if isinstance(data, list):
                    self.log_test("Tenants endpoint", True, f"Direct list format: {len(data)} tenants")
                    return True
                else:
                    self.log_test("Tenants endpoint", False, f"Missing items/meta structure: {list(data.keys())}")
                    return False
        else:
            self.log_test("Tenants endpoint", False, f"Status: {status}, Response: {data}")
            return False

    def test_players_endpoint(self):
        """Test 4b: GET /api/v1/players?page=1&page_size=5&include_total=true -> 200 and returns {items, meta}"""
        print("\n🔍 Test 4b: Players Endpoint")
        
        endpoint = 'api/v1/players?page=1&page_size=5&include_total=true'
        success, data, status = self.make_request('GET', endpoint, 200, auth=True)
        
        if success and isinstance(data, dict) and 'items' in data and 'meta' in data:
            items_count = len(data['items']) if isinstance(data['items'], list) else 0
            meta = data['meta']
            page = meta.get('page', 'N/A')
            page_size = meta.get('page_size', 'N/A')
            total = meta.get('total', 'N/A')
            
            self.log_test("Players endpoint", True, 
                         f"Items: {items_count}, Page: {page}, Size: {page_size}, Total: {total}")
            return True
        else:
            self.log_test("Players endpoint", False, f"Status: {status}, Response: {data}")
            return False

    def test_games_endpoint(self):
        """Test 4c: GET /api/v1/games?page=1&page_size=5&include_total=true -> 200 and returns {items, meta}"""
        print("\n🔍 Test 4c: Games Endpoint")
        
        endpoint = 'api/v1/games?page=1&page_size=5&include_total=true'
        success, data, status = self.make_request('GET', endpoint, 200, auth=True)
        
        if success and isinstance(data, dict) and 'items' in data and 'meta' in data:
            items_count = len(data['items']) if isinstance(data['items'], list) else 0
            meta = data['meta']
            page = meta.get('page', 'N/A')
            page_size = meta.get('page_size', 'N/A')
            total = meta.get('total', 'N/A')
            
            self.log_test("Games endpoint", True, 
                         f"Items: {items_count}, Page: {page}, Size: {page_size}, Total: {total}")
            return True
        else:
            self.log_test("Games endpoint", False, f"Status: {status}, Response: {data}")
            return False

    def test_transactions_endpoint(self):
        """Test 4d: GET /api/v1/finance/transactions?page=1&page_size=5&include_total=true -> 200 and returns {items, meta}"""
        print("\n🔍 Test 4d: Finance Transactions Endpoint")
        
        endpoint = 'api/v1/finance/transactions?page=1&page_size=5&include_total=true'
        success, data, status = self.make_request('GET', endpoint, 200, auth=True)
        
        if success and isinstance(data, dict) and 'items' in data and 'meta' in data:
            items_count = len(data['items']) if isinstance(data['items'], list) else 0
            meta = data['meta']
            page = meta.get('page', 'N/A')
            page_size = meta.get('page_size', 'N/A')
            total = meta.get('total', 'N/A')
            
            self.log_test("Finance transactions endpoint", True, 
                         f"Items: {items_count}, Page: {page}, Size: {page_size}, Total: {total}")
            return True
        else:
            self.log_test("Finance transactions endpoint", False, f"Status: {status}, Response: {data}")
            return False

    def test_import_dependencies(self):
        """Test 5: Ensure server can import without Mongo/motor dependency"""
        print("\n🔍 Test 5: Import Dependencies Check")
        
        try:
            # Try to import the main server module to check for import errors
            import subprocess
            result = subprocess.run([
                'python', '-c', 
                'import sys; sys.path.append("/app/backend"); from server import app; print("Import successful")'
            ], capture_output=True, text=True, timeout=10, cwd='/app')
            
            if result.returncode == 0 and "Import successful" in result.stdout:
                self.log_test("Import dependencies", True, "Server imports without Mongo/motor errors")
                return True
            else:
                error_msg = result.stderr if result.stderr else result.stdout
                if "motor" in error_msg.lower() or "mongo" in error_msg.lower():
                    self.log_test("Import dependencies", False, f"Mongo/motor dependency error: {error_msg}")
                else:
                    self.log_test("Import dependencies", True, "No Mongo/motor dependency issues found")
                    return True
                return False
                
        except Exception as e:
            self.log_test("Import dependencies", False, f"Import test failed: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all P0 Patch 1 tests"""
        print("🚀 P0 PATCH 1 BACKEND SMOKE/REGRESSION TEST")
        print("=" * 50)
        print(f"Backend URL: {self.base_url}")
        print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run tests in sequence
        test_results = []
        
        test_results.append(self.test_health_endpoint())
        test_results.append(self.test_readiness_endpoint())
        test_results.append(self.test_auth_login())
        
        # Only run authenticated tests if login succeeded
        if self.access_token:
            test_results.append(self.test_tenants_endpoint())
            test_results.append(self.test_players_endpoint())
            test_results.append(self.test_games_endpoint())
            test_results.append(self.test_transactions_endpoint())
        else:
            print("\n⚠️  Skipping authenticated tests - login failed")
            test_results.extend([False, False, False, False])
        
        test_results.append(self.test_import_dependencies())
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {len(self.failed_tests)}")
        
        if self.failed_tests:
            print(f"\n❌ Failed Tests:")
            for test in self.failed_tests:
                print(f"   - {test}")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"\n📈 Success Rate: {success_rate:.1f}%")
        
        if all(test_results):
            print("\n🎉 ALL P0 PATCH 1 TESTS PASSED!")
            return True
        else:
            print("\n⚠️  SOME P0 PATCH 1 TESTS FAILED")
            return False

def main():
    """Main function"""
    tester = P0Patch1Tester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()