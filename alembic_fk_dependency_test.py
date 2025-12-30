#!/usr/bin/env python3
"""
Alembic FK Dependency Fix Verification Test

This test verifies that the FK ordering issue in alembic migration 
`6512f9dafb83_register_game_models_fixed_2.py` has been fixed by ensuring:

1. robotdefinition table is created before gamerobotbinding (which has FK robot_id -> robotdefinition.id)
2. gamesession and gameround tables are created before gameevent (which has FK round_id -> gameround.id)
3. alembic upgrade head works on fresh database without FK dependency errors
"""

import asyncio
import os
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path
import httpx

# Use the configured backend URL from environment
BACKEND_URL = os.getenv("REACT_APP_BACKEND_URL", "https://paymaster-11.preview.emergentagent.com")

class AlembicFKDependencyTestSuite:
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
    
    def test_alembic_upgrade_fresh_database(self) -> bool:
        """Test 1: Verify alembic upgrade head works on fresh SQLite database"""
        try:
            with tempfile.TemporaryDirectory() as tmp:
                db_path = Path(tmp) / "fresh_test.db"
                db_path.touch()  # Create empty file
                
                # Set up environment for alembic
                env = {**os.environ}
                env["PYTHONPATH"] = "/app/backend"
                env["ENV"] = "local"
                env["CI_STRICT"] = "0"
                env["DATABASE_URL"] = f"sqlite+aiosqlite:////{db_path}"
                env["SYNC_DATABASE_URL"] = f"sqlite:////{db_path}"
                
                # Run alembic upgrade head
                cmd = [sys.executable, "-m", "alembic", "-c", "alembic.ini", "upgrade", "head"]
                result = subprocess.run(
                    cmd, 
                    cwd="/app/backend", 
                    env=env, 
                    capture_output=True, 
                    text=True, 
                    timeout=60
                )
                
                if result.returncode != 0:
                    self.log_result(
                        "Alembic Upgrade Fresh Database", 
                        False, 
                        f"Exit code: {result.returncode}, STDERR: {result.stderr}, STDOUT: {result.stdout}"
                    )
                    return False
                
                # Verify database was created with expected tables
                conn = sqlite3.connect(str(db_path))
                try:
                    cursor = conn.cursor()
                    
                    # Check for alembic_version table
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'")
                    if not cursor.fetchone():
                        self.log_result("Alembic Upgrade Fresh Database", False, "alembic_version table not found")
                        return False
                    
                    # Check for game-related tables
                    required_tables = ['gamesession', 'gameround', 'gameevent', 'robotdefinition', 'gamerobotbinding']
                    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name IN ({','.join(['?' for _ in required_tables])})", required_tables)
                    found_tables = [row[0] for row in cursor.fetchall()]
                    
                    missing_tables = set(required_tables) - set(found_tables)
                    if missing_tables:
                        self.log_result(
                            "Alembic Upgrade Fresh Database", 
                            False, 
                            f"Missing tables: {missing_tables}"
                        )
                        return False
                    
                    self.log_result(
                        "Alembic Upgrade Fresh Database", 
                        True, 
                        f"Successfully created database with {len(found_tables)} game tables"
                    )
                    return True
                    
                finally:
                    conn.close()
                    
        except Exception as e:
            self.log_result("Alembic Upgrade Fresh Database", False, f"Exception: {str(e)}")
            return False
    
    def test_migration_file_table_ordering(self) -> bool:
        """Test 2: Verify the migration file has correct table creation order"""
        try:
            migration_file = "/app/backend/alembic/versions/6512f9dafb83_register_game_models_fixed_2.py"
            
            with open(migration_file, 'r') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            # Find line numbers for table creations
            robotdefinition_line = None
            gamerobotbinding_line = None
            gamesession_line = None
            gameround_line = None
            gameevent_line = None
            
            for i, line in enumerate(lines):
                if "if not table_exists('robotdefinition'):" in line:
                    robotdefinition_line = i + 1
                elif "if not table_exists('gamerobotbinding'):" in line:
                    gamerobotbinding_line = i + 1
                elif "if not table_exists('gamesession'):" in line:
                    gamesession_line = i + 1
                elif "if not table_exists('gameround'):" in line:
                    gameround_line = i + 1
                elif "if not table_exists('gameevent'):" in line:
                    gameevent_line = i + 1
            
            # Verify robotdefinition comes before gamerobotbinding
            if not robotdefinition_line or not gamerobotbinding_line:
                self.log_result(
                    "Migration File Table Ordering", 
                    False, 
                    f"Could not find robotdefinition ({robotdefinition_line}) or gamerobotbinding ({gamerobotbinding_line}) creation"
                )
                return False
            
            if robotdefinition_line >= gamerobotbinding_line:
                self.log_result(
                    "Migration File Table Ordering", 
                    False, 
                    f"robotdefinition (line {robotdefinition_line}) should come before gamerobotbinding (line {gamerobotbinding_line})"
                )
                return False
            
            # Verify gamesession and gameround come before gameevent
            if not gamesession_line or not gameround_line or not gameevent_line:
                self.log_result(
                    "Migration File Table Ordering", 
                    False, 
                    f"Could not find gamesession ({gamesession_line}), gameround ({gameround_line}), or gameevent ({gameevent_line}) creation"
                )
                return False
            
            if gamesession_line >= gameevent_line or gameround_line >= gameevent_line:
                self.log_result(
                    "Migration File Table Ordering", 
                    False, 
                    f"gamesession (line {gamesession_line}) and gameround (line {gameround_line}) should come before gameevent (line {gameevent_line})"
                )
                return False
            
            self.log_result(
                "Migration File Table Ordering", 
                True, 
                f"Correct ordering: robotdefinition (line {robotdefinition_line}) → gamerobotbinding (line {gamerobotbinding_line}), "
                f"gamesession (line {gamesession_line}) & gameround (line {gameround_line}) → gameevent (line {gameevent_line})"
            )
            return True
            
        except Exception as e:
            self.log_result("Migration File Table Ordering", False, f"Exception: {str(e)}")
            return False
    
    def test_pytest_alembic_tests(self) -> bool:
        """Test 3: Run the specific pytest tests mentioned in the review"""
        try:
            cmd = [
                sys.executable, "-m", "pytest", "-q", 
                "backend/tests/test_runtime_alembic_sqlite_smoke.py",
                "backend/tests/test_alembic_heads_guard.py"
            ]
            
            result = subprocess.run(
                cmd,
                cwd="/app",
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                self.log_result(
                    "Pytest Alembic Tests", 
                    False, 
                    f"Exit code: {result.returncode}, STDERR: {result.stderr}, STDOUT: {result.stdout}"
                )
                return False
            
            # Parse output to count passed tests
            stdout_lines = result.stdout.split('\n')
            passed_line = [line for line in stdout_lines if 'passed' in line and 'warnings' in line]
            
            if passed_line:
                self.log_result(
                    "Pytest Alembic Tests", 
                    True, 
                    f"Tests completed successfully: {passed_line[0].strip()}"
                )
            else:
                self.log_result(
                    "Pytest Alembic Tests", 
                    True, 
                    "Tests completed successfully"
                )
            return True
            
        except Exception as e:
            self.log_result("Pytest Alembic Tests", False, f"Exception: {str(e)}")
            return False
    
    async def test_backend_health_check(self) -> bool:
        """Test 4: Verify backend is healthy after migration"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.base_url}/health")
                
                if response.status_code != 200:
                    self.log_result(
                        "Backend Health Check", 
                        False, 
                        f"Status: {response.status_code}, Response: {response.text}"
                    )
                    return False
                
                data = response.json()
                status = data.get("status")
                
                if status != "healthy":
                    self.log_result(
                        "Backend Health Check", 
                        False, 
                        f"Expected 'healthy', got '{status}'"
                    )
                    return False
                
                self.log_result(
                    "Backend Health Check", 
                    True, 
                    f"Backend status: {status}, environment: {data.get('environment')}"
                )
                return True
                
        except Exception as e:
            self.log_result("Backend Health Check", False, f"Exception: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run the complete FK dependency fix verification test suite"""
        print("🚀 Starting Alembic FK Dependency Fix Verification Test Suite...")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 80)
        
        # Run all tests
        test_results = []
        
        # Test 1: Fresh database migration
        test_results.append(self.test_alembic_upgrade_fresh_database())
        
        # Test 2: Migration file ordering verification
        test_results.append(self.test_migration_file_table_ordering())
        
        # Test 3: Pytest alembic tests
        test_results.append(self.test_pytest_alembic_tests())
        
        # Test 4: Backend health check
        test_results.append(await self.test_backend_health_check())
        
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
            print("🎉 All FK dependency fix verification tests PASSED!")
            print("\n✅ VERIFIED: The alembic migration 6512f9dafb83_register_game_models_fixed_2.py")
            print("   correctly creates tables in the right order to avoid FK dependency errors:")
            print("   - robotdefinition → gamerobotbinding")
            print("   - gamesession & gameround → gameevent")
            return True
        else:
            print(f"⚠️  {total - passed} test(s) failed. Review the details above.")
            return False

async def main():
    """Main test runner"""
    test_suite = AlembicFKDependencyTestSuite()
    success = await test_suite.run_all_tests()
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)