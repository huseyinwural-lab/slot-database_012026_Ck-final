#!/usr/bin/env python3
"""
Backend LEDGER-OPS-001 Reconciliation Test Suite

This test suite validates:
1. POST /api/v1/finance/reconciliation/run?date={TODAY} - should return 200 OK (previously 520)
2. GET /api/v1/finance/reconciliation/summary?date={TODAY} - confirm results
3. Unit tests in backend/tests/test_reconciliation.py still pass

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

class LedgerOps001ReconciliationTestSuite:
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
    
    async def test_reconciliation_run_endpoint(self) -> bool:
        """Test 1: POST /api/v1/finance/reconciliation/run?date={TODAY} - should return 200 OK"""
        try:
            if not self.admin_token:
                self.log_result("Reconciliation Run Endpoint", False, "No admin token available")
                return False
            
            async with httpx.AsyncClient(timeout=60.0) as client:  # Increased timeout for reconciliation
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                
                # Get today's date in ISO format
                today = datetime.now(timezone.utc).date().isoformat()
                
                # Test the reconciliation run endpoint
                response = await client.post(
                    f"{self.base_url}/finance/reconciliation/run",
                    params={"date": today},
                    headers=headers
                )
                
                if response.status_code != 200:
                    self.log_result("Reconciliation Run Endpoint", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
                    return False
                
                data = response.json()
                
                # Validate response structure
                required_fields = ["run_id", "inserted", "scanned"]
                for field in required_fields:
                    if field not in data:
                        self.log_result("Reconciliation Run Endpoint", False, 
                                      f"Missing field in response: {field}")
                        return False
                
                # Validate field types
                if not isinstance(data["inserted"], int) or data["inserted"] < 0:
                    self.log_result("Reconciliation Run Endpoint", False, 
                                  f"Invalid inserted count: {data['inserted']}")
                    return False
                
                if not isinstance(data["scanned"], int) or data["scanned"] < 0:
                    self.log_result("Reconciliation Run Endpoint", False, 
                                  f"Invalid scanned count: {data['scanned']}")
                    return False
                
                if not data["run_id"] or not isinstance(data["run_id"], str):
                    self.log_result("Reconciliation Run Endpoint", False, 
                                  f"Invalid run_id: {data['run_id']}")
                    return False
                
                self.log_result("Reconciliation Run Endpoint", True, 
                              f"Run ID: {data['run_id']}, Inserted: {data['inserted']}, Scanned: {data['scanned']}")
                
                # Store run_id for summary test
                self.last_run_id = data["run_id"]
                return True
                
        except Exception as e:
            self.log_result("Reconciliation Run Endpoint", False, f"Exception: {str(e)}")
            return False
    
    async def test_reconciliation_summary_endpoint(self) -> bool:
        """Test 2: GET /api/v1/finance/reconciliation/summary?date={TODAY} - confirm results"""
        try:
            if not self.admin_token:
                self.log_result("Reconciliation Summary Endpoint", False, "No admin token available")
                return False
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                
                # Get today's date in ISO format
                today = datetime.now(timezone.utc).date().isoformat()
                
                # Test the reconciliation summary endpoint
                response = await client.get(
                    f"{self.base_url}/finance/reconciliation/summary",
                    params={"date": today},
                    headers=headers
                )
                
                if response.status_code != 200:
                    self.log_result("Reconciliation Summary Endpoint", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
                    return False
                
                data = response.json()
                
                # Validate response structure
                required_fields = ["run_id", "counts_by_finding_code", "counts_by_severity", "scanned_tx_count"]
                for field in required_fields:
                    if field not in data:
                        self.log_result("Reconciliation Summary Endpoint", False, 
                                      f"Missing field in response: {field}")
                        return False
                
                # Validate field types
                if not isinstance(data["counts_by_finding_code"], dict):
                    self.log_result("Reconciliation Summary Endpoint", False, 
                                  f"Invalid counts_by_finding_code: {data['counts_by_finding_code']}")
                    return False
                
                if not isinstance(data["counts_by_severity"], dict):
                    self.log_result("Reconciliation Summary Endpoint", False, 
                                  f"Invalid counts_by_severity: {data['counts_by_severity']}")
                    return False
                
                if not isinstance(data["scanned_tx_count"], int) or data["scanned_tx_count"] < 0:
                    self.log_result("Reconciliation Summary Endpoint", False, 
                                  f"Invalid scanned_tx_count: {data['scanned_tx_count']}")
                    return False
                
                # Check if run_id matches the one from the run endpoint (if we have it)
                if hasattr(self, 'last_run_id') and data["run_id"] and data["run_id"] != self.last_run_id:
                    self.log_result("Reconciliation Summary Endpoint", False, 
                                  f"Run ID mismatch: expected {self.last_run_id}, got {data['run_id']}")
                    return False
                
                self.log_result("Reconciliation Summary Endpoint", True, 
                              f"Run ID: {data['run_id']}, Scanned: {data['scanned_tx_count']}, "
                              f"Finding codes: {len(data['counts_by_finding_code'])}, "
                              f"Severities: {len(data['counts_by_severity'])}")
                return True
                
        except Exception as e:
            self.log_result("Reconciliation Summary Endpoint", False, f"Exception: {str(e)}")
            return False
    
    async def test_reconciliation_unit_tests(self) -> bool:
        """Test 3: Run existing unit tests in backend/tests/test_reconciliation.py"""
        try:
            # Run the existing pytest tests for reconciliation
            result = subprocess.run([
                "python", "-m", "pytest", 
                "tests/test_reconciliation.py", 
                "-v"
            ], 
            cwd="/app/backend",
            capture_output=True, 
            text=True,
            timeout=120
            )
            
            if result.returncode == 0:
                # Count passed tests
                output_lines = result.stdout.split('\n')
                passed_tests = [line for line in output_lines if '::test_' in line and 'PASSED' in line]
                
                self.log_result("Reconciliation Unit Tests", True, 
                              f"All {len(passed_tests)} pytest tests passed. Tests: {[line.split('::')[1].split(' ')[0] for line in passed_tests]}")
                return True
            else:
                self.log_result("Reconciliation Unit Tests", False, 
                              f"Pytest failed. Return code: {result.returncode}, "
                              f"Stdout: {result.stdout}, Stderr: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.log_result("Reconciliation Unit Tests", False, "Pytest timed out after 120 seconds")
            return False
        except Exception as e:
            self.log_result("Reconciliation Unit Tests", False, f"Exception running pytest: {str(e)}")
            return False
    
    async def test_reconciliation_findings_endpoint(self) -> bool:
        """Test 4: GET /api/v1/finance/reconciliation/findings - validate findings structure"""
        try:
            if not self.admin_token:
                self.log_result("Reconciliation Findings Endpoint", False, "No admin token available")
                return False
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                
                # Get today's date in ISO format
                today = datetime.now(timezone.utc).date().isoformat()
                
                # Test the reconciliation findings endpoint
                response = await client.get(
                    f"{self.base_url}/finance/reconciliation/findings",
                    params={"date": today, "limit": 10},
                    headers=headers
                )
                
                if response.status_code != 200:
                    self.log_result("Reconciliation Findings Endpoint", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
                    return False
                
                data = response.json()
                
                # Validate response structure
                if "items" not in data or "meta" not in data:
                    self.log_result("Reconciliation Findings Endpoint", False, 
                                  "Missing items or meta in response")
                    return False
                
                meta = data["meta"]
                items = data["items"]
                
                # Validate meta fields
                required_meta_fields = ["total", "limit", "offset"]
                for field in required_meta_fields:
                    if field not in meta:
                        self.log_result("Reconciliation Findings Endpoint", False, 
                                      f"Missing {field} in meta")
                        return False
                
                # Validate items structure (if any findings exist)
                for item in items:
                    required_item_fields = ["tenant_id", "tx_id", "finding_type", "severity", "status", "raw"]
                    for field in required_item_fields:
                        if field not in item:
                            self.log_result("Reconciliation Findings Endpoint", False, 
                                          f"Missing {field} in finding item")
                            return False
                
                self.log_result("Reconciliation Findings Endpoint", True, 
                              f"Total findings: {meta['total']}, Items returned: {len(items)}")
                return True
                
        except Exception as e:
            self.log_result("Reconciliation Findings Endpoint", False, f"Exception: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run the complete LEDGER-OPS-001 reconciliation test suite"""
        print("🚀 Starting LEDGER-OPS-001 Reconciliation Test Suite...")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 80)
        
        # Setup
        if not await self.setup_auth():
            print("\n❌ Authentication setup failed. Cannot proceed with tests.")
            return False
        
        # Run all tests
        test_results = []
        
        # Test 1: Reconciliation run endpoint (the main fix)
        test_results.append(await self.test_reconciliation_run_endpoint())
        
        # Test 2: Reconciliation summary endpoint
        test_results.append(await self.test_reconciliation_summary_endpoint())
        
        # Test 3: Unit tests still pass
        test_results.append(await self.test_reconciliation_unit_tests())
        
        # Test 4: Reconciliation findings endpoint (additional validation)
        test_results.append(await self.test_reconciliation_findings_endpoint())
        
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
            print("🎉 All LEDGER-OPS-001 reconciliation tests PASSED!")
            return True
        else:
            print(f"⚠️  {total - passed} test(s) failed. Review the details above.")
            return False

async def main():
    """Main test runner"""
    test_suite = P04PanelIntegrityTestSuite()
    success = await test_suite.run_all_tests()
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)