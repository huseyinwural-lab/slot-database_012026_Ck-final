#!/usr/bin/env python3
"""
Review Request Test Suite

This test suite validates the specific requirements from the review request:
1) Call GET http://localhost:8001/api/ready and confirm alembic.head==20260102_04.
2) Call POST http://localhost:8001/api/v1/ci/seed twice and confirm both return 200.
3) Call player register/login then GET /api/v1/player/client-games/ with player token and confirm classic777 exists.

Report the exact outputs.
"""

import asyncio
import json
import uuid
from typing import Dict, Any
import httpx

# Use localhost:8001 as specified in the review request
BACKEND_URL = "http://localhost:8001"

class ReviewRequestTestSuite:
    def __init__(self):
        self.base_url = f"{BACKEND_URL}/api"
        self.api_v1_url = f"{BACKEND_URL}/api/v1"
        self.player_token = None
        self.test_player_email = None
        self.test_player_password = None
        self.test_results = []
        
    def log_result(self, test_name: str, success: bool, details: str = "", exact_output: str = ""):
        """Log test result with exact output"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "exact_output": exact_output
        })
        print(f"{status}: {test_name}")
        if details:
            print(f"    {details}")
        if exact_output:
            print(f"    EXACT OUTPUT: {exact_output}")
    
    async def test_ready_endpoint_alembic_head(self) -> bool:
        """Test 1: Call GET http://localhost:8001/api/ready and confirm alembic.head==20260102_04"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.base_url}/ready")
                
                exact_output = f"Status: {response.status_code}, Response: {response.text}"
                
                if response.status_code != 200:
                    self.log_result("GET /api/ready", False, 
                                  f"Expected status 200, got {response.status_code}", exact_output)
                    return False
                
                data = response.json()
                alembic_info = data.get("alembic", {})
                head = alembic_info.get("head")
                
                if head != "20260102_04":
                    self.log_result("GET /api/ready", False, 
                                  f"Expected alembic.head==20260102_04, got {head}", exact_output)
                    return False
                
                self.log_result("GET /api/ready", True, 
                              f"✅ Confirmed alembic.head==20260102_04", exact_output)
                return True
                
        except Exception as e:
            exact_output = f"Exception: {str(e)}"
            self.log_result("GET /api/ready", False, f"Exception occurred", exact_output)
            return False
    
    async def test_ci_seed_first_call(self) -> bool:
        """Test 2a: Call POST http://localhost:8001/api/v1/ci/seed (first time) and confirm returns 200"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(f"{self.api_v1_url}/ci/seed")
                
                exact_output = f"Status: {response.status_code}, Response: {response.text}"
                
                if response.status_code != 200:
                    self.log_result("POST /api/v1/ci/seed (First Call)", False, 
                                  f"Expected status 200, got {response.status_code}", exact_output)
                    return False
                
                self.log_result("POST /api/v1/ci/seed (First Call)", True, 
                              f"✅ First call returned 200", exact_output)
                return True
                
        except Exception as e:
            exact_output = f"Exception: {str(e)}"
            self.log_result("POST /api/v1/ci/seed (First Call)", False, f"Exception occurred", exact_output)
            return False
    
    async def test_ci_seed_second_call(self) -> bool:
        """Test 2b: Call POST http://localhost:8001/api/v1/ci/seed (second time) and confirm returns 200"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(f"{self.api_v1_url}/ci/seed")
                
                exact_output = f"Status: {response.status_code}, Response: {response.text}"
                
                if response.status_code != 200:
                    self.log_result("POST /api/v1/ci/seed (Second Call)", False, 
                                  f"Expected status 200, got {response.status_code}", exact_output)
                    return False
                
                self.log_result("POST /api/v1/ci/seed (Second Call)", True, 
                              f"✅ Second call returned 200", exact_output)
                return True
                
        except Exception as e:
            exact_output = f"Exception: {str(e)}"
            self.log_result("POST /api/v1/ci/seed (Second Call)", False, f"Exception occurred", exact_output)
            return False
    
    async def test_player_register_and_login(self) -> bool:
        """Test 3a: Register and login player to get token for client-games endpoint"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Generate unique player credentials
                self.test_player_email = f"reviewtest_{uuid.uuid4().hex[:8]}@casino.com"
                self.test_player_password = "ReviewTestPlayer123!"
                
                player_data = {
                    "email": self.test_player_email,
                    "username": f"reviewtest_{uuid.uuid4().hex[:8]}",
                    "password": self.test_player_password,
                    "tenant_id": "default_casino"
                }
                
                # Register player
                response = await client.post(
                    f"{self.api_v1_url}/auth/player/register",
                    json=player_data
                )
                
                register_output = f"Register Status: {response.status_code}, Response: {response.text}"
                
                if response.status_code != 200:
                    self.log_result("Player Register", False, 
                                  f"Registration failed with status {response.status_code}", register_output)
                    return False
                
                # Login player
                player_login_data = {
                    "email": self.test_player_email,
                    "password": self.test_player_password,
                    "tenant_id": "default_casino"
                }
                
                response = await client.post(
                    f"{self.api_v1_url}/auth/player/login",
                    json=player_login_data
                )
                
                login_output = f"Login Status: {response.status_code}, Response: {response.text}"
                exact_output = f"{register_output} | {login_output}"
                
                if response.status_code != 200:
                    self.log_result("Player Register and Login", False, 
                                  f"Login failed with status {response.status_code}", exact_output)
                    return False
                
                player_data = response.json()
                self.player_token = player_data.get("access_token")
                if not self.player_token:
                    self.log_result("Player Register and Login", False, 
                                  "No player access token in response", exact_output)
                    return False
                
                self.log_result("Player Register and Login", True, 
                              f"✅ Player registered and logged in successfully", exact_output)
                return True
                
        except Exception as e:
            exact_output = f"Exception: {str(e)}"
            self.log_result("Player Register and Login", False, f"Exception occurred", exact_output)
            return False
    
    async def test_client_games_classic777(self) -> bool:
        """Test 3b: Call GET /api/v1/player/client-games/ with player token and confirm classic777 exists"""
        try:
            if not self.player_token:
                self.log_result("GET /api/v1/player/client-games/", False, 
                              "No player token available", "No token available")
                return False
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {self.player_token}"}
                
                response = await client.get(
                    f"{self.api_v1_url}/player/client-games/",
                    headers=headers
                )
                
                exact_output = f"Status: {response.status_code}, Response: {response.text}"
                
                if response.status_code != 200:
                    self.log_result("GET /api/v1/player/client-games/", False, 
                                  f"Expected status 200, got {response.status_code}", exact_output)
                    return False
                
                data = response.json()
                
                # Look for classic777 in the response
                classic777_found = False
                classic777_details = ""
                
                if isinstance(data, list):
                    # If response is a list of games
                    for game in data:
                        if isinstance(game, dict):
                            external_id = game.get("external_id")
                            name = game.get("name", "")
                            if external_id == "classic777" or "classic777" in name.lower():
                                classic777_found = True
                                classic777_details = f"Found game: {game}"
                                break
                elif isinstance(data, dict):
                    # If response is an object with games array
                    games = data.get("games", []) or data.get("items", []) or data.get("data", [])
                    for game in games:
                        if isinstance(game, dict):
                            external_id = game.get("external_id")
                            name = game.get("name", "")
                            if external_id == "classic777" or "classic777" in name.lower():
                                classic777_found = True
                                classic777_details = f"Found game: {game}"
                                break
                
                if not classic777_found:
                    self.log_result("GET /api/v1/player/client-games/", False, 
                                  "classic777 game not found in response", exact_output)
                    return False
                
                self.log_result("GET /api/v1/player/client-games/", True, 
                              f"✅ Confirmed classic777 exists - {classic777_details}", exact_output)
                return True
                
        except Exception as e:
            exact_output = f"Exception: {str(e)}"
            self.log_result("GET /api/v1/player/client-games/", False, f"Exception occurred", exact_output)
            return False
    
    async def run_all_tests(self):
        """Run the complete review request test suite"""
        print("🚀 Starting Review Request Test Suite...")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 80)
        
        # Run all tests in sequence
        test_results = []
        
        # Test 1: GET /api/ready and confirm alembic.head==20260102_04
        test_results.append(await self.test_ready_endpoint_alembic_head())
        
        # Test 2a: POST /api/v1/ci/seed (first call)
        test_results.append(await self.test_ci_seed_first_call())
        
        # Test 2b: POST /api/v1/ci/seed (second call)
        test_results.append(await self.test_ci_seed_second_call())
        
        # Test 3a: Player register and login
        test_results.append(await self.test_player_register_and_login())
        
        # Test 3b: GET /api/v1/player/client-games/ and confirm classic777
        test_results.append(await self.test_client_games_classic777())
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 REVIEW REQUEST TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(test_results)
        total = len(test_results)
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"]:
                print(f"    {result['details']}")
            if result["exact_output"]:
                print(f"    EXACT OUTPUT: {result['exact_output']}")
            print()
        
        print(f"\n🎯 OVERALL RESULT: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 All review request tests PASSED!")
            return True
        else:
            print(f"⚠️  {total - passed} test(s) failed. Review the details above.")
            return False

async def main():
    """Main function to run the review request test suite"""
    suite = ReviewRequestTestSuite()
    success = await suite.run_all_tests()
    return success

if __name__ == "__main__":
    asyncio.run(main())