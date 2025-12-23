#!/usr/bin/env python3
"""
LEDGER-OPS-001 Reconciliation API Test Suite

This test suite validates:
1. POST /api/v1/finance/reconciliation/run?date={TODAY}
2. GET /api/v1/finance/reconciliation/summary?date={TODAY}

Tests are designed to run against the backend service using the configured URL.
"""

import asyncio
import json
from datetime import datetime, timezone, date as date_cls
import httpx
import os

# Get backend URL from frontend .env file
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    except:
        pass
    return "http://localhost:8001"

BACKEND_URL = get_backend_url()

class ReconciliationTestSuite:
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
        """Test POST /api/v1/finance/reconciliation/run?date={TODAY}"""
        try:
            if not self.admin_token:
                self.log_result("Reconciliation Run Endpoint", False, "No admin token available")
                return False
            
            async with httpx.AsyncClient(timeout=60.0) as client:  # Longer timeout for reconciliation
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                
                # Test with today's date
                today = date_cls.today().isoformat()
                
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
                        self.log_result("Reconciliation Run Endpoint", False, f"Missing field: {field}")
                        return False
                
                # Validate field types
                if not isinstance(data["run_id"], str):
                    self.log_result("Reconciliation Run Endpoint", False, f"Invalid run_id type: {type(data['run_id'])}")
                    return False
                
                if not isinstance(data["inserted"], int) or data["inserted"] < 0:
                    self.log_result("Reconciliation Run Endpoint", False, f"Invalid inserted count: {data['inserted']}")
                    return False
                
                if not isinstance(data["scanned"], int) or data["scanned"] < 0:
                    self.log_result("Reconciliation Run Endpoint", False, f"Invalid scanned count: {data['scanned']}")
                    return False
                
                self.log_result("Reconciliation Run Endpoint", True, 
                              f"Run ID: {data['run_id']}, Inserted: {data['inserted']}, Scanned: {data['scanned']}")
                return True
                
        except Exception as e:
            self.log_result("Reconciliation Run Endpoint", False, f"Exception: {str(e)}")
            return False
    
    async def test_reconciliation_summary_endpoint(self) -> bool:
        """Test GET /api/v1/finance/reconciliation/summary?date={TODAY}"""
        try:
            if not self.admin_token:
                self.log_result("Reconciliation Summary Endpoint", False, "No admin token available")
                return False
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                
                # Test with today's date
                today = date_cls.today().isoformat()
                
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
                        self.log_result("Reconciliation Summary Endpoint", False, f"Missing field: {field}")
                        return False
                
                # Validate field types
                if data["run_id"] is not None and not isinstance(data["run_id"], str):
                    self.log_result("Reconciliation Summary Endpoint", False, f"Invalid run_id type: {type(data['run_id'])}")
                    return False
                
                if not isinstance(data["counts_by_finding_code"], dict):
                    self.log_result("Reconciliation Summary Endpoint", False, f"Invalid counts_by_finding_code type: {type(data['counts_by_finding_code'])}")
                    return False
                
                if not isinstance(data["counts_by_severity"], dict):
                    self.log_result("Reconciliation Summary Endpoint", False, f"Invalid counts_by_severity type: {type(data['counts_by_severity'])}")
                    return False
                
                if not isinstance(data["scanned_tx_count"], int) or data["scanned_tx_count"] < 0:
                    self.log_result("Reconciliation Summary Endpoint", False, f"Invalid scanned_tx_count: {data['scanned_tx_count']}")
                    return False
                
                # Log summary details
                finding_codes = list(data["counts_by_finding_code"].keys())
                severities = list(data["counts_by_severity"].keys())
                
                details = f"Run ID: {data['run_id']}, Scanned: {data['scanned_tx_count']}"
                if finding_codes:
                    details += f", Finding codes: {finding_codes}"
                if severities:
                    details += f", Severities: {severities}"
                
                self.log_result("Reconciliation Summary Endpoint", True, details)
                return True
                
        except Exception as e:
            self.log_result("Reconciliation Summary Endpoint", False, f"Exception: {str(e)}")
            return False
    
    async def test_reconciliation_run_without_date(self) -> bool:
        """Test POST /api/v1/finance/reconciliation/run without date parameter (should default to today)"""
        try:
            if not self.admin_token:
                self.log_result("Reconciliation Run Without Date", False, "No admin token available")
                return False
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                
                response = await client.post(
                    f"{self.base_url}/finance/reconciliation/run",
                    headers=headers
                )
                
                if response.status_code != 200:
                    self.log_result("Reconciliation Run Without Date", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
                    return False
                
                data = response.json()
                
                # Validate response structure (same as with date)
                required_fields = ["run_id", "inserted", "scanned"]
                for field in required_fields:
                    if field not in data:
                        self.log_result("Reconciliation Run Without Date", False, f"Missing field: {field}")
                        return False
                
                self.log_result("Reconciliation Run Without Date", True, 
                              f"Run ID: {data['run_id']}, Inserted: {data['inserted']}, Scanned: {data['scanned']}")
                return True
                
        except Exception as e:
            self.log_result("Reconciliation Run Without Date", False, f"Exception: {str(e)}")
            return False
    
    async def test_reconciliation_summary_without_date(self) -> bool:
        """Test GET /api/v1/finance/reconciliation/summary without date parameter (should default to today)"""
        try:
            if not self.admin_token:
                self.log_result("Reconciliation Summary Without Date", False, "No admin token available")
                return False
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                
                response = await client.get(
                    f"{self.base_url}/finance/reconciliation/summary",
                    headers=headers
                )
                
                if response.status_code != 200:
                    self.log_result("Reconciliation Summary Without Date", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
                    return False
                
                data = response.json()
                
                # Validate response structure (same as with date)
                required_fields = ["run_id", "counts_by_finding_code", "counts_by_severity", "scanned_tx_count"]
                for field in required_fields:
                    if field not in data:
                        self.log_result("Reconciliation Summary Without Date", False, f"Missing field: {field}")
                        return False
                
                self.log_result("Reconciliation Summary Without Date", True, 
                              f"Run ID: {data['run_id']}, Scanned: {data['scanned_tx_count']}")
                return True
                
        except Exception as e:
            self.log_result("Reconciliation Summary Without Date", False, f"Exception: {str(e)}")
            return False
    
    async def test_reconciliation_findings_endpoint(self) -> bool:
        """Test GET /api/v1/finance/reconciliation/findings endpoint"""
        try:
            if not self.admin_token:
                self.log_result("Reconciliation Findings Endpoint", False, "No admin token available")
                return False
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                
                # Test with today's date
                today = date_cls.today().isoformat()
                
                response = await client.get(
                    f"{self.base_url}/finance/reconciliation/findings",
                    params={"date": today},
                    headers=headers
                )
                
                if response.status_code != 200:
                    self.log_result("Reconciliation Findings Endpoint", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
                    return False
                
                data = response.json()
                
                # Validate response structure
                required_fields = ["items", "meta"]
                for field in required_fields:
                    if field not in data:
                        self.log_result("Reconciliation Findings Endpoint", False, f"Missing field: {field}")
                        return False
                
                # Validate meta structure
                meta = data["meta"]
                required_meta_fields = ["total", "limit", "offset"]
                for field in required_meta_fields:
                    if field not in meta:
                        self.log_result("Reconciliation Findings Endpoint", False, f"Missing meta field: {field}")
                        return False
                
                items = data["items"]
                if not isinstance(items, list):
                    self.log_result("Reconciliation Findings Endpoint", False, f"Items should be a list, got: {type(items)}")
                    return False
                
                self.log_result("Reconciliation Findings Endpoint", True, 
                              f"Found {len(items)} findings, Total: {meta['total']}")
                return True
                
        except Exception as e:
            self.log_result("Reconciliation Findings Endpoint", False, f"Exception: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run the complete LEDGER-OPS-001 reconciliation test suite"""
        print("🚀 Starting LEDGER-OPS-001 Reconciliation API Test Suite...")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 80)
        
        # Setup
        if not await self.setup_auth():
            print("\n❌ Authentication setup failed. Cannot proceed with tests.")
            return False
        
        # Run all tests
        test_results = []
        
        # Test 1: Reconciliation run with date parameter
        test_results.append(await self.test_reconciliation_run_endpoint())
        
        # Test 2: Reconciliation summary with date parameter
        test_results.append(await self.test_reconciliation_summary_endpoint())
        
        # Test 3: Reconciliation run without date parameter
        test_results.append(await self.test_reconciliation_run_without_date())
        
        # Test 4: Reconciliation summary without date parameter
        test_results.append(await self.test_reconciliation_summary_without_date())
        
        # Test 5: Reconciliation findings endpoint
        test_results.append(await self.test_reconciliation_findings_endpoint())
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 LEDGER-OPS-001 TEST SUMMARY")
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
    test_suite = ReconciliationTestSuite()
    success = await test_suite.run_all_tests()
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)