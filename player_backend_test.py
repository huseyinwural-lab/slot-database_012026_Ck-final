#!/usr/bin/env python3
"""
Player App Backend Test Suite

This test suite validates the player app verification flows:
1. Email verification (mocked API)
2. SMS verification (mocked API) 
3. Support ticket submission (mocked API)
4. Player registration and login flow
5. Wallet operations (verification dependent)

Tests are designed to run against the configured backend service.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List, Tuple
import httpx
import os
import uuid

# Get backend URL from frontend-player .env
def get_backend_url():
    try:
        with open("/app/frontend-player/.env", "r") as f:
            for line in f:
                if line.startswith("VITE_API_URL="):
                    return line.split("=", 1)[1].strip()
    except Exception:
        pass
    return "http://localhost:8001/api/v1"  # fallback

BACKEND_URL = get_backend_url()

class PlayerAppTestSuite:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.test_results = []
        self.test_player_email = None
        self.test_player_phone = None
        self.test_player_password = None
        self.player_token = None
        
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
    
    async def test_email_verification_send(self) -> bool:
        """Test 1: Send email verification code (mocked API)"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                self.test_player_email = f"player_{uuid.uuid4().hex[:8]}@test.com"
                
                payload = {"email": self.test_player_email}
                
                response = await client.post(
                    f"{self.base_url}/verify/email/send",
                    json=payload
                )
                
                if response.status_code != 200:
                    self.log_result("Email Verification Send", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
                    return False
                
                data = response.json()
                if not data.get("ok"):
                    self.log_result("Email Verification Send", False, 
                                  f"Response not ok: {data}")
                    return False
                
                self.log_result("Email Verification Send", True, 
                              f"Email verification sent to {self.test_player_email}")
                return True
                
        except Exception as e:
            self.log_result("Email Verification Send", False, f"Exception: {str(e)}")
            return False
    
    async def test_email_verification_confirm(self) -> bool:
        """Test 2: Confirm email verification with code 123456 (mocked API)"""
        try:
            if not self.test_player_email:
                self.log_result("Email Verification Confirm", False, "No test email available")
                return False
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "email": self.test_player_email,
                    "code": "123456"
                }
                
                response = await client.post(
                    f"{self.base_url}/verify/email/confirm",
                    json=payload
                )
                
                if response.status_code != 200:
                    self.log_result("Email Verification Confirm", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
                    return False
                
                data = response.json()
                if not data.get("ok"):
                    self.log_result("Email Verification Confirm", False, 
                                  f"Response not ok: {data}")
                    return False
                
                status = data.get("data", {}).get("status")
                if status != "verified":
                    self.log_result("Email Verification Confirm", False, 
                                  f"Expected status 'verified', got '{status}'")
                    return False
                
                self.log_result("Email Verification Confirm", True, 
                              f"Email verification confirmed with status: {status}")
                return True
                
        except Exception as e:
            self.log_result("Email Verification Confirm", False, f"Exception: {str(e)}")
            return False
    
    async def test_sms_verification_send(self) -> bool:
        """Test 3: Send SMS verification code (mocked API)"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                self.test_player_phone = f"+1555{uuid.uuid4().hex[:7]}"
                
                payload = {"phone": self.test_player_phone}
                
                response = await client.post(
                    f"{self.base_url}/verify/sms/send",
                    json=payload
                )
                
                if response.status_code != 200:
                    self.log_result("SMS Verification Send", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
                    return False
                
                data = response.json()
                if not data.get("ok"):
                    self.log_result("SMS Verification Send", False, 
                                  f"Response not ok: {data}")
                    return False
                
                self.log_result("SMS Verification Send", True, 
                              f"SMS verification sent to {self.test_player_phone}")
                return True
                
        except Exception as e:
            self.log_result("SMS Verification Send", False, f"Exception: {str(e)}")
            return False
    
    async def test_sms_verification_confirm(self) -> bool:
        """Test 4: Confirm SMS verification with code 123456 (mocked API)"""
        try:
            if not self.test_player_phone:
                self.log_result("SMS Verification Confirm", False, "No test phone available")
                return False
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "phone": self.test_player_phone,
                    "code": "123456"
                }
                
                response = await client.post(
                    f"{self.base_url}/verify/sms/confirm",
                    json=payload
                )
                
                if response.status_code != 200:
                    self.log_result("SMS Verification Confirm", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
                    return False
                
                data = response.json()
                if not data.get("ok"):
                    self.log_result("SMS Verification Confirm", False, 
                                  f"Response not ok: {data}")
                    return False
                
                status = data.get("data", {}).get("status")
                if status != "verified":
                    self.log_result("SMS Verification Confirm", False, 
                                  f"Expected status 'verified', got '{status}'")
                    return False
                
                self.log_result("SMS Verification Confirm", True, 
                              f"SMS verification confirmed with status: {status}")
                return True
                
        except Exception as e:
            self.log_result("SMS Verification Confirm", False, f"Exception: {str(e)}")
            return False
    
    async def test_support_ticket_submission(self) -> bool:
        """Test 5: Submit support ticket (mocked API)"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {"message": "Test support ticket from player app"}
                
                response = await client.post(
                    f"{self.base_url}/support/ticket",
                    json=payload
                )
                
                if response.status_code != 200:
                    self.log_result("Support Ticket Submission", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
                    return False
                
                data = response.json()
                if not data.get("ok"):
                    self.log_result("Support Ticket Submission", False, 
                                  f"Response not ok: {data}")
                    return False
                
                status = data.get("data", {}).get("status")
                if status != "received":
                    self.log_result("Support Ticket Submission", False, 
                                  f"Expected status 'received', got '{status}'")
                    return False
                
                self.log_result("Support Ticket Submission", True, 
                              f"Support ticket submitted with status: {status}")
                return True
                
        except Exception as e:
            self.log_result("Support Ticket Submission", False, f"Exception: {str(e)}")
            return False
    
    async def test_player_registration(self) -> bool:
        """Test 6: Player registration flow"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if not self.test_player_email:
                    self.test_player_email = f"player_{uuid.uuid4().hex[:8]}@test.com"
                
                self.test_player_password = "TestPlayer123!"
                
                player_data = {
                    "username": f"testplayer_{uuid.uuid4().hex[:8]}",
                    "email": self.test_player_email,
                    "phone": self.test_player_phone or f"+1555{uuid.uuid4().hex[:7]}",
                    "dob": "1990-01-01",
                    "password": self.test_player_password,
                    "tenant_id": "default_casino"
                }
                
                response = await client.post(
                    f"{self.base_url}/auth/player/register",
                    json=player_data
                )
                
                if response.status_code != 200:
                    self.log_result("Player Registration", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
                    return False
                
                data = response.json()
                player_id = data.get("player_id")
                if not player_id:
                    self.log_result("Player Registration", False, "No player ID in response")
                    return False
                
                self.log_result("Player Registration", True, 
                              f"Player registered with ID: {player_id}")
                return True
                
        except Exception as e:
            self.log_result("Player Registration", False, f"Exception: {str(e)}")
            return False
    
    async def test_player_login(self) -> bool:
        """Test 7: Player login flow"""
        try:
            if not self.test_player_email or not self.test_player_password:
                self.log_result("Player Login", False, "No player credentials available")
                return False
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                login_data = {
                    "email": self.test_player_email,
                    "password": self.test_player_password,
                    "tenant_id": "default_casino"
                }
                
                response = await client.post(
                    f"{self.base_url}/auth/player/login",
                    json=login_data
                )
                
                if response.status_code != 200:
                    self.log_result("Player Login", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
                    return False
                
                data = response.json()
                self.player_token = data.get("access_token")
                if not self.player_token:
                    self.log_result("Player Login", False, "No access token in response")
                    return False
                
                self.log_result("Player Login", True, 
                              f"Player logged in successfully, token length: {len(self.player_token)}")
                return True
                
        except Exception as e:
            self.log_result("Player Login", False, f"Exception: {str(e)}")
            return False
    
    async def test_wallet_balance(self) -> bool:
        """Test 8: Get wallet balance (requires authentication)"""
        try:
            if not self.player_token:
                self.log_result("Wallet Balance", False, "No player token available")
                return False
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {self.player_token}"}
                
                response = await client.get(
                    f"{self.base_url}/player/wallet/balance",
                    headers=headers
                )
                
                if response.status_code != 200:
                    self.log_result("Wallet Balance", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
                    return False
                
                data = response.json()
                balance = data.get("balance", {})
                available = balance.get("available_real", 0)
                
                self.log_result("Wallet Balance", True, 
                              f"Wallet balance retrieved: {available}")
                return True
                
        except Exception as e:
            self.log_result("Wallet Balance", False, f"Exception: {str(e)}")
            return False
    
    async def test_telemetry_events(self) -> bool:
        """Test 9: Send telemetry events (mocked API)"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "events": [
                        {
                            "type": "page_view",
                            "data": {"page": "/lobby"},
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    ]
                }
                
                response = await client.post(
                    f"{self.base_url}/telemetry/events",
                    json=payload
                )
                
                # Telemetry might return 200 or 204, both are acceptable
                if response.status_code not in [200, 204]:
                    self.log_result("Telemetry Events", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
                    return False
                
                self.log_result("Telemetry Events", True, 
                              f"Telemetry events sent successfully (Status: {response.status_code})")
                return True
                
        except Exception as e:
            self.log_result("Telemetry Events", False, f"Exception: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run the complete player app test suite"""
        print("🚀 Starting Player App Backend Test Suite...")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 80)
        
        # Run all tests in sequence
        test_results = []
        
        # Test 1: Email verification send
        test_results.append(await self.test_email_verification_send())
        
        # Test 2: Email verification confirm
        test_results.append(await self.test_email_verification_confirm())
        
        # Test 3: SMS verification send
        test_results.append(await self.test_sms_verification_send())
        
        # Test 4: SMS verification confirm
        test_results.append(await self.test_sms_verification_confirm())
        
        # Test 5: Support ticket submission
        test_results.append(await self.test_support_ticket_submission())
        
        # Test 6: Player registration
        test_results.append(await self.test_player_registration())
        
        # Test 7: Player login
        test_results.append(await self.test_player_login())
        
        # Test 8: Wallet balance
        test_results.append(await self.test_wallet_balance())
        
        # Test 9: Telemetry events
        test_results.append(await self.test_telemetry_events())
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 PLAYER APP BACKEND TEST SUMMARY")
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
            print("🎉 All player app backend tests PASSED!")
            return True
        else:
            print(f"⚠️  {total - passed} test(s) failed. Review the details above.")
            return False

async def main():
    """Main test runner"""
    suite = PlayerAppTestSuite()
    success = await suite.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))