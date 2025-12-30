#!/usr/bin/env python3
"""
Postgres Migration Fix Verification Test

This test verifies the fix for the Postgres migration crash in:
backend/alembic/versions/3c4ee35573cd_t13_001_schema_drift_reset_full.py

The fix changed adminuser.mfa_enabled server_default from sa.text('0') to sa.text('false')
to avoid Postgres DatatypeMismatch.

Tests:
1. Verify the migration file contains the correct server_default value
2. Run pytest tests for alembic smoke tests
3. Test alembic upgrade head on fresh SQLite database
4. Verify the column is created with correct default behavior
"""

import asyncio
import os
import subprocess
import sqlite3
import tempfile
from pathlib import Path

class PostgresMigrationTest:
    def __init__(self):
        self.backend_dir = Path("/app/backend")
        self.migration_file = self.backend_dir / "alembic/versions/3c4ee35573cd_t13_001_schema_drift_reset_full.py"
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
    
    def test_migration_file_content(self) -> bool:
        """Test 1: Verify migration file contains correct server_default"""
        try:
            if not self.migration_file.exists():
                self.log_result("Migration File Exists", False, f"File not found: {self.migration_file}")
                return False
            
            content = self.migration_file.read_text()
            
            # Look for the specific line with the fix
            target_line = "server_default=sa.text('false')"
            if target_line not in content:
                self.log_result("Migration File Content", False, f"Expected '{target_line}' not found in migration file")
                return False
            
            # Ensure the old problematic line is not present
            old_line = "server_default=sa.text('0')"
            if old_line in content:
                self.log_result("Migration File Content", False, f"Old problematic line '{old_line}' still present")
                return False
            
            # Find the exact line number for verification
            lines = content.split('\n')
            line_number = None
            for i, line in enumerate(lines, 1):
                if target_line in line and 'mfa_enabled' in line:
                    line_number = i
                    break
            
            if line_number:
                self.log_result("Migration File Content", True, f"Found correct server_default at line {line_number}")
            else:
                self.log_result("Migration File Content", False, "Could not locate the mfa_enabled column definition")
                return False
            
            return True
            
        except Exception as e:
            self.log_result("Migration File Content", False, f"Exception: {str(e)}")
            return False
    
    def test_pytest_alembic_tests(self) -> bool:
        """Test 2: Run pytest alembic smoke tests"""
        try:
            cmd = [
                "pytest", "-q", 
                "backend/tests/test_runtime_alembic_sqlite_smoke.py",
                "backend/tests/test_alembic_heads_guard.py"
            ]
            
            result = subprocess.run(
                cmd, 
                cwd="/app", 
                capture_output=True, 
                text=True, 
                timeout=60
            )
            
            if result.returncode != 0:
                self.log_result("Pytest Alembic Tests", False, 
                              f"Exit code: {result.returncode}, stderr: {result.stderr}")
                return False
            
            # Parse output to get test count
            output_lines = result.stdout.split('\n')
            summary_line = None
            for line in output_lines:
                if "passed" in line and ("warning" in line or "error" in line or line.strip().endswith("passed")):
                    summary_line = line.strip()
                    break
            
            self.log_result("Pytest Alembic Tests", True, f"Tests passed: {summary_line}")
            return True
            
        except subprocess.TimeoutExpired:
            self.log_result("Pytest Alembic Tests", False, "Test timeout after 60 seconds")
            return False
        except Exception as e:
            self.log_result("Pytest Alembic Tests", False, f"Exception: {str(e)}")
            return False
    
    def test_alembic_upgrade_fresh_db(self) -> bool:
        """Test 3: Test alembic upgrade head on fresh SQLite database"""
        try:
            # Create temporary database file
            with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
                tmp_db_path = tmp_db.name
            
            try:
                # Set environment variable for the test database
                env = os.environ.copy()
                env['DATABASE_URL'] = f"sqlite+aiosqlite:///{tmp_db_path}"
                
                # Run alembic upgrade head
                cmd = ["alembic", "upgrade", "head"]
                result = subprocess.run(
                    cmd,
                    cwd=str(self.backend_dir),
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=60
                )
                
                if result.returncode != 0:
                    self.log_result("Alembic Upgrade Fresh DB", False, 
                                  f"Exit code: {result.returncode}, stderr: {result.stderr}")
                    return False
                
                # Verify database was created
                if not os.path.exists(tmp_db_path):
                    self.log_result("Alembic Upgrade Fresh DB", False, "Database file was not created")
                    return False
                
                # Check database size (should be non-zero)
                db_size = os.path.getsize(tmp_db_path)
                if db_size == 0:
                    self.log_result("Alembic Upgrade Fresh DB", False, "Database file is empty")
                    return False
                
                self.log_result("Alembic Upgrade Fresh DB", True, 
                              f"Database created successfully ({db_size} bytes)")
                return True
                
            finally:
                # Clean up temporary database
                if os.path.exists(tmp_db_path):
                    os.unlink(tmp_db_path)
                    
        except subprocess.TimeoutExpired:
            self.log_result("Alembic Upgrade Fresh DB", False, "Alembic upgrade timeout after 60 seconds")
            return False
        except Exception as e:
            self.log_result("Alembic Upgrade Fresh DB", False, f"Exception: {str(e)}")
            return False
    
    def test_column_default_behavior(self) -> bool:
        """Test 4: Verify mfa_enabled column default behavior"""
        try:
            # Create temporary database file
            with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
                tmp_db_path = tmp_db.name
            
            try:
                # Set environment variable for the test database
                env = os.environ.copy()
                env['DATABASE_URL'] = f"sqlite+aiosqlite:///{tmp_db_path}"
                
                # Run alembic upgrade head
                cmd = ["alembic", "upgrade", "head"]
                result = subprocess.run(
                    cmd,
                    cwd=str(self.backend_dir),
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=60
                )
                
                if result.returncode != 0:
                    self.log_result("Column Default Behavior", False, 
                                  f"Failed to create test database: {result.stderr}")
                    return False
                
                # Test the column behavior
                conn = sqlite3.connect(tmp_db_path)
                cursor = conn.cursor()
                
                try:
                    # Check if adminuser table exists
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='adminuser'")
                    if not cursor.fetchone():
                        self.log_result("Column Default Behavior", False, "adminuser table not found")
                        return False
                    
                    # Check column info
                    cursor.execute("PRAGMA table_info(adminuser)")
                    columns = cursor.fetchall()
                    
                    mfa_column = None
                    for col in columns:
                        if col[1] == 'mfa_enabled':
                            mfa_column = col
                            break
                    
                    if not mfa_column:
                        self.log_result("Column Default Behavior", False, "mfa_enabled column not found")
                        return False
                    
                    # Insert test record without specifying mfa_enabled
                    cursor.execute('''
                        INSERT INTO adminuser (
                            id, tenant_id, username, email, full_name, password_hash, 
                            role, is_platform_owner, status, is_active, failed_login_attempts, created_at
                        ) VALUES (
                            'test-id', 'test-tenant', 'testuser', 'test@example.com', 'Test User', 
                            'hash', 'admin', 0, 'active', 1, 0, datetime('now')
                        )
                    ''')
                    
                    # Check the default value
                    cursor.execute("SELECT mfa_enabled FROM adminuser WHERE id = 'test-id'")
                    result = cursor.fetchone()
                    
                    if result is None:
                        self.log_result("Column Default Behavior", False, "Failed to insert test record")
                        return False
                    
                    mfa_value = result[0]
                    
                    # Verify it's falsy (should be 0 or False)
                    if mfa_value not in [0, False]:
                        self.log_result("Column Default Behavior", False, 
                                      f"Expected falsy value, got {mfa_value} (type: {type(mfa_value)})")
                        return False
                    
                    self.log_result("Column Default Behavior", True, 
                                  f"mfa_enabled defaults to {mfa_value} (falsy: {not mfa_value})")
                    return True
                    
                finally:
                    conn.close()
                    
            finally:
                # Clean up temporary database
                if os.path.exists(tmp_db_path):
                    os.unlink(tmp_db_path)
                    
        except Exception as e:
            self.log_result("Column Default Behavior", False, f"Exception: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all verification tests"""
        print("🔍 Starting Postgres Migration Fix Verification Tests...")
        print("=" * 80)
        
        # Run all tests
        test_results = []
        
        test_results.append(self.test_migration_file_content())
        test_results.append(self.test_pytest_alembic_tests())
        test_results.append(self.test_alembic_upgrade_fresh_db())
        test_results.append(self.test_column_default_behavior())
        
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
            print("🎉 All Postgres migration fix verification tests PASSED!")
            print("\n✅ VERIFICATION COMPLETE:")
            print("   - Migration file contains correct server_default=sa.text('false')")
            print("   - Pytest alembic tests pass")
            print("   - Alembic upgrade head works on fresh SQLite database")
            print("   - mfa_enabled column defaults to falsy value as expected")
            return True
        else:
            print(f"⚠️  {total - passed} test(s) failed. Review the details above.")
            return False

async def main():
    """Main test runner"""
    test_suite = PostgresMigrationTest()
    success = await test_suite.run_all_tests()
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)