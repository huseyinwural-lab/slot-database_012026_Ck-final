#!/usr/bin/env python3
"""
Backend CI Sanity Test Suite

This test suite validates the specific requirements from the CI fixes review:
1. Verify backend /api/health and /api/ready endpoints respond 200 on the running dev server
2. Verify that importing backend server module does not immediately raise ValueError for missing secrets when ENV is not staging/prod
3. Run pytest for backend/tests/test_reconciliation_runs_api.py and report if any 'Future attached to a different loop' errors occur

Tests are designed to run against the localhost backend service.
"""

import asyncio
import json
import subprocess
import sys
from typing import Dict, Any, List, Tuple
import httpx
import os

# Use localhost backend for testing as requested
BACKEND_URL = "http://localhost:8001"

class BackendCISanityTestSuite:
    def __init__(self):
        self.base_url = f"{BACKEND_URL}/api"
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
    
    async def test_health_endpoint(self) -> bool:
        """Test 1: Verify /api/health endpoint responds 200"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.base_url}/health")
                
                if response.status_code != 200:
                    self.log_result("Health Endpoint", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
                    return False
                
                data = response.json()
                status = data.get("status")
                environment = data.get("environment")
                
                if status != "healthy":
                    self.log_result("Health Endpoint", False, 
                                  f"Expected status 'healthy', got '{status}'")
                    return False
                
                self.log_result("Health Endpoint", True, 
                              f"Status: {status}, Environment: {environment}")
                return True
                
        except Exception as e:
            self.log_result("Health Endpoint", False, f"Exception: {str(e)}")
            return False
    
    async def test_ready_endpoint(self) -> bool:
        """Test 2: Verify /api/ready endpoint responds 200"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.base_url}/ready")
                
                if response.status_code != 200:
                    self.log_result("Ready Endpoint", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
                    return False
                
                data = response.json()
                status = data.get("status")
                dependencies = data.get("dependencies", {})
                
                if status != "ready":
                    self.log_result("Ready Endpoint", False, 
                                  f"Expected status 'ready', got '{status}'")
                    return False
                
                db_status = dependencies.get("database", "unknown")
                redis_status = dependencies.get("redis", "unknown")
                migrations_status = dependencies.get("migrations", "unknown")
                
                self.log_result("Ready Endpoint", True, 
                              f"Status: {status}, DB: {db_status}, Redis: {redis_status}, Migrations: {migrations_status}")
                return True
                
        except Exception as e:
            self.log_result("Ready Endpoint", False, f"Exception: {str(e)}")
            return False
    
    async def test_readiness_endpoint(self) -> bool:
        """Test 3: Verify /api/readiness endpoint responds 200 (alias for ready)"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.base_url}/readiness")
                
                if response.status_code != 200:
                    self.log_result("Readiness Endpoint", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
                    return False
                
                data = response.json()
                status = data.get("status")
                
                if status != "ready":
                    self.log_result("Readiness Endpoint", False, 
                                  f"Expected status 'ready', got '{status}'")
                    return False
                
                self.log_result("Readiness Endpoint", True, f"Status: {status}")
                return True
                
        except Exception as e:
            self.log_result("Readiness Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def test_server_import(self) -> bool:
        """Test 4: Verify importing backend server module does not raise ValueError for missing secrets"""
        try:
            # Change to backend directory and test import
            original_cwd = os.getcwd()
            os.chdir('/app/backend')
            
            # Test import in a subprocess to isolate any potential issues
            result = subprocess.run([
                sys.executable, '-c', 
                'import server; print("Import successful")'
            ], capture_output=True, text=True, timeout=30)
            
            os.chdir(original_cwd)
            
            if result.returncode != 0:
                self.log_result("Server Import", False, 
                              f"Import failed with exit code {result.returncode}. "
                              f"Stdout: {result.stdout}, Stderr: {result.stderr}")
                return False
            
            # Check for ValueError in stderr
            if "ValueError" in result.stderr:
                self.log_result("Server Import", False, 
                              f"ValueError found in stderr: {result.stderr}")
                return False
            
            self.log_result("Server Import", True, 
                          f"Import successful. Stdout: {result.stdout.strip()}")
            return True
            
        except Exception as e:
            self.log_result("Server Import", False, f"Exception: {str(e)}")
            return False
    
    def test_reconciliation_pytest(self) -> bool:
        """Test 5: Run pytest for test_reconciliation_runs_api.py and check for 'Future attached to a different loop' errors"""
        try:
            # Change to backend directory and run pytest
            original_cwd = os.getcwd()
            os.chdir('/app/backend')
            
            result = subprocess.run([
                sys.executable, '-m', 'pytest', '-q', 
                'tests/test_reconciliation_runs_api.py', '-v'
            ], capture_output=True, text=True, timeout=120)
            
            os.chdir(original_cwd)
            
            # Check if tests passed
            if result.returncode != 0:
                self.log_result("Reconciliation Pytest", False, 
                              f"Pytest failed with exit code {result.returncode}. "
                              f"Stdout: {result.stdout}, Stderr: {result.stderr}")
                return False
            
            # Check for 'Future attached to a different loop' errors
            combined_output = result.stdout + result.stderr
            if "Future attached to a different loop" in combined_output:
                self.log_result("Reconciliation Pytest", False, 
                              f"'Future attached to a different loop' error found in output: {combined_output}")
                return False
            
            # Extract test results
            lines = result.stdout.split('\n')
            test_summary = ""
            for line in lines:
                if "passed" in line and ("warning" in line or "error" in line or "failed" in line):
                    test_summary = line.strip()
                    break
            
            self.log_result("Reconciliation Pytest", True, 
                          f"All tests passed. {test_summary}")
            return True
            
        except Exception as e:
            self.log_result("Reconciliation Pytest", False, f"Exception: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run the complete CI sanity test suite"""
        print("🚀 Starting Backend CI Sanity Test Suite...")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 80)
        
        # Run all tests
        test_results = []
        
        # Test 1: Health endpoint
        test_results.append(await self.test_health_endpoint())
        
        # Test 2: Ready endpoint
        test_results.append(await self.test_ready_endpoint())
        
        # Test 3: Readiness endpoint (alias)
        test_results.append(await self.test_readiness_endpoint())
        
        # Test 4: Server import
        test_results.append(self.test_server_import())
        
        # Test 5: Reconciliation pytest
        test_results.append(self.test_reconciliation_pytest())
        
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
            print("🎉 All Backend CI sanity tests PASSED!")
            return True
        else:
            print(f"⚠️  {total - passed} test(s) failed. Review the details above.")
            return False

async def main():
    """Main test runner"""
    test_suite = BackendCISanityTestSuite()
    success = await test_suite.run_all_tests()
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)