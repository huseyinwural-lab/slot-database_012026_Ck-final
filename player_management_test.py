import requests
import sys
import json
from datetime import datetime

class PlayerManagementTester:
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

    def test_player_list_filters(self):
        """Test Player List with Status, VIP, and Risk filters"""
        print("\n🎯 TESTING PLAYER LIST FILTERS")
        
        # Test Status Filter
        success1, active_players = self.run_test("Players - Status Filter (Active)", "GET", "api/v1/players?status=active", 200)
        success2, suspended_players = self.run_test("Players - Status Filter (Suspended)", "GET", "api/v1/players?status=suspended", 200)
        
        # Test VIP Level Filter
        success3, vip_players = self.run_test("Players - VIP Filter (Level 5)", "GET", "api/v1/players?vip_level=5", 200)
        success4, vip1_players = self.run_test("Players - VIP Filter (Level 1)", "GET", "api/v1/players?vip_level=1", 200)
        
        # Test Risk Score Filter
        success5, high_risk = self.run_test("Players - Risk Filter (High)", "GET", "api/v1/players?risk_score=high", 200)
        success6, low_risk = self.run_test("Players - Risk Filter (Low)", "GET", "api/v1/players?risk_score=low", 200)
        
        # Test Combined Filters
        success7, combined = self.run_test("Players - Combined Filters", "GET", "api/v1/players?status=active&vip_level=5&risk_score=low", 200)
        
        # Validate filter results
        if success1 and isinstance(active_players, list):
            print(f"✅ Active players filter returned {len(active_players)} results")
            if len(active_players) > 0:
                # Check if all returned players have active status
                active_count = sum(1 for p in active_players if p.get('status') == 'active')
                print(f"✅ Filter validation: {active_count}/{len(active_players)} players have active status")
        
        if success3 and isinstance(vip_players, list):
            print(f"✅ VIP Level 5 filter returned {len(vip_players)} results")
            if len(vip_players) > 0:
                vip5_count = sum(1 for p in vip_players if p.get('vip_level') == 5)
                print(f"✅ Filter validation: {vip5_count}/{len(vip_players)} players have VIP level 5")
        
        if success5 and isinstance(high_risk, list):
            print(f"✅ High risk filter returned {len(high_risk)} results")
            if len(high_risk) > 0:
                high_risk_count = sum(1 for p in high_risk if p.get('risk_score') == 'high')
                print(f"✅ Filter validation: {high_risk_count}/{len(high_risk)} players have high risk score")
        
        return success1 and success2 and success3 and success4 and success5 and success6 and success7

    def test_player_detail_tabs(self):
        """Test Player Detail tabs load correctly"""
        print("\n📋 TESTING PLAYER DETAIL TABS")
        
        # First get a player ID
        success, players_response = self.run_test("Get Players for Detail Test", "GET", "api/v1/players", 200)
        if not success or not isinstance(players_response, list) or len(players_response) == 0:
            print("❌ No players found for detail testing")
            return False
        
        player_id = players_response[0].get('id')
        if not player_id:
            print("❌ Player ID not found")
            return False
        
        print(f"Testing with Player ID: {player_id}")
        
        # Test Profile Tab (Player Detail)
        success1, player_detail = self.run_test(f"Profile Tab - Player Detail", "GET", f"api/v1/players/{player_id}", 200)
        
        # Test KYC Tab
        success2, kyc_data = self.run_test(f"KYC Tab - Player KYC", "GET", f"api/v1/players/{player_id}/kyc", 200)
        
        # Test Finance Tab (Transactions)
        success3, transactions = self.run_test(f"Finance Tab - Player Transactions", "GET", f"api/v1/players/{player_id}/transactions", 200)
        
        # Test Logs Tab
        success4, logs = self.run_test(f"Logs Tab - Player Logs", "GET", f"api/v1/players/{player_id}/logs", 200)
        
        # Validate tab data structure
        if success1 and isinstance(player_detail, dict):
            required_fields = ['id', 'username', 'email', 'balance_real', 'balance_bonus', 'status', 'vip_level', 'kyc_status']
            missing_fields = [field for field in required_fields if field not in player_detail]
            if not missing_fields:
                print("✅ Profile tab data structure is complete")
            else:
                print(f"⚠️  Profile tab missing fields: {missing_fields}")
        
        if success2 and isinstance(kyc_data, list):
            print(f"✅ KYC tab returned {len(kyc_data)} documents")
        
        if success3 and isinstance(transactions, list):
            print(f"✅ Finance tab returned {len(transactions)} transactions")
        
        if success4 and isinstance(logs, list):
            print(f"✅ Logs tab returned {len(logs)} login logs")
            if len(logs) > 0:
                log_fields = ['player_id', 'ip_address', 'location', 'device_info', 'status', 'timestamp']
                first_log = logs[0]
                missing_log_fields = [field for field in log_fields if field not in first_log]
                if not missing_log_fields:
                    print("✅ Login log structure is complete")
                else:
                    print(f"⚠️  Login log missing fields: {missing_log_fields}")
        
        return success1 and success2 and success3 and success4

    def test_balance_adjustment_approval(self):
        """Test Balance Adjustment > $1000 triggers approval queue"""
        print("\n💰 TESTING BALANCE ADJUSTMENT APPROVAL LOGIC")
        
        # First get a player ID
        success, players_response = self.run_test("Get Players for Balance Test", "GET", "api/v1/players", 200)
        if not success or not isinstance(players_response, list) or len(players_response) == 0:
            print("❌ No players found for balance testing")
            return False
        
        player_id = players_response[0].get('id')
        if not player_id:
            print("❌ Player ID not found")
            return False
        
        print(f"Testing with Player ID: {player_id}")
        
        # Test small adjustment (should be processed directly)
        small_adjustment = {
            "amount": 500,
            "type": "real",
            "note": "Test small adjustment - should be processed directly"
        }
        success1, small_response = self.run_test("Small Balance Adjustment (<$1000)", "POST", f"api/v1/players/{player_id}/balance", 200, small_adjustment)
        
        if success1 and isinstance(small_response, dict):
            message = small_response.get('message', '')
            if 'Balance updated' in message:
                print("✅ Small adjustment processed directly")
            else:
                print(f"⚠️  Unexpected response for small adjustment: {message}")
        
        # Test large adjustment (should go to approval queue)
        large_adjustment = {
            "amount": 1500,
            "type": "real", 
            "note": "Test large adjustment - should go to approval queue"
        }
        success2, large_response = self.run_test("Large Balance Adjustment (>$1000)", "POST", f"api/v1/players/{player_id}/balance", 200, large_adjustment)
        
        if success2 and isinstance(large_response, dict):
            message = large_response.get('message', '')
            if 'Approval Queue' in message and '$1000' in message:
                print("✅ Large adjustment correctly sent to approval queue")
            else:
                print(f"⚠️  Unexpected response for large adjustment: {message}")
        
        # Test negative large adjustment
        negative_adjustment = {
            "amount": -1200,
            "type": "real",
            "note": "Test negative large adjustment - should go to approval queue"
        }
        success3, negative_response = self.run_test("Negative Large Balance Adjustment", "POST", f"api/v1/players/{player_id}/balance", 200, negative_adjustment)
        
        if success3 and isinstance(negative_response, dict):
            message = negative_response.get('message', '')
            if 'Approval Queue' in message:
                print("✅ Negative large adjustment correctly sent to approval queue")
            else:
                print(f"⚠️  Unexpected response for negative adjustment: {message}")
        
        # Check approval queue to verify requests were added
        success4, approvals = self.run_test("Check Approval Queue", "GET", "api/v1/approvals", 200)
        
        if success4 and isinstance(approvals, list):
            manual_adjustments = [a for a in approvals if a.get('type') == 'manual_adjustment']
            print(f"✅ Found {len(manual_adjustments)} manual adjustment requests in approval queue")
            
            # Show details of recent approval requests
            for approval in manual_adjustments[-2:]:  # Show last 2
                amount = approval.get('amount', 0)
                details = approval.get('details', {})
                note = details.get('note', 'No note')
                print(f"   📋 Approval: ${amount} - {note}")
        
        return success1 and success2 and success3 and success4

    def test_login_logs_display(self):
        """Test Login logs display correctly"""
        print("\n📜 TESTING LOGIN LOGS DISPLAY")
        
        # First get a player ID
        success, players_response = self.run_test("Get Players for Logs Test", "GET", "api/v1/players", 200)
        if not success or not isinstance(players_response, list) or len(players_response) == 0:
            print("❌ No players found for logs testing")
            return False
        
        player_id = players_response[0].get('id')
        if not player_id:
            print("❌ Player ID not found")
            return False
        
        print(f"Testing with Player ID: {player_id}")
        
        # Test login logs endpoint
        success1, logs = self.run_test(f"Player Login Logs", "GET", f"api/v1/players/{player_id}/logs", 200)
        
        if success1 and isinstance(logs, list):
            print(f"✅ Retrieved {len(logs)} login log entries")
            
            if len(logs) > 0:
                # Validate log structure
                first_log = logs[0]
                required_fields = ['player_id', 'ip_address', 'location', 'device_info', 'status', 'timestamp']
                missing_fields = [field for field in required_fields if field not in first_log]
                
                if not missing_fields:
                    print("✅ Login log structure is complete")
                    
                    # Display sample log entries
                    print("📋 Sample log entries:")
                    for i, log in enumerate(logs[:3]):  # Show first 3 logs
                        timestamp = log.get('timestamp', 'Unknown')
                        ip = log.get('ip_address', 'Unknown')
                        location = log.get('location', 'Unknown')
                        device = log.get('device_info', 'Unknown')
                        status = log.get('status', 'Unknown')
                        status_emoji = "✅" if status == 'success' else "❌"
                        
                        print(f"   {i+1}. {status_emoji} {timestamp} | {ip} | {location} | {device}")
                    
                    # Validate data types and formats
                    validation_passed = True
                    for log in logs:
                        if not isinstance(log.get('player_id'), str):
                            print("⚠️  player_id should be string")
                            validation_passed = False
                        if not isinstance(log.get('ip_address'), str):
                            print("⚠️  ip_address should be string")
                            validation_passed = False
                        if log.get('status') not in ['success', 'failed', 'blocked']:
                            print(f"⚠️  Unexpected status value: {log.get('status')}")
                            validation_passed = False
                    
                    if validation_passed:
                        print("✅ All log entries have valid data types and values")
                    
                else:
                    print(f"⚠️  Login log missing required fields: {missing_fields}")
            else:
                print("⚠️  No login logs found (this might be expected for test data)")
        
        return success1

def main():
    print("🎯 Player Management Module Testing")
    print("=" * 50)
    
    tester = PlayerManagementTester()
    
    # Run specific Player Management tests
    test_results = []
    
    test_results.append(("Player List Filters", tester.test_player_list_filters()))
    test_results.append(("Player Detail Tabs", tester.test_player_detail_tabs()))
    test_results.append(("Balance Adjustment Approval", tester.test_balance_adjustment_approval()))
    test_results.append(("Login Logs Display", tester.test_login_logs_display()))
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 PLAYER MANAGEMENT TEST SUMMARY")
    print("=" * 50)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<30} {status}")
    
    print(f"\nTotal Tests: {tester.tests_run}")
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
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())