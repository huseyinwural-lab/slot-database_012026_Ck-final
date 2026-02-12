#!/usr/bin/env python3
"""
Risk Sprint 2 Test Suite

This test suite validates:
1. Risk Sprint 2 pytest tests pass
2. risk_history table exists
3. Risk admin API endpoints are reachable

Tests are designed to run against the configured backend service.
"""

import asyncio
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Tuple
import httpx
import os
import uuid
import subprocess
import re

# Use external ingress base URL from REACT_APP_BACKEND_URL as specified in the review request
def get_backend_url():
    try:
        with open("/app/frontend/.env", "r") as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    return line.split("=", 1)[1].strip()
    except Exception:
        pass
    return "https://deal-maker-6.preview.emergentagent.com"  # fallback

BACKEND_URL = get_backend_url()

class RiskSprint2TestSuite:
    def __init__(self):
        self.base_url = f"{BACKEND_URL}/api/v1"
        self.admin_token = None
        self.test_results = []
        
    def log_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        print(f"{status}: {test_name}")
        if details:
            print(f"    {details}")
    
    async def setup_auth(self) -> bool:
        """Setup admin authentication"""
        try:
            # Login as admin
            async with httpx.AsyncClient(timeout=30.0) as client:
                login_data = {
                    "email": "admin@casino.com",
                    "password": "Admin123!"
                }
                
                response = await client.post(
                    f"{self.base_url}/auth/login",
                    json=login_data
                )
                
                if response.status_code != 200:
                    self.log_result("Admin Login", False, f"Status: {response.status_code}, Response: {response.text}")
                    return False
                
                data = response.json()
                self.admin_token = data.get("access_token")
                if not self.admin_token:
                    self.log_result("Admin Login", False, "No access token in response")
                    return False
                
                self.log_result("Admin Login", True, f"Token length: {len(self.admin_token)}")
                return True
                
        except Exception as e:
            self.log_result("Admin Login", False, f"Exception: {str(e)}")
            return False
    
    def test_pytest_bet_throttle(self) -> bool:
        """Test 1: Run pytest backend/tests/risk/test_bet_throttle.py"""
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "tests/risk/test_bet_throttle.py", "-v"],
                cwd="/app/backend",
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                # Count passed tests
                passed_count = result.stdout.count(" PASSED")
                self.log_result("Pytest Bet Throttle", True, f"{passed_count} tests passed")
                return True
            else:
                self.log_result("Pytest Bet Throttle", False, f"Exit code: {result.returncode}, stderr: {result.stderr}")
                return False
                
        except Exception as e:
            self.log_result("Pytest Bet Throttle", False, f"Exception: {str(e)}")
            return False
    
    def test_pytest_bet_throttling_integration(self) -> bool:
        """Test 2: Run pytest backend/tests/risk/test_bet_throttling_integration.py"""
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "tests/risk/test_bet_throttling_integration.py", "-v"],
                cwd="/app/backend",
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                # Count passed tests
                passed_count = result.stdout.count(" PASSED")
                self.log_result("Pytest Bet Throttling Integration", True, f"{passed_count} tests passed")
                return True
            else:
                self.log_result("Pytest Bet Throttling Integration", False, f"Exit code: {result.returncode}, stderr: {result.stderr}")
                return False
                
        except Exception as e:
            self.log_result("Pytest Bet Throttling Integration", False, f"Exception: {str(e)}")
            return False
    
    def test_pytest_admin_risk_dashboard_api(self) -> bool:
        """Test 3: Run pytest backend/tests/risk/test_admin_risk_dashboard_api.py"""
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "tests/risk/test_admin_risk_dashboard_api.py", "-v"],
                cwd="/app/backend",
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                # Count passed tests
                passed_count = result.stdout.count(" PASSED")
                self.log_result("Pytest Admin Risk Dashboard API", True, f"{passed_count} tests passed")
                return True
            else:
                self.log_result("Pytest Admin Risk Dashboard API", False, f"Exit code: {result.returncode}, stderr: {result.stderr}")
                return False
                
        except Exception as e:
            self.log_result("Pytest Admin Risk Dashboard API", False, f"Exception: {str(e)}")
            return False
    
    def test_risk_history_table_exists(self) -> bool:
        """Test 4: Verify that risk_history table exists"""
        try:
            import sqlite3
            conn = sqlite3.connect('/app/backend/casino.db')
            cursor = conn.cursor()
            
            # Check if risk_history table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='risk_history';")
            risk_history_exists = cursor.fetchone()
            
            if not risk_history_exists:
                self.log_result("Risk History Table Exists", False, "risk_history table not found")
                conn.close()
                return False
            
            # Check table schema
            cursor.execute('PRAGMA table_info(risk_history);')
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            required_columns = ['id', 'user_id', 'tenant_id', 'old_score', 'new_score', 'old_level', 'new_level', 'change_reason', 'changed_by', 'created_at']
            missing_columns = [col for col in required_columns if col not in column_names]
            
            if missing_columns:
                self.log_result("Risk History Table Exists", False, f"Missing columns: {missing_columns}")
                conn.close()
                return False
            
            self.log_result("Risk History Table Exists", True, f"Table exists with {len(columns)} columns: {column_names}")
            conn.close()
            return True
            
        except Exception as e:
            self.log_result("Risk History Table Exists", False, f"Exception: {str(e)}")
            return False
    
    async def test_risk_admin_profile_endpoint(self) -> bool:
        """Test 5: Check if /api/v1/admin/risk/{user_id}/profile is reachable"""
        try:
            if not self.admin_token:
                self.log_result("Risk Admin Profile Endpoint", False, "No admin token available")
                return False
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                test_user_id = str(uuid.uuid4())
                
                response = await client.get(
                    f"{self.base_url}/admin/risk/{test_user_id}/profile",
                    headers=headers
                )
                
                # Should return 200 with NO_PROFILE status for non-existent user
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "NO_PROFILE":
                        self.log_result("Risk Admin Profile Endpoint", True, "Endpoint reachable, returns NO_PROFILE for non-existent user")
                        return True
                    else:
                        self.log_result("Risk Admin Profile Endpoint", True, f"Endpoint reachable, returned: {data}")
                        return True
                else:
                    self.log_result("Risk Admin Profile Endpoint", False, f"Status: {response.status_code}, Response: {response.text}")
                    return False
                
        except Exception as e:
            self.log_result("Risk Admin Profile Endpoint", False, f"Exception: {str(e)}")
            return False
    
    async def test_risk_admin_history_endpoint(self) -> bool:
        """Test 6: Check if /api/v1/admin/risk/{user_id}/history is reachable"""
        try:
            if not self.admin_token:
                self.log_result("Risk Admin History Endpoint", False, "No admin token available")
                return False
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                test_user_id = str(uuid.uuid4())
                
                response = await client.get(
                    f"{self.base_url}/admin/risk/{test_user_id}/history",
                    headers=headers
                )
                
                # Should return 200 with empty list for non-existent user
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        self.log_result("Risk Admin History Endpoint", True, f"Endpoint reachable, returned {len(data)} history items")
                        return True
                    else:
                        self.log_result("Risk Admin History Endpoint", True, f"Endpoint reachable, returned: {data}")
                        return True
                else:
                    self.log_result("Risk Admin History Endpoint", False, f"Status: {response.status_code}, Response: {response.text}")
                    return False
                
        except Exception as e:
            self.log_result("Risk Admin History Endpoint", False, f"Exception: {str(e)}")
            return False
    
    async def test_risk_admin_override_endpoint(self) -> bool:
        """Test 7: Check if /api/v1/admin/risk/{user_id}/override is reachable"""
        try:
            if not self.admin_token:
                self.log_result("Risk Admin Override Endpoint", False, "No admin token available")
                return False
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                test_user_id = str(uuid.uuid4())
                
                payload = {
                    "score": 50,
                    "reason": "Test override for Risk Sprint 2 verification"
                }
                
                response = await client.post(
                    f"{self.base_url}/admin/risk/{test_user_id}/override",
                    json=payload,
                    headers=headers
                )
                
                # Should return 200 with updated profile
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "updated" and "profile" in data:
                        profile = data["profile"]
                        if profile.get("risk_score") == 50:
                            self.log_result("Risk Admin Override Endpoint", True, f"Endpoint working, created profile with score 50")
                            return True
                        else:
                            self.log_result("Risk Admin Override Endpoint", False, f"Score not updated correctly: {profile}")
                            return False
                    else:
                        self.log_result("Risk Admin Override Endpoint", False, f"Unexpected response format: {data}")
                        return False
                else:
                    self.log_result("Risk Admin Override Endpoint", False, f"Status: {response.status_code}, Response: {response.text}")
                    return False
                
        except Exception as e:
            self.log_result("Risk Admin Override Endpoint", False, f"Exception: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run the complete Risk Sprint 2 test suite"""
        print("🚀 Starting Risk Sprint 2 Test Suite...")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 80)
        
        # Run pytest tests first (don't need auth)
        test_results = []
        
        # Test 1: Pytest bet throttle
        test_results.append(self.test_pytest_bet_throttle())
        
        # Test 2: Pytest bet throttling integration
        test_results.append(self.test_pytest_bet_throttling_integration())
        
        # Test 3: Pytest admin risk dashboard API
        test_results.append(self.test_pytest_admin_risk_dashboard_api())
        
        # Test 4: Risk history table exists
        test_results.append(self.test_risk_history_table_exists())
        
        # Setup auth for API tests
        if not await self.setup_auth():
            print("\n❌ Authentication setup failed. Cannot proceed with API tests.")
            # Add failed results for API tests
            for test_name in ["Risk Admin Profile Endpoint", "Risk Admin History Endpoint", "Risk Admin Override Endpoint"]:
                self.log_result(test_name, False, "Authentication failed")
                test_results.append(False)
        else:
            # Test 5: Risk admin profile endpoint
            test_results.append(await self.test_risk_admin_profile_endpoint())
            
            # Test 6: Risk admin history endpoint
            test_results.append(await self.test_risk_admin_history_endpoint())
            
            # Test 7: Risk admin override endpoint
            test_results.append(await self.test_risk_admin_override_endpoint())
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 RISK SPRINT 2 TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(test_results)
        total = len(test_results)
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"]:
                print(f"    {result['details']}")
        
        print(f"\n🎯 OVERALL RESULT: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 All Risk Sprint 2 tests PASSED!")
            return True
        else:
            print(f"⚠️  {total - passed} test(s) failed. Review the details above.")
            return False

async def main():
    """Main test runner"""
    suite = RiskSprint2TestSuite()
    success = await suite.run_all_tests()
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)