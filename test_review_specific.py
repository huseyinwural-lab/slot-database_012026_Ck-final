#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class ReviewRequestTester:
    def __init__(self, base_url="https://pspreconcile.preview.emergentagent.com"):
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

    def test_review_request_specific(self):
        """Test specific endpoints mentioned in the review request"""
        print("\n🎯 REVIEW REQUEST SPECIFIC TESTS")
        
        # 1. AI Risk Analysis: POST /api/v1/finance/transactions/tx2/analyze-risk
        print("\n🤖 Testing AI Risk Analysis Endpoint")
        success1, risk_response = self.run_test("AI Risk Analysis - tx2", "POST", "api/v1/finance/transactions/tx2/analyze-risk", 200)
        
        risk_analysis_valid = True
        if success1 and isinstance(risk_response, dict):
            print("🔍 VALIDATING AI RISK ANALYSIS RESPONSE")
            
            # Check for risk_score
            if 'risk_score' in risk_response:
                risk_score = risk_response['risk_score']
                print(f"   ✅ risk_score: {risk_score}")
                if not isinstance(risk_score, (int, float)) or risk_score < 0 or risk_score > 100:
                    print(f"   ❌ Invalid risk_score value: {risk_score} (should be 0-100)")
                    risk_analysis_valid = False
            else:
                print(f"   ❌ MISSING: risk_score")
                risk_analysis_valid = False
            
            # Check for risk_level
            if 'risk_level' in risk_response:
                risk_level = risk_response['risk_level']
                print(f"   ✅ risk_level: {risk_level}")
                valid_levels = ['low', 'medium', 'high', 'critical', 'unknown']
                if risk_level not in valid_levels:
                    print(f"   ⚠️  Unexpected risk_level: {risk_level}")
            else:
                print(f"   ❌ MISSING: risk_level")
                risk_analysis_valid = False
            
            # Check for reason
            if 'reason' in risk_response:
                reason = risk_response['reason']
                print(f"   ✅ reason: {reason[:50]}...")
            else:
                print(f"   ❌ MISSING: reason")
                risk_analysis_valid = False
                
            # Optional fields validation
            optional_fields = ['flags', 'recommendation', 'details', 'error']
            for field in optional_fields:
                if field in risk_response:
                    print(f"   ✅ {field}: {risk_response[field]}")
        else:
            print("❌ Failed to get valid AI risk analysis response")
            risk_analysis_valid = False
        
        # 2. Game Management: GET /api/v1/games
        print("\n🎮 Testing Game Management Endpoint")
        success2, games_response = self.run_test("Game Management - Get Games", "GET", "api/v1/games", 200)
        
        games_valid = True
        if success2 and isinstance(games_response, list):
            print(f"✅ Games endpoint returned {len(games_response)} games")
            
            if len(games_response) > 0:
                game = games_response[0]
                required_game_fields = ['id', 'name', 'provider', 'category']
                missing_game_fields = [field for field in required_game_fields if field not in game]
                
                if not missing_game_fields:
                    print(f"✅ Game structure complete: {game['name']} by {game['provider']}")
                    print(f"   📂 Category: {game['category']}")
                    print(f"   🆔 ID: {game['id']}")
                else:
                    print(f"⚠️  Game missing fields: {missing_game_fields}")
                    games_valid = False
            else:
                print("⚠️  No games found in response")
        else:
            print("❌ Failed to get valid games list response")
            games_valid = False
        
        # 3. Geo Rules: PUT /api/v1/games/{game_id}/details with countries_allowed
        print("\n🌍 Testing Geo Rules Update")
        geo_rules_valid = True
        
        if success2 and isinstance(games_response, list) and len(games_response) > 0:
            game_id = games_response[0]['id']
            geo_update_data = {
                "countries_allowed": ["TR", "DE"]
            }
            
            success3, geo_response = self.run_test(f"Geo Rules Update - {game_id}", "PUT", f"api/v1/games/{game_id}/details", 200, geo_update_data)
            
            if success3 and isinstance(geo_response, dict):
                if 'message' in geo_response:
                    print(f"✅ Geo rules update successful: {geo_response['message']}")
                    
                    # Verify the update by fetching the game again
                    success4, updated_games = self.run_test("Verify Geo Rules Update", "GET", "api/v1/games", 200)
                    if success4 and isinstance(updated_games, list):
                        updated_game = next((g for g in updated_games if g.get('id') == game_id), None)
                        if updated_game and 'countries_allowed' in updated_game:
                            countries = updated_game['countries_allowed']
                            if countries == ["TR", "DE"]:
                                print(f"✅ Geo rules successfully updated: {countries}")
                            else:
                                print(f"⚠️  Geo rules may not have been updated correctly: {countries}")
                        else:
                            print("⚠️  Updated game not found or missing countries_allowed field")
                else:
                    print("⚠️  Geo rules update response missing message field")
                    geo_rules_valid = False
            else:
                print("❌ Failed to update geo rules")
                geo_rules_valid = False
        else:
            print("❌ Cannot test geo rules - no games available")
            geo_rules_valid = False
        
        print(f"\n📊 REVIEW REQUEST TEST SUMMARY:")
        print(f"   🤖 AI Risk Analysis: {'✅ PASS' if success1 and risk_analysis_valid else '❌ FAIL'}")
        print(f"   🎮 Game Management: {'✅ PASS' if success2 and games_valid else '❌ FAIL'}")
        print(f"   🌍 Geo Rules Update: {'✅ PASS' if geo_rules_valid else '❌ FAIL'}")
        
        return success1 and risk_analysis_valid and success2 and games_valid and geo_rules_valid

if __name__ == "__main__":
    tester = ReviewRequestTester()
    
    print("🎯 REVIEW REQUEST SPECIFIC TESTING")
    print("=" * 50)
    
    result = tester.test_review_request_specific()
    
    print(f"\n{'='*50}")
    print(f"🏁 FINAL SUMMARY")
    print(f"{'='*50}")
    print(f"✅ Tests Passed: {tester.tests_passed}/{tester.tests_run}")
    print(f"❌ Tests Failed: {len(tester.failed_tests)}")
    
    if tester.failed_tests:
        print(f"\n💥 FAILED TESTS:")
        for i, failure in enumerate(tester.failed_tests, 1):
            print(f"{i}. {failure['name']}")
            if 'error' in failure:
                print(f"   Error: {failure['error']}")
            else:
                print(f"   Expected: {failure['expected']}, Got: {failure['actual']}")
                print(f"   Response: {failure['response']}")
    
    success_rate = (tester.tests_passed / tester.tests_run) * 100 if tester.tests_run > 0 else 0
    print(f"\n🎯 Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("🎉 Overall Status: GOOD")
    elif success_rate >= 60:
        print("⚠️  Overall Status: NEEDS ATTENTION")
    else:
        print("🚨 Overall Status: CRITICAL ISSUES")
    
    sys.exit(0 if result else 1)