#!/usr/bin/env python3
"""
Backend Test Suite

This test suite validates:
1. ADMIN-REVIEW-002 Withdrawal Review API
2. Responsible Gaming (RG) Player Exclusion and Login Enforcement

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

# Use backend URL from frontend/.env as specified in the review request
def get_backend_url():
    try:
        with open("/app/frontend/.env", "r") as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    return line.split("=", 1)[1].strip()
    except Exception:
        pass
    return "http://localhost:8001"  # fallback

BACKEND_URL = get_backend_url()

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
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Create a test player using player registration endpoint
                player_email = f"testplayer_{uuid.uuid4().hex[:8]}@example.com"
                player_password = "TestPlayer123!"
                
                player_data = {
                    "email": player_email,
                    "username": f"testplayer_{uuid.uuid4().hex[:8]}",
                    "password": player_password,
                    "tenant_id": "default_casino"
                }
                
                response = await client.post(
                    f"{self.base_url}/auth/player/register",
                    json=player_data
                )
                
                if response.status_code != 200:
                    self.log_result("Create Test Player", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
                    return False
                
                data = response.json()
                self.test_player_id = data.get("player_id")
                if not self.test_player_id:
                    self.log_result("Create Test Player", False, "No player ID in response")
                    return False
                
                self.log_result("Create Test Player", True, f"Player ID: {self.test_player_id}")
                
                # Login as the test player to get player token
                player_login_data = {
                    "email": player_email,
                    "password": player_password,
                    "tenant_id": "default_casino"
                }
                
                response = await client.post(
                    f"{self.base_url}/auth/player/login",
                    json=player_login_data
                )
                
                if response.status_code != 200:
                    self.log_result("Player Login", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
                    return False
                
                player_login_response = response.json()
                self.player_token = player_login_response.get("access_token")
                if not self.player_token:
                    self.log_result("Player Login", False, "No player access token in response")
                    return False
                
                self.log_result("Player Login", True, f"Player token length: {len(self.player_token)}")
                
                # Now we need to update the player's KYC status to verified using admin token
                if not self.admin_token:
                    self.log_result("Update Player KYC", False, "No admin token available")
                    return False
                
                # Update KYC status to verified using the KYC review endpoint
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                kyc_payload = {"status": "approved"}
                
                response = await client.post(
                    f"{self.base_url}/kyc/documents/{self.test_player_id}/review",
                    json=kyc_payload,
                    headers=headers
                )
                
                if response.status_code != 200:
                    self.log_result("Update Player KYC", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
                    return False
                
                kyc_data = response.json()
                player_status = kyc_data.get("player_status")
                
                if player_status != "verified":
                    self.log_result("Update Player KYC", False, 
                                  f"Expected 'verified', got '{player_status}'")
                    return False
                
                self.log_result("Update Player KYC", True, f"Player KYC status: {player_status}")
                
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

class P0VerificationTestSuite:
    def __init__(self):
        self.base_url = f"{BACKEND_URL}/api/v1"
        self.admin_token = None
        self.player_token = None
        self.test_player_email = None
        self.test_player_password = None
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
    
    async def test_seed_admin(self) -> bool:
        """Test 1: Seed admin via POST /api/v1/admin/seed"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(f"{self.base_url}/admin/seed")
                
                if response.status_code not in [200, 201]:
                    self.log_result("Seed Admin", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
                    return False
                
                data = response.json()
                self.log_result("Seed Admin", True, f"Admin seeded successfully: {data}")
                return True
                
        except Exception as e:
            self.log_result("Seed Admin", False, f"Exception: {str(e)}")
            return False
    
    async def test_admin_login(self) -> bool:
        """Test 2: Login admin (admin@casino.com/Admin123!)"""
        try:
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
                    self.log_result("Admin Login", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
                    return False
                
                data = response.json()
                self.admin_token = data.get("access_token")
                if not self.admin_token:
                    self.log_result("Admin Login", False, "No access token in response")
                    return False
                
                self.log_result("Admin Login", True, f"Admin logged in successfully")
                return True
                
        except Exception as e:
            self.log_result("Admin Login", False, f"Exception: {str(e)}")
            return False
    
    async def test_register_player(self) -> bool:
        """Test 3: Register a new player"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Generate unique player credentials
                self.test_player_email = f"p0test_{uuid.uuid4().hex[:8]}@casino.com"
                self.test_player_password = "P0TestPlayer123!"
                
                player_data = {
                    "email": self.test_player_email,
                    "username": f"p0test_{uuid.uuid4().hex[:8]}",
                    "password": self.test_player_password,
                    "tenant_id": "default_casino"
                }
                
                response = await client.post(
                    f"{self.base_url}/auth/player/register",
                    json=player_data
                )
                
                if response.status_code != 200:
                    self.log_result("Register Player", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
                    return False
                
                data = response.json()
                player_id = data.get("player_id")
                if not player_id:
                    self.log_result("Register Player", False, "No player ID in response")
                    return False
                
                self.log_result("Register Player", True, f"Player registered with ID: {player_id}")
                return True
                
        except Exception as e:
            self.log_result("Register Player", False, f"Exception: {str(e)}")
            return False
    
    async def test_player_login(self) -> bool:
        """Test 4: Login player"""
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
                
                self.log_result("Player Login", True, f"Player logged in successfully")
                return True
                
        except Exception as e:
            self.log_result("Player Login", False, f"Exception: {str(e)}")
            return False
    
    async def test_player_deposit(self) -> bool:
        """Test 5: Call POST /api/v1/player/wallet/deposit with required Idempotency-Key and method=test"""
        try:
            if not self.player_token:
                self.log_result("Player Deposit", False, "No player token available")
                return False
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {
                    "Authorization": f"Bearer {self.player_token}",
                    "Idempotency-Key": str(uuid.uuid4())
                }
                
                deposit_data = {
                    "amount": 100.0,
                    "method": "test"
                }
                
                response = await client.post(
                    f"{self.base_url}/player/wallet/deposit",
                    json=deposit_data,
                    headers=headers
                )
                
                if response.status_code != 200:
                    self.log_result("Player Deposit", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
                    return False
                
                data = response.json()
                self.log_result("Player Deposit", True, f"Deposit successful: {data}")
                return True
                
        except Exception as e:
            self.log_result("Player Deposit", False, f"Exception: {str(e)}")
            return False
    
    async def test_cors_preflight(self) -> bool:
        """Test 6: Call OPTIONS preflight to /api/v1/auth/player/login with Origin=http://localhost:3001 and verify CORS headers"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {
                    "Origin": "http://localhost:3001",
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "Content-Type,Authorization"
                }
                
                response = await client.options(
                    f"{self.base_url}/auth/player/login",
                    headers=headers
                )
                
                if response.status_code not in [200, 204]:
                    self.log_result("CORS Preflight", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
                    return False
                
                # Check CORS headers
                cors_origin = response.headers.get("Access-Control-Allow-Origin")
                cors_methods = response.headers.get("Access-Control-Allow-Methods")
                cors_headers = response.headers.get("Access-Control-Allow-Headers")
                
                # Verify that the origin is allowed
                origin_allowed = (cors_origin == "*" or 
                                cors_origin == "http://localhost:3001" or
                                "localhost:3001" in cors_origin)
                
                if not origin_allowed:
                    self.log_result("CORS Preflight", False, 
                                  f"Origin not allowed. Access-Control-Allow-Origin: {cors_origin}")
                    return False
                
                self.log_result("CORS Preflight", True, 
                              f"CORS headers valid - Origin: {cors_origin}, Methods: {cors_methods}, Headers: {cors_headers}")
                return True
                
        except Exception as e:
            self.log_result("CORS Preflight", False, f"Exception: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run the complete P0 verification test suite"""
        print("🚀 Starting P0 Backend Verification Test Suite...")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 80)
        
        # Run all tests in sequence
        test_results = []
        
        # Test 1: Seed admin
        test_results.append(await self.test_seed_admin())
        
        # Test 2: Admin login
        test_results.append(await self.test_admin_login())
        
        # Test 3: Register player
        test_results.append(await self.test_register_player())
        
        # Test 4: Player login
        test_results.append(await self.test_player_login())
        
        # Test 5: Player deposit
        test_results.append(await self.test_player_deposit())
        
        # Test 6: CORS preflight
        test_results.append(await self.test_cors_preflight())
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 P0 VERIFICATION TEST SUMMARY")
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
            print("🎉 All P0 verification tests PASSED!")
            return True
        else:
            print(f"⚠️  {total - passed} test(s) failed. Review the details above.")
            return False

class ResponsibleGamingTestSuite:
    def __init__(self):
        self.base_url = f"{BACKEND_URL}/api/v1"
        self.player_token = None
        self.test_player_email = None
        self.test_player_password = None
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
    
    async def test_rg_endpoint_exists(self) -> bool:
        """Test 1: Verify backend has new endpoint POST /api/v1/rg/player/exclusion (must not 404)"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Try to call the endpoint without auth to see if it exists (should get 401/403, not 404)
                response = await client.post(
                    f"{self.base_url}/rg/player/exclusion",
                    json={"type": "self_exclusion", "duration_hours": 24}
                )
                
                # We expect 401 (unauthorized) or 403 (forbidden), NOT 404 (not found)
                if response.status_code == 404:
                    self.log_result("RG Endpoint Exists", False, 
                                  f"Endpoint returned 404 - endpoint does not exist")
                    return False
                elif response.status_code in [401, 403]:
                    self.log_result("RG Endpoint Exists", True, 
                                  f"Endpoint exists (returned {response.status_code} as expected)")
                    return True
                else:
                    self.log_result("RG Endpoint Exists", True, 
                                  f"Endpoint exists (returned {response.status_code})")
                    return True
                    
        except Exception as e:
            self.log_result("RG Endpoint Exists", False, f"Exception: {str(e)}")
            return False
    
    async def create_and_login_player(self) -> bool:
        """Test 2: Create a player (register) and login to obtain player token"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Generate unique player credentials
                self.test_player_email = f"rgtest_{uuid.uuid4().hex[:8]}@example.com"
                self.test_player_password = "RGTestPlayer123!"
                
                # Register player
                player_data = {
                    "email": self.test_player_email,
                    "username": f"rgtest_{uuid.uuid4().hex[:8]}",
                    "password": self.test_player_password,
                    "tenant_id": "default_casino"
                }
                
                response = await client.post(
                    f"{self.base_url}/auth/player/register",
                    json=player_data
                )
                
                if response.status_code != 200:
                    self.log_result("Create Player", False, 
                                  f"Registration failed - Status: {response.status_code}, Response: {response.text}")
                    return False
                
                reg_data = response.json()
                player_id = reg_data.get("player_id")
                if not player_id:
                    self.log_result("Create Player", False, "No player ID in registration response")
                    return False
                
                self.log_result("Create Player", True, f"Player registered with ID: {player_id}")
                
                # Login player to get token
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
                                  f"Login failed - Status: {response.status_code}, Response: {response.text}")
                    return False
                
                login_response = response.json()
                self.player_token = login_response.get("access_token")
                if not self.player_token:
                    self.log_result("Player Login", False, "No access token in login response")
                    return False
                
                self.log_result("Player Login", True, f"Player logged in successfully, token length: {len(self.player_token)}")
                return True
                
        except Exception as e:
            self.log_result("Create and Login Player", False, f"Exception: {str(e)}")
            return False
    
    async def test_self_exclusion(self) -> bool:
        """Test 3: Call POST /api/v1/rg/player/exclusion with body {"type":"self_exclusion","duration_hours":24} using Bearer player token; expect HTTP 200"""
        try:
            if not self.player_token:
                self.log_result("Self Exclusion", False, "No player token available")
                return False
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {self.player_token}"}
                
                exclusion_data = {
                    "type": "self_exclusion",
                    "duration_hours": 24
                }
                
                response = await client.post(
                    f"{self.base_url}/rg/player/exclusion",
                    json=exclusion_data,
                    headers=headers
                )
                
                if response.status_code != 200:
                    self.log_result("Self Exclusion", False, 
                                  f"Expected 200, got {response.status_code}, Response: {response.text}")
                    return False
                
                data = response.json()
                status = data.get("status")
                exclusion_type = data.get("type")
                duration_hours = data.get("duration_hours")
                
                if status != "ok":
                    self.log_result("Self Exclusion", False, f"Expected status 'ok', got '{status}'")
                    return False
                
                if exclusion_type != "self_exclusion":
                    self.log_result("Self Exclusion", False, f"Expected type 'self_exclusion', got '{exclusion_type}'")
                    return False
                
                if duration_hours != 24:
                    self.log_result("Self Exclusion", False, f"Expected duration_hours 24, got {duration_hours}")
                    return False
                
                self.log_result("Self Exclusion", True, 
                              f"Self-exclusion successful: status={status}, type={exclusion_type}, duration={duration_hours}h")
                return True
                
        except Exception as e:
            self.log_result("Self Exclusion", False, f"Exception: {str(e)}")
            return False
    
    async def test_login_enforcement(self) -> bool:
        """Test 4: Call POST /api/v1/auth/player/login again for same player; expect HTTP 403 with detail RG_SELF_EXCLUDED"""
        try:
            if not self.test_player_email or not self.test_player_password:
                self.log_result("Login Enforcement", False, "No player credentials available")
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
                
                if response.status_code != 403:
                    self.log_result("Login Enforcement", False, 
                                  f"Expected 403, got {response.status_code}, Response: {response.text}")
                    return False
                
                data = response.json()
                detail = data.get("detail")
                
                if detail != "RG_SELF_EXCLUDED":
                    self.log_result("Login Enforcement", False, 
                                  f"Expected detail 'RG_SELF_EXCLUDED', got '{detail}'")
                    return False
                
                self.log_result("Login Enforcement", True, 
                              f"Login correctly blocked with 403 and detail 'RG_SELF_EXCLUDED'")
                return True
                
        except Exception as e:
            self.log_result("Login Enforcement", False, f"Exception: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run the complete Responsible Gaming test suite"""
        print("🚀 Starting Responsible Gaming Player Exclusion Test Suite...")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 80)
        
        # Run all tests in sequence
        test_results = []
        
        # Test 1: Verify RG endpoint exists
        test_results.append(await self.test_rg_endpoint_exists())
        
        # Test 2: Create player and login
        test_results.append(await self.create_and_login_player())
        
        # Test 3: Self-exclusion
        test_results.append(await self.test_self_exclusion())
        
        # Test 4: Login enforcement
        test_results.append(await self.test_login_enforcement())
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 RESPONSIBLE GAMING TEST SUMMARY")
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
            print("🎉 All Responsible Gaming tests PASSED!")
            return True
        else:
            print(f"⚠️  {total - passed} test(s) failed. Review the details above.")
            return False


async def main():
    """Main test runner"""
    print("🎯 Backend Test Suite Runner")
    print("=" * 80)
    
    # Check which test suite to run based on command line args or run both
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "p0":
        # Run only P0 verification tests
        print("Running P0 verification tests only...")
        p0_suite = P0VerificationTestSuite()
        success = await p0_suite.run_all_tests()
        return success
    elif len(sys.argv) > 1 and sys.argv[1] == "rg":
        # Run only Responsible Gaming tests
        print("Running Responsible Gaming tests only...")
        rg_suite = ResponsibleGamingTestSuite()
        success = await rg_suite.run_all_tests()
        return success
    elif len(sys.argv) > 1 and sys.argv[1] == "admin":
        # Run only Admin Review tests
        print("Running Admin Review tests only...")
        admin_suite = AdminReview002TestSuite()
        success = await admin_suite.run_all_tests()
        return success
    else:
        # Run P0 verification tests (as requested in review)
        print("Running P0 verification tests...")
        p0_suite = P0VerificationTestSuite()
        p0_success = await p0_suite.run_all_tests()
        
        print("\n" + "=" * 80)
        print("🏁 FINAL SUMMARY")
        print("=" * 80)
        print(f"P0 Verification Tests: {'✅ PASSED' if p0_success else '❌ FAILED'}")
        
        return p0_success


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)