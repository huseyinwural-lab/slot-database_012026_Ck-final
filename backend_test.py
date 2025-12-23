#!/usr/bin/env python3
"""
Backend ADMIN-REVIEW-002 Withdrawal Review API Test Suite

This test suite validates:
1. Login as admin
2. Create a test player and withdrawal request (or use existing)
3. Test Approve Withdrawal:
   - Call POST /api/v1/finance/withdrawals/{id}/review with action='approve' but NO reason. Expect 400 REASON_REQUIRED.
   - Call again WITH reason='Good to go'. Expect 200 OK.
4. Test Mark Paid:
   - Call POST /api/v1/finance/withdrawals/{id}/mark-paid without body or reason. Expect 400 REASON_REQUIRED (or 422 validation error).
   - Call again WITH body {"reason": "Done"}. Expect 200 OK.
5. Verify audit logs contain the reason.

Tests are designed to run against the localhost backend service.
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

# Use localhost backend for testing as requested
BACKEND_URL = "http://localhost:8001"

class AdminReview002TestSuite:
    def __init__(self):
        self.base_url = f"{BACKEND_URL}/api/v1"
        self.admin_token = None
        self.player_token = None
        self.test_player_id = None
        self.withdrawal_id = None
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
    
    async def create_test_player(self) -> bool:
        """Create a test player for withdrawal testing"""
        try:
            if not self.admin_token:
                self.log_result("Create Test Player", False, "No admin token available")
                return False
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                
                # Create a test player
                player_data = {
                    "email": f"testplayer_{uuid.uuid4().hex[:8]}@example.com",
                    "password": "TestPlayer123!",
                    "full_name": "Test Player for Withdrawal",
                    "kyc_status": "verified"  # Need verified KYC for withdrawals
                }
                
                response = await client.post(
                    f"{self.base_url}/admin/players",
                    json=player_data,
                    headers=headers
                )
                
                if response.status_code != 200:
                    self.log_result("Create Test Player", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
                    return False
                
                data = response.json()
                self.test_player_id = data.get("id")
                if not self.test_player_id:
                    self.log_result("Create Test Player", False, "No player ID in response")
                    return False
                
                self.log_result("Create Test Player", True, f"Player ID: {self.test_player_id}")
                
                # Login as the test player to get player token
                player_login_data = {
                    "email": player_data["email"],
                    "password": player_data["password"]
                }
                
                response = await client.post(
                    f"{self.base_url}/player/auth/login",
                    json=player_login_data
                )
                
                if response.status_code != 200:
                    self.log_result("Player Login", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
                    return False
                
                player_data = response.json()
                self.player_token = player_data.get("access_token")
                if not self.player_token:
                    self.log_result("Player Login", False, "No player access token in response")
                    return False
                
                self.log_result("Player Login", True, f"Player token length: {len(self.player_token)}")
                return True
                
        except Exception as e:
            self.log_result("Create Test Player", False, f"Exception: {str(e)}")
            return False
    
    async def fund_player_account(self) -> bool:
        """Fund the test player account so they can make withdrawals"""
        try:
            if not self.player_token:
                self.log_result("Fund Player Account", False, "No player token available")
                return False
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {
                    "Authorization": f"Bearer {self.player_token}",
                    "Idempotency-Key": str(uuid.uuid4())
                }
                
                # Make a test deposit
                deposit_data = {
                    "amount": 1000.0,
                    "method": "test"
                }
                
                response = await client.post(
                    f"{self.base_url}/player/wallet/deposit",
                    json=deposit_data,
                    headers=headers
                )
                
                if response.status_code != 200:
                    self.log_result("Fund Player Account", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
                    return False
                
                data = response.json()
                balance = data.get("balance", {})
                available = balance.get("available_real", 0)
                
                self.log_result("Fund Player Account", True, f"Available balance: {available}")
                return True
                
        except Exception as e:
            self.log_result("Fund Player Account", False, f"Exception: {str(e)}")
            return False
    
    async def create_withdrawal_request(self) -> bool:
        """Create a withdrawal request for testing"""
        try:
            if not self.player_token:
                self.log_result("Create Withdrawal Request", False, "No player token available")
                return False
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {
                    "Authorization": f"Bearer {self.player_token}",
                    "Idempotency-Key": str(uuid.uuid4())
                }
                
                # Create withdrawal request
                withdrawal_data = {
                    "amount": 100.0,
                    "method": "test_bank",
                    "address": "test-bank-account-123"
                }
                
                response = await client.post(
                    f"{self.base_url}/player/wallet/withdraw",
                    json=withdrawal_data,
                    headers=headers
                )
                
                if response.status_code != 200:
                    self.log_result("Create Withdrawal Request", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
                    return False
                
                data = response.json()
                transaction = data.get("transaction", {})
                self.withdrawal_id = transaction.get("id")
                
                if not self.withdrawal_id:
                    self.log_result("Create Withdrawal Request", False, "No withdrawal ID in response")
                    return False
                
                self.log_result("Create Withdrawal Request", True, 
                              f"Withdrawal ID: {self.withdrawal_id}, State: {transaction.get('state')}")
                return True
                
        except Exception as e:
            self.log_result("Create Withdrawal Request", False, f"Exception: {str(e)}")
            return False
    
    async def test_approve_withdrawal_without_reason(self) -> bool:
        """Test 1: Approve withdrawal without reason - should return 400 REASON_REQUIRED"""
        try:
            if not self.admin_token or not self.withdrawal_id:
                self.log_result("Approve Without Reason", False, "Missing admin token or withdrawal ID")
                return False
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                
                # Try to approve without reason
                payload = {"action": "approve"}  # No reason field
                
                response = await client.post(
                    f"{self.base_url}/finance/withdrawals/{self.withdrawal_id}/review",
                    json=payload,
                    headers=headers
                )
                
                if response.status_code != 400:
                    self.log_result("Approve Without Reason", False, 
                                  f"Expected 400, got {response.status_code}, Response: {response.text}")
                    return False
                
                data = response.json()
                error_code = data.get("detail", {}).get("error_code")
                
                if error_code != "REASON_REQUIRED":
                    self.log_result("Approve Without Reason", False, 
                                  f"Expected REASON_REQUIRED, got {error_code}")
                    return False
                
                self.log_result("Approve Without Reason", True, 
                              f"Correctly returned 400 with REASON_REQUIRED")
                return True
                
        except Exception as e:
            self.log_result("Approve Without Reason", False, f"Exception: {str(e)}")
            return False
    
    async def test_approve_withdrawal_with_reason(self) -> bool:
        """Test 2: Approve withdrawal with reason - should return 200 OK"""
        try:
            if not self.admin_token or not self.withdrawal_id:
                self.log_result("Approve With Reason", False, "Missing admin token or withdrawal ID")
                return False
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                
                # Approve with reason
                payload = {
                    "action": "approve",
                    "reason": "Good to go"
                }
                
                response = await client.post(
                    f"{self.base_url}/finance/withdrawals/{self.withdrawal_id}/review",
                    json=payload,
                    headers=headers
                )
                
                if response.status_code != 200:
                    self.log_result("Approve With Reason", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
                    return False
                
                data = response.json()
                transaction = data.get("transaction", {})
                state = transaction.get("state")
                
                if state != "approved":
                    self.log_result("Approve With Reason", False, 
                                  f"Expected state 'approved', got '{state}'")
                    return False
                
                self.log_result("Approve With Reason", True, 
                              f"Successfully approved withdrawal, state: {state}")
                return True
                
        except Exception as e:
            self.log_result("Approve With Reason", False, f"Exception: {str(e)}")
            return False
    
    async def test_mark_paid_without_reason(self) -> bool:
        """Test 3: Mark paid without reason - should return 400 REASON_REQUIRED"""
        try:
            if not self.admin_token or not self.withdrawal_id:
                self.log_result("Mark Paid Without Reason", False, "Missing admin token or withdrawal ID")
                return False
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                
                # Try to mark paid without reason
                payload = {}  # Empty body, no reason
                
                response = await client.post(
                    f"{self.base_url}/finance/withdrawals/{self.withdrawal_id}/mark-paid",
                    json=payload,
                    headers=headers
                )
                
                if response.status_code not in [400, 422]:
                    self.log_result("Mark Paid Without Reason", False, 
                                  f"Expected 400 or 422, got {response.status_code}, Response: {response.text}")
                    return False
                
                data = response.json()
                error_code = data.get("detail", {}).get("error_code")
                
                if error_code != "REASON_REQUIRED":
                    self.log_result("Mark Paid Without Reason", False, 
                                  f"Expected REASON_REQUIRED, got {error_code}")
                    return False
                
                self.log_result("Mark Paid Without Reason", True, 
                              f"Correctly returned {response.status_code} with REASON_REQUIRED")
                return True
                
        except Exception as e:
            self.log_result("Mark Paid Without Reason", False, f"Exception: {str(e)}")
            return False
    
    async def test_mark_paid_with_reason(self) -> bool:
        """Test 4: Mark paid with reason - should return 200 OK"""
        try:
            if not self.admin_token or not self.withdrawal_id:
                self.log_result("Mark Paid With Reason", False, "Missing admin token or withdrawal ID")
                return False
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                
                # Mark paid with reason
                payload = {"reason": "Done"}
                
                response = await client.post(
                    f"{self.base_url}/finance/withdrawals/{self.withdrawal_id}/mark-paid",
                    json=payload,
                    headers=headers
                )
                
                if response.status_code != 200:
                    self.log_result("Mark Paid With Reason", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
                    return False
                
                data = response.json()
                transaction = data.get("transaction", {})
                state = transaction.get("state")
                
                if state != "paid":
                    self.log_result("Mark Paid With Reason", False, 
                                  f"Expected state 'paid', got '{state}'")
                    return False
                
                self.log_result("Mark Paid With Reason", True, 
                              f"Successfully marked withdrawal as paid, state: {state}")
                return True
                
        except Exception as e:
            self.log_result("Mark Paid With Reason", False, f"Exception: {str(e)}")
            return False
    
    async def test_verify_audit_logs(self) -> bool:
        """Test 5: Verify audit logs contain the reasons"""
        try:
            if not self.admin_token or not self.withdrawal_id:
                self.log_result("Verify Audit Logs", False, "Missing admin token or withdrawal ID")
                return False
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                
                # Query audit logs for withdrawal-related events
                params = {
                    "resource_id": self.withdrawal_id,
                    "since_hours": 1,
                    "limit": 50
                }
                
                response = await client.get(
                    f"{self.base_url}/audit/events",
                    params=params,
                    headers=headers
                )
                
                if response.status_code != 200:
                    self.log_result("Verify Audit Logs", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
                    return False
                
                data = response.json()
                items = data.get("items", [])
                
                # Look for approval and mark-paid events with reasons
                approval_found = False
                mark_paid_found = False
                
                for item in items:
                    action = item.get("action", "")
                    details = item.get("details", {})
                    reason = details.get("reason")
                    
                    if action == "FIN_WITHDRAW_APPROVED" and reason == "Good to go":
                        approval_found = True
                    elif action == "FIN_WITHDRAW_MARK_PAID" and reason == "Done":
                        mark_paid_found = True
                
                if not approval_found:
                    self.log_result("Verify Audit Logs", False, 
                                  "Approval audit event with reason 'Good to go' not found")
                    return False
                
                if not mark_paid_found:
                    self.log_result("Verify Audit Logs", False, 
                                  "Mark paid audit event with reason 'Done' not found")
                    return False
                
                self.log_result("Verify Audit Logs", True, 
                              f"Found {len(items)} audit events, both approval and mark-paid reasons verified")
                return True
                
        except Exception as e:
            self.log_result("Verify Audit Logs", False, f"Exception: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run the complete ADMIN-REVIEW-002 test suite"""
        print("🚀 Starting ADMIN-REVIEW-002 Withdrawal Review API Test Suite...")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 80)
        
        # Setup
        if not await self.setup_auth():
            print("\n❌ Authentication setup failed. Cannot proceed with tests.")
            return False
        
        if not await self.create_test_player():
            print("\n❌ Test player creation failed. Cannot proceed with tests.")
            return False
        
        if not await self.fund_player_account():
            print("\n❌ Player account funding failed. Cannot proceed with tests.")
            return False
        
        if not await self.create_withdrawal_request():
            print("\n❌ Withdrawal request creation failed. Cannot proceed with tests.")
            return False
        
        # Run all tests
        test_results = []
        
        # Test 1: Approve without reason (should fail)
        test_results.append(await self.test_approve_withdrawal_without_reason())
        
        # Test 2: Approve with reason (should succeed)
        test_results.append(await self.test_approve_withdrawal_with_reason())
        
        # Test 3: Mark paid without reason (should fail)
        test_results.append(await self.test_mark_paid_without_reason())
        
        # Test 4: Mark paid with reason (should succeed)
        test_results.append(await self.test_mark_paid_with_reason())
        
        # Test 5: Verify audit logs contain reasons
        test_results.append(await self.test_verify_audit_logs())
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
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
            print("🎉 All ADMIN-REVIEW-002 withdrawal review tests PASSED!")
            return True
        else:
            print(f"⚠️  {total - passed} test(s) failed. Review the details above.")
            return False

async def main():
    """Main test runner"""
    test_suite = AdminReview002TestSuite()
    success = await test_suite.run_all_tests()
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)