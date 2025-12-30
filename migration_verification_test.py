#!/usr/bin/env python3
"""
Migration Verification Test for T15_drift_fix_final_v2

This test verifies the specific requirements from the review request:
1. pytest tests pass
2. alembic upgrade head on fresh SQLite completes
3. Migration no longer contains 'except Exception: pass'
4. mfa_enabled default is set to sa.text('false')
5. index_exists and columns_exist guards are present
"""

import subprocess
import os
import tempfile
import sys
from pathlib import Path

class MigrationVerificationTest:
    def __init__(self):
        self.backend_dir = Path("/app/backend")
        self.migration_file = self.backend_dir / "alembic/versions/0968ae561847_t15_drift_fix_final_v2.py"
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
    
    def test_pytest_passes(self) -> bool:
        """Test 1: Verify pytest tests pass"""
        try:
            result = subprocess.run([
                "pytest", "-q", 
                "backend/tests/test_runtime_alembic_sqlite_smoke.py",
                "backend/tests/test_alembic_heads_guard.py"
            ], 
            cwd="/app",
            capture_output=True, 
            text=True,
            timeout=60
            )
            
            if result.returncode == 0:
                self.log_result("Pytest Tests", True, f"Tests passed successfully")
                return True
            else:
                self.log_result("Pytest Tests", False, f"Exit code: {result.returncode}, stderr: {result.stderr}")
                return False
                
        except Exception as e:
            self.log_result("Pytest Tests", False, f"Exception: {str(e)}")
            return False
    
    def test_alembic_upgrade_fresh_sqlite(self) -> bool:
        """Test 2: Verify alembic upgrade head works on fresh SQLite"""
        try:
            with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
                tmp_db_path = tmp_db.name
            
            try:
                # Set up environment for fresh SQLite database
                env = os.environ.copy()
                env["DATABASE_URL"] = f"sqlite+aiosqlite:///{tmp_db_path}"
                
                result = subprocess.run([
                    "alembic", "upgrade", "head"
                ], 
                cwd=self.backend_dir,
                env=env,
                capture_output=True, 
                text=True,
                timeout=60
                )
                
                if result.returncode == 0:
                    self.log_result("Alembic Upgrade Fresh SQLite", True, "Migration completed successfully")
                    return True
                else:
                    self.log_result("Alembic Upgrade Fresh SQLite", False, 
                                  f"Exit code: {result.returncode}, stderr: {result.stderr}")
                    return False
                    
            finally:
                # Clean up temporary database file
                try:
                    os.unlink(tmp_db_path)
                except:
                    pass
                    
        except Exception as e:
            self.log_result("Alembic Upgrade Fresh SQLite", False, f"Exception: {str(e)}")
            return False
    
    def test_no_exception_swallowing(self) -> bool:
        """Test 3: Verify migration no longer contains 'except Exception: pass'"""
        try:
            if not self.migration_file.exists():
                self.log_result("No Exception Swallowing", False, f"Migration file not found: {self.migration_file}")
                return False
            
            content = self.migration_file.read_text()
            
            if "except Exception: pass" in content:
                self.log_result("No Exception Swallowing", False, "Found 'except Exception: pass' in migration file")
                return False
            else:
                self.log_result("No Exception Swallowing", True, "No exception swallowing found")
                return True
                
        except Exception as e:
            self.log_result("No Exception Swallowing", False, f"Exception: {str(e)}")
            return False
    
    def test_mfa_enabled_default(self) -> bool:
        """Test 4: Verify mfa_enabled default is set to sa.text('false')"""
        try:
            if not self.migration_file.exists():
                self.log_result("MFA Enabled Default", False, f"Migration file not found: {self.migration_file}")
                return False
            
            content = self.migration_file.read_text()
            
            if "server_default=sa.text('false')" in content:
                self.log_result("MFA Enabled Default", True, "Found correct mfa_enabled default value")
                return True
            else:
                self.log_result("MFA Enabled Default", False, "sa.text('false') not found in migration file")
                return False
                
        except Exception as e:
            self.log_result("MFA Enabled Default", False, f"Exception: {str(e)}")
            return False
    
    def test_guard_functions_present(self) -> bool:
        """Test 5: Verify index_exists and columns_exist guard functions are present"""
        try:
            if not self.migration_file.exists():
                self.log_result("Guard Functions Present", False, f"Migration file not found: {self.migration_file}")
                return False
            
            content = self.migration_file.read_text()
            
            has_index_exists = "def index_exists(index_name: str, table_name: str) -> bool:" in content
            has_columns_exist = "def columns_exist(table_name: str, columns: list[str]) -> bool:" in content
            has_safe_create_index = "def safe_create_index(index_name, table_name, columns):" in content
            
            if has_index_exists and has_columns_exist and has_safe_create_index:
                self.log_result("Guard Functions Present", True, "All guard functions found")
                return True
            else:
                missing = []
                if not has_index_exists:
                    missing.append("index_exists")
                if not has_columns_exist:
                    missing.append("columns_exist")
                if not has_safe_create_index:
                    missing.append("safe_create_index")
                
                self.log_result("Guard Functions Present", False, f"Missing functions: {', '.join(missing)}")
                return False
                
        except Exception as e:
            self.log_result("Guard Functions Present", False, f"Exception: {str(e)}")
            return False
    
    def test_pg_indexes_check(self) -> bool:
        """Test 6: Verify pg_indexes check for Postgres is present"""
        try:
            if not self.migration_file.exists():
                self.log_result("Postgres Index Check", False, f"Migration file not found: {self.migration_file}")
                return False
            
            content = self.migration_file.read_text()
            
            if 'FROM pg_indexes' in content and 'dialect == "postgresql"' in content:
                self.log_result("Postgres Index Check", True, "Postgres-specific index checking found")
                return True
            else:
                self.log_result("Postgres Index Check", False, "Postgres index checking not found")
                return False
                
        except Exception as e:
            self.log_result("Postgres Index Check", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all verification tests"""
        print("🚀 Starting Migration Verification Test Suite...")
        print(f"Migration file: {self.migration_file}")
        print("=" * 80)
        
        # Run all tests
        test_results = []
        
        test_results.append(self.test_pytest_passes())
        test_results.append(self.test_alembic_upgrade_fresh_sqlite())
        test_results.append(self.test_no_exception_swallowing())
        test_results.append(self.test_mfa_enabled_default())
        test_results.append(self.test_guard_functions_present())
        test_results.append(self.test_pg_indexes_check())
        
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
            print("🎉 All migration verification tests PASSED!")
            return True
        else:
            print(f"⚠️  {total - passed} test(s) failed. Review the details above.")
            return False

def main():
    """Main test runner"""
    test_suite = MigrationVerificationTest()
    success = test_suite.run_all_tests()
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)