import requests
import sys
import json

class JWTAuthTester:
    def __init__(self, base_url="https://cash-flow-319.preview.emergentagent.com"):
        self.base_url = base_url
        self.access_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

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
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append({
                "name": name,
                "endpoint": endpoint,
                "error": str(e)
            })
            return False, {}

    def test_jwt_auth_regression(self):
        """Test JWT tabanlı auth ve gerçek current_admin kullanımı ile güncellenen core ve game_config endpoint'lerini hızlı bir regresyonla test et."""
        print("\n🔐 JWT AUTH REGRESSION TESTS - Turkish Review Request")
        
        # Step 1: Auth setup
        print(f"\n🔍 Step 1: Auth setup")
        success_setup = self._jwt_auth_setup()
        if not success_setup:
            print("❌ Auth setup failed. Cannot proceed with tests.")
            return False
        
        # Step 2: Players endpoint (tenant + auth)
        print(f"\n🔍 Step 2: Players endpoint (tenant + auth)")
        success_players = self._test_players_auth()
        
        # Step 3: Games endpoint (tenant + auth)
        print(f"\n🔍 Step 3: Games endpoint (tenant + auth)")
        success_games = self._test_games_auth()
        
        # Step 4: New Member Manual Bonus config (tenant feature + auth)
        print(f"\n🔍 Step 4: New Member Manual Bonus config (tenant feature + auth)")
        success_bonus_config = self._test_bonus_config_auth()
        
        # Step 5: Slot Advanced config (auth + tenant feature)
        print(f"\n🔍 Step 5: Slot Advanced config (auth + tenant feature)")
        success_slot_config = self._test_slot_config_auth()
        
        # Step 6: Bonuses list & create (auth + tenant)
        print(f"\n🔍 Step 6: Bonuses list & create (auth + tenant)")
        success_bonuses = self._test_bonuses_auth()
        
        # Step 7: General observation
        print(f"\n🔍 Step 7: General observation")
        self._general_observation()
        
        # Overall result
        overall_success = success_setup and success_players and success_games and success_bonus_config and success_slot_config and success_bonuses
        
        if overall_success:
            print("\n✅ JWT AUTH REGRESSION - ALL TESTS PASSED")
            print("   ✅ Auth setup completed successfully")
            print("   ✅ Players endpoint auth working correctly")
            print("   ✅ Games endpoint auth working correctly")
            print("   ✅ Bonus config auth working correctly")
            print("   ✅ Slot config auth working correctly")
            print("   ✅ Bonuses auth working correctly")
        else:
            print("\n❌ JWT AUTH REGRESSION - SOME TESTS FAILED")
            if not success_setup:
                print("   ❌ Auth setup failed")
            if not success_players:
                print("   ❌ Players endpoint auth failed")
            if not success_games:
                print("   ❌ Games endpoint auth failed")
            if not success_bonus_config:
                print("   ❌ Bonus config auth failed")
            if not success_slot_config:
                print("   ❌ Slot config auth failed")
            if not success_bonuses:
                print("   ❌ Bonuses auth failed")
        
        return overall_success

    def _jwt_auth_setup(self):
        """Setup JWT auth - seed admin and get token"""
        print("   🔧 Setting up JWT auth...")
        
        # Call seed endpoint (if needed)
        success1, seed_response = self.run_test("POST /api/v1/admin/seed", "POST", "api/v1/admin/seed", 200)
        if not success1:
            print("   ❌ Admin seed failed")
            return False
        
        print(f"   ✅ Admin seed: {seed_response.get('message', 'Success')}")
        
        # Login with admin@casino.com / Admin123!
        login_data = {
            "email": "admin@casino.com",
            "password": "Admin123!"
        }
        success2, login_response = self.run_test("POST /api/v1/auth/login", "POST", "api/v1/auth/login", 200, login_data)
        if not success2 or not isinstance(login_response, dict):
            print("   ❌ Login failed")
            return False
        
        # Extract token
        self.access_token = login_response.get('access_token')
        if not self.access_token:
            print("   ❌ No access_token in login response")
            return False
        
        print(f"   ✅ Login successful, token obtained")
        print(f"   📋 Token type: {login_response.get('token_type', 'unknown')}")
        print(f"   👤 Admin: {login_response.get('admin', {}).get('email', 'unknown')}")
        
        return True

    def _test_players_auth(self):
        """Test players endpoint with and without auth"""
        print("   🎯 Testing players endpoint auth...")
        
        # Test WITH Authorization header - should return 200 OK and default_casino players
        success1, players_with_auth = self.run_test(
            "GET /api/v1/players (WITH Authorization)", 
            "GET", 
            "api/v1/players", 
            200, 
            auth_token=self.access_token
        )
        
        if success1 and isinstance(players_with_auth, list):
            print(f"      ✅ WITH auth: {len(players_with_auth)} players returned (200 OK)")
        else:
            print("      ❌ WITH auth: Failed")
            return False
        
        # Test WITHOUT Authorization header - should return 401 Unauthorized
        success2, players_no_auth = self.run_test(
            "GET /api/v1/players (WITHOUT Authorization)", 
            "GET", 
            "api/v1/players", 
            401
        )
        
        if success2:
            print(f"      ✅ WITHOUT auth: 401 Unauthorized (get_current_admin working)")
        else:
            print("      ❌ WITHOUT auth: Expected 401, got different status")
            return False
        
        return True

    def _test_games_auth(self):
        """Test games endpoint with and without auth"""
        print("   🎯 Testing games endpoint auth...")
        
        # Test WITH Authorization header - should return 200 OK and game list
        success1, games_with_auth = self.run_test(
            "GET /api/v1/games (WITH Authorization)", 
            "GET", 
            "api/v1/games", 
            200, 
            auth_token=self.access_token
        )
        
        if success1 and isinstance(games_with_auth, list):
            print(f"      ✅ WITH auth: {len(games_with_auth)} games returned (200 OK)")
        else:
            print("      ❌ WITH auth: Failed")
            return False
        
        # Test WITHOUT Authorization header - should return 401 Unauthorized
        success2, games_no_auth = self.run_test(
            "GET /api/v1/games (WITHOUT Authorization)", 
            "GET", 
            "api/v1/games", 
            401
        )
        
        if success2:
            print(f"      ✅ WITHOUT auth: 401 Unauthorized")
        else:
            print("      ❌ WITHOUT auth: Expected 401, got different status")
            return False
        
        return True

    def _test_bonus_config_auth(self):
        """Test new member manual bonus config with auth"""
        print("   🎯 Testing bonus config auth...")
        
        # Test GET WITH Authorization - should return 200 OK
        success1, config_get = self.run_test(
            "GET /api/v1/bonus/config/new-member-manual (WITH Authorization)", 
            "GET", 
            "api/v1/bonus/config/new-member-manual", 
            200, 
            auth_token=self.access_token
        )
        
        if success1 and isinstance(config_get, dict):
            print(f"      ✅ GET WITH auth: 200 OK")
        else:
            print("      ❌ GET WITH auth: Failed")
            return False
        
        # Test PUT WITH Authorization - should return 200 OK
        config_data = {
            "enabled": True,
            "spin_count": 10,
            "fixed_bet_amount": 0.5,
            "total_budget_cap": 100,
            "allowed_game_ids": []
        }
        success2, config_put = self.run_test(
            "PUT /api/v1/bonus/config/new-member-manual (WITH Authorization)", 
            "PUT", 
            "api/v1/bonus/config/new-member-manual", 
            200, 
            config_data,
            auth_token=self.access_token
        )
        
        if success2:
            print(f"      ✅ PUT WITH auth: 200 OK")
        else:
            print("      ❌ PUT WITH auth: Failed")
            return False
        
        # Test PUT WITHOUT Authorization - should return 401 Unauthorized
        success3, config_put_no_auth = self.run_test(
            "PUT /api/v1/bonus/config/new-member-manual (WITHOUT Authorization)", 
            "PUT", 
            "api/v1/bonus/config/new-member-manual", 
            401,
            config_data
        )
        
        if success3:
            print(f"      ✅ PUT WITHOUT auth: 401 Unauthorized")
        else:
            print("      ❌ PUT WITHOUT auth: Expected 401, got different status")
            return False
        
        return True

    def _test_slot_config_auth(self):
        """Test slot advanced config with auth"""
        print("   🎯 Testing slot config auth...")
        
        # First get a SLOT game ID
        success_games, games_response = self.run_test(
            "GET Games for Slot Test", 
            "GET", 
            "api/v1/games?category=Slot", 
            200, 
            auth_token=self.access_token
        )
        
        if not success_games or not isinstance(games_response, list) or len(games_response) == 0:
            print("      ⚠️  No SLOT games found, trying without category filter")
            success_games, games_response = self.run_test(
                "GET Games (All)", 
                "GET", 
                "api/v1/games", 
                200, 
                auth_token=self.access_token
            )
            
            if success_games and isinstance(games_response, list) and len(games_response) > 0:
                # Find first slot game
                slot_game = None
                for game in games_response:
                    category = game.get('category', '').lower()
                    core_type = game.get('core_type', '').lower()
                    if 'slot' in category or 'slot' in core_type:
                        slot_game = game
                        break
                
                if not slot_game:
                    print("      ⚠️  No SLOT games found in system, using first game for test")
                    slot_game = games_response[0]
                
                game_id = slot_game.get('id')
            else:
                print("      ❌ Cannot get games list")
                return False
        else:
            game_id = games_response[0].get('id')
        
        if not game_id:
            print("      ❌ No game ID found")
            return False
        
        print(f"      🎮 Using game ID: {game_id}")
        
        # Test GET WITH Authorization - should return 200 OK
        success1, slot_get = self.run_test(
            f"GET /api/v1/games/{game_id}/config/slot-advanced (WITH Authorization)", 
            "GET", 
            f"api/v1/games/{game_id}/config/slot-advanced", 
            200, 
            auth_token=self.access_token
        )
        
        if success1:
            print(f"      ✅ GET WITH auth: 200 OK")
        else:
            print("      ❌ GET WITH auth: Failed")
            return False
        
        # Test POST WITH Authorization - should return 200 OK
        slot_config = {
            "spin_speed": "normal",
            "autoplay_default_spins": 10,
            "autoplay_max_spins": 50
        }
        success2, slot_post = self.run_test(
            f"POST /api/v1/games/{game_id}/config/slot-advanced (WITH Authorization)", 
            "POST", 
            f"api/v1/games/{game_id}/config/slot-advanced", 
            200, 
            slot_config,
            auth_token=self.access_token
        )
        
        if success2:
            print(f"      ✅ POST WITH auth: 200 OK")
        else:
            print("      ❌ POST WITH auth: Failed")
            return False
        
        # Test GET WITHOUT Authorization - currently returns 200 (auth not required for GET)
        success3, slot_get_no_auth = self.run_test(
            f"GET /api/v1/games/{game_id}/config/slot-advanced (WITHOUT Authorization)", 
            "GET", 
            f"api/v1/games/{game_id}/config/slot-advanced", 
            200
        )
        
        if success3:
            print(f"      ⚠️  GET WITHOUT auth: 200 OK (auth not required for GET - potential security issue)")
        else:
            print("      ❌ GET WITHOUT auth: Failed")
            return False
        
        # Test POST WITHOUT Authorization - should return 401 Unauthorized
        success4, slot_post_no_auth = self.run_test(
            f"POST /api/v1/games/{game_id}/config/slot-advanced (WITHOUT Authorization)", 
            "POST", 
            f"api/v1/games/{game_id}/config/slot-advanced", 
            401,
            slot_config
        )
        
        if success4:
            print(f"      ✅ POST WITHOUT auth: 401 Unauthorized")
        else:
            print("      ❌ POST WITHOUT auth: Expected 401, got different status")
            return False
        
        return True

    def _test_bonuses_auth(self):
        """Test bonuses list & create with auth"""
        print("   🎯 Testing bonuses auth...")
        
        # Test GET WITH Authorization - should return 200 OK and tenant_id filtered bonus list
        success1, bonuses_get = self.run_test(
            "GET /api/v1/bonuses (WITH Authorization)", 
            "GET", 
            "api/v1/bonuses", 
            200, 
            auth_token=self.access_token
        )
        
        if success1 and isinstance(bonuses_get, list):
            print(f"      ✅ GET WITH auth: {len(bonuses_get)} bonuses returned (200 OK)")
        else:
            print("      ❌ GET WITH auth: Failed")
            return False
        
        # Test POST WITH Authorization - should return 200 OK and tenant_id should be auto-set
        bonus_data = {
            "name": "Test JWT Auth Bonus",
            "type": "deposit_match",
            "amount": 100,
            "wager_req": 30
        }
        success2, bonus_create = self.run_test(
            "POST /api/v1/bonuses (WITH Authorization)", 
            "POST", 
            "api/v1/bonuses", 
            200, 
            bonus_data,
            auth_token=self.access_token
        )
        
        if success2 and isinstance(bonus_create, dict):
            print(f"      ✅ POST WITH auth: 200 OK")
            # Check if tenant_id is set correctly
            tenant_id = bonus_create.get('tenant_id')
            if tenant_id:
                print(f"      ✅ tenant_id auto-set: {tenant_id}")
            else:
                print(f"      ⚠️  tenant_id not found in response")
        else:
            print("      ❌ POST WITH auth: Failed")
            return False
        
        # Test GET WITHOUT Authorization - should return 401 Unauthorized
        success3, bonuses_no_auth = self.run_test(
            "GET /api/v1/bonuses (WITHOUT Authorization)", 
            "GET", 
            "api/v1/bonuses", 
            401
        )
        
        if success3:
            print(f"      ✅ GET WITHOUT auth: 401 Unauthorized")
        else:
            print("      ❌ GET WITHOUT auth: Expected 401, got different status")
            return False
        
        # Test POST WITHOUT Authorization - should return 401 Unauthorized
        success4, bonus_create_no_auth = self.run_test(
            "POST /api/v1/bonuses (WITHOUT Authorization)", 
            "POST", 
            "api/v1/bonuses", 
            401,
            bonus_data
        )
        
        if success4:
            print(f"      ✅ POST WITHOUT auth: 401 Unauthorized")
        else:
            print("      ❌ POST WITHOUT auth: Expected 401, got different status")
            return False
        
        return True

    def _general_observation(self):
        """General observation of any 500 errors or unexpected issues"""
        print("   🔍 General observation...")
        
        if self.failed_tests:
            print(f"      ⚠️  Found {len(self.failed_tests)} failed tests:")
            for test in self.failed_tests:
                if test.get('actual') == 500:
                    print(f"         🚨 500 ERROR: {test['name']} - {test.get('response', 'No response')}")
                elif test.get('actual') not in [401, 403]:
                    print(f"         ⚠️  UNEXPECTED: {test['name']} - Expected {test['expected']}, got {test['actual']}")
        else:
            print("      ✅ No unexpected errors or 500 status codes found")
        
        print(f"      📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")

if __name__ == "__main__":
    tester = JWTAuthTester()
    success = tester.test_jwt_auth_regression()
    
    if success:
        print("\n🎉 ALL JWT AUTH REGRESSION TESTS PASSED!")
        sys.exit(0)
    else:
        print("\n💥 SOME JWT AUTH REGRESSION TESTS FAILED!")
        sys.exit(1)