#!/usr/bin/env python3
"""
P1.2 Discount Engine Backend Test Suite

This test suite validates the P1.2 Discount Engine functionality:
1. Database migrations are applied correctly
2. Discount models and schema are valid
3. Discount precedence logic works correctly
4. Ledger integration with discounts works correctly

Tests are designed to run against the configured backend service.
"""

import asyncio
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, Any, List, Tuple
import httpx
import os
import uuid
import subprocess
import re

# Use external ingress base URL from REACT_APP_BACKEND_URL
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

class P12DiscountEngineTestSuite:
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
    
    def test_database_migrations(self) -> bool:
        """Test 1: Verify database migrations are applied correctly"""
        try:
            # Check alembic current version
            result = subprocess.run(
                ["python", "-m", "alembic", "current"],
                cwd="/app/backend",
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.log_result("Database Migrations", False, f"Alembic error: {result.stderr}")
                return False
            
            # Check if discount migration is applied
            if "p1_discount_migration" not in result.stdout:
                self.log_result("Database Migrations", False, "P1 discount migration not found")
                return False
            
            self.log_result("Database Migrations", True, "P1 discount migration applied successfully")
            return True
            
        except Exception as e:
            self.log_result("Database Migrations", False, f"Exception: {str(e)}")
            return False
    
    def test_discount_schema_validation(self) -> bool:
        """Test 2: Verify discount database schema is correct"""
        try:
            import sqlite3
            conn = sqlite3.connect('/app/backend/casino.db')
            cursor = conn.cursor()
            
            # Check discounts table
            cursor.execute("PRAGMA table_info(discounts)")
            discount_columns = {row[1]: row[2] for row in cursor.fetchall()}
            
            expected_discount_columns = {
                'id': 'UUID',
                'code': 'VARCHAR',
                'description': 'VARCHAR',
                'type': 'VARCHAR(10)',
                'value': 'NUMERIC(10, 2)',
                'start_at': 'DATETIME',
                'end_at': 'DATETIME',
                'is_active': 'BOOLEAN'
            }
            
            for col, col_type in expected_discount_columns.items():
                if col not in discount_columns:
                    self.log_result("Discount Schema Validation", False, f"Missing column: {col}")
                    conn.close()
                    return False
                if discount_columns[col] != col_type:
                    self.log_result("Discount Schema Validation", False, 
                                  f"Column {col} type mismatch: expected {col_type}, got {discount_columns[col]}")
                    conn.close()
                    return False
            
            # Check discount_rules table
            cursor.execute("PRAGMA table_info(discount_rules)")
            rules_columns = {row[1]: row[2] for row in cursor.fetchall()}
            
            expected_rules_columns = {
                'id': 'UUID',
                'discount_id': 'UUID',
                'segment_type': 'VARCHAR(10)',
                'tenant_id': 'VARCHAR',
                'priority': 'INTEGER'
            }
            
            for col, col_type in expected_rules_columns.items():
                if col not in rules_columns:
                    self.log_result("Discount Schema Validation", False, f"Missing column in discount_rules: {col}")
                    conn.close()
                    return False
                if rules_columns[col] != col_type:
                    self.log_result("Discount Schema Validation", False, 
                                  f"Column {col} type mismatch in discount_rules: expected {col_type}, got {rules_columns[col]}")
                    conn.close()
                    return False
            
            conn.close()
            self.log_result("Discount Schema Validation", True, "All discount tables and columns are correctly defined")
            return True
            
        except Exception as e:
            self.log_result("Discount Schema Validation", False, f"Exception: {str(e)}")
            return False
    
    def test_discount_precedence_logic(self) -> bool:
        """Test 3: Run the discount precedence integration tests"""
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "tests/pricing/test_discount_precedence_integration.py", "-v"],
                cwd="/app/backend",
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.log_result("Discount Precedence Logic", False, f"Test failed: {result.stdout}\n{result.stderr}")
                return False
            
            # Check if all tests passed
            if "FAILED" in result.stdout:
                self.log_result("Discount Precedence Logic", False, f"Some tests failed: {result.stdout}")
                return False
            
            # Count passed tests
            passed_count = result.stdout.count("PASSED")
            if passed_count < 2:  # We expect at least 2 tests
                self.log_result("Discount Precedence Logic", False, f"Expected at least 2 tests, got {passed_count}")
                return False
            
            self.log_result("Discount Precedence Logic", True, f"All {passed_count} precedence tests passed")
            return True
            
        except Exception as e:
            self.log_result("Discount Precedence Logic", False, f"Exception: {str(e)}")
            return False
    
    def test_discount_ledger_integration(self) -> bool:
        """Test 4: Run the discount commit ledger tests"""
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "tests/pricing/test_discount_commit_ledger.py", "-v"],
                cwd="/app/backend",
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.log_result("Discount Ledger Integration", False, f"Test failed: {result.stdout}\n{result.stderr}")
                return False
            
            # Check if all tests passed
            if "FAILED" in result.stdout:
                self.log_result("Discount Ledger Integration", False, f"Some tests failed: {result.stdout}")
                return False
            
            # Count passed tests
            passed_count = result.stdout.count("PASSED")
            if passed_count < 2:  # We expect at least 2 tests
                self.log_result("Discount Ledger Integration", False, f"Expected at least 2 tests, got {passed_count}")
                return False
            
            self.log_result("Discount Ledger Integration", True, f"All {passed_count} ledger integration tests passed")
            return True
            
        except Exception as e:
            self.log_result("Discount Ledger Integration", False, f"Exception: {str(e)}")
            return False
    
    def test_discount_models_import(self) -> bool:
        """Test 5: Verify discount models can be imported and instantiated"""
        try:
            # Test importing discount models
            import sys
            sys.path.append('/app/backend')
            
            from app.models.discount import Discount, DiscountRules, DiscountTypeEnum, SegmentTypeEnum
            
            # Test creating discount instances
            now = datetime.utcnow()
            
            discount = Discount(
                code="TEST_DISCOUNT",
                description="Test discount for validation",
                type=DiscountTypeEnum.PERCENTAGE,
                value=20.0,
                start_at=now,
                is_active=True
            )
            
            rule = DiscountRules(
                discount_id=discount.id,
                segment_type=SegmentTypeEnum.INDIVIDUAL,
                tenant_id="test_tenant",
                priority=50
            )
            
            # Verify attributes
            if discount.code != "TEST_DISCOUNT":
                self.log_result("Discount Models Import", False, "Discount code not set correctly")
                return False
            
            if discount.type != DiscountTypeEnum.PERCENTAGE:
                self.log_result("Discount Models Import", False, "Discount type not set correctly")
                return False
            
            if rule.priority != 50:
                self.log_result("Discount Models Import", False, "Rule priority not set correctly")
                return False
            
            self.log_result("Discount Models Import", True, "Discount models imported and instantiated successfully")
            return True
            
        except Exception as e:
            self.log_result("Discount Models Import", False, f"Exception: {str(e)}")
            return False
    
    async def test_backend_health_check(self) -> bool:
        """Test 6: Verify backend is running and healthy"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.base_url}/health")
                
                if response.status_code != 200:
                    self.log_result("Backend Health Check", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
                    return False
                
                data = response.json()
                status = data.get("status")
                
                if status != "healthy":
                    self.log_result("Backend Health Check", False, f"Expected 'healthy', got '{status}'")
                    return False
                
                self.log_result("Backend Health Check", True, f"Backend is healthy")
                return True
                
        except Exception as e:
            self.log_result("Backend Health Check", False, f"Exception: {str(e)}")
            return False
    
    def test_combined_discount_tests(self) -> bool:
        """Test 7: Run both discount test files together to ensure no conflicts"""
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", 
                 "tests/pricing/test_discount_commit_ledger.py", 
                 "tests/pricing/test_discount_precedence_integration.py", 
                 "-v"],
                cwd="/app/backend",
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.log_result("Combined Discount Tests", False, f"Test failed: {result.stdout}\n{result.stderr}")
                return False
            
            # Check if all tests passed
            if "FAILED" in result.stdout:
                self.log_result("Combined Discount Tests", False, f"Some tests failed: {result.stdout}")
                return False
            
            # Count passed tests
            passed_count = result.stdout.count("PASSED")
            if passed_count < 4:  # We expect at least 4 tests total
                self.log_result("Combined Discount Tests", False, f"Expected at least 4 tests, got {passed_count}")
                return False
            
            self.log_result("Combined Discount Tests", True, f"All {passed_count} combined discount tests passed")
            return True
            
        except Exception as e:
            self.log_result("Combined Discount Tests", False, f"Exception: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run the complete P1.2 Discount Engine test suite"""
        print("🚀 Starting P1.2 Discount Engine Test Suite...")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 80)
        
        # Run all tests
        test_results = []
        
        # Test 1: Database migrations
        test_results.append(self.test_database_migrations())
        
        # Test 2: Schema validation
        test_results.append(self.test_discount_schema_validation())
        
        # Test 3: Discount precedence logic
        test_results.append(self.test_discount_precedence_logic())
        
        # Test 4: Discount ledger integration
        test_results.append(self.test_discount_ledger_integration())
        
        # Test 5: Model imports
        test_results.append(self.test_discount_models_import())
        
        # Test 6: Backend health check
        test_results.append(await self.test_backend_health_check())
        
        # Test 7: Combined tests
        test_results.append(self.test_combined_discount_tests())
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 P1.2 DISCOUNT ENGINE TEST SUMMARY")
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
            print("🎉 All P1.2 Discount Engine tests PASSED!")
            print("\n✅ P1.2 Discount Engine is working correctly:")
            print("   - Database migrations applied successfully")
            print("   - Discount schema is valid")
            print("   - Discount precedence logic works correctly")
            print("   - Ledger integration with discounts works correctly")
            return True
        else:
            print(f"⚠️  {total - passed} test(s) failed. Review the details above.")
            return False

async def main():
    """Main test runner"""
    suite = P12DiscountEngineTestSuite()
    success = await suite.run_all_tests()
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)