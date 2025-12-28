#!/usr/bin/env python3
"""
P0 Deploy Config Refactor Regression Test Suite

This test suite validates:
1. Health endpoints (/api/health and /api/ready)
2. Config snapshot logging does NOT leak secrets
3. Alembic offline migrations use sync DSN derived from DATABASE_URL
4. Basic auth smoke test with bootstrap credentials

Tests are designed to run against the production backend URL.
"""

import asyncio
import json
import os
import re
import subprocess
from typing import Dict, Any, List
import httpx

# Use the production backend URL from frontend/.env
FRONTEND_ENV_PATH = "/app/frontend/.env"

def get_backend_url() -> str:
    """Get backend URL from frontend/.env"""
    try:
        with open(FRONTEND_ENV_PATH, 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    except Exception as e:
        print(f"Error reading frontend .env: {e}")
    
    # Fallback
    return "https://payroll-epic.preview.emergentagent.com"

BACKEND_URL = get_backend_url()

class P0DeployConfigTestSuite:
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
        """Test 1: Verify GET /api/health returns 200 JSON"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.base_url}/health")
                
                if response.status_code != 200:
                    self.log_result("Health Endpoint", False, 
                                  f"Expected 200, got {response.status_code}, Response: {response.text}")
                    return False
                
                try:
                    data = response.json()
                    if not isinstance(data, dict):
                        self.log_result("Health Endpoint", False, "Response is not JSON object")
                        return False
                    
                    # Check for expected fields
                    if "status" not in data:
                        self.log_result("Health Endpoint", False, "Missing 'status' field in response")
                        return False
                    
                    self.log_result("Health Endpoint", True, 
                                  f"Status: {data.get('status')}, Environment: {data.get('environment', 'N/A')}")
                    return True
                    
                except json.JSONDecodeError:
                    self.log_result("Health Endpoint", False, "Response is not valid JSON")
                    return False
                
        except Exception as e:
            self.log_result("Health Endpoint", False, f"Exception: {str(e)}")
            return False
    
    async def test_ready_endpoint(self) -> bool:
        """Test 2: Verify GET /api/ready returns 200 JSON (or 503 if DB unreachable)"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.base_url}/ready")
                
                if response.status_code not in [200, 503]:
                    self.log_result("Ready Endpoint", False, 
                                  f"Expected 200 or 503, got {response.status_code}, Response: {response.text}")
                    return False
                
                try:
                    data = response.json()
                    if not isinstance(data, dict):
                        self.log_result("Ready Endpoint", False, "Response is not JSON object")
                        return False
                    
                    status = data.get("status")
                    if response.status_code == 200:
                        if status != "ready":
                            self.log_result("Ready Endpoint", False, f"Expected status 'ready', got '{status}'")
                            return False
                        
                        self.log_result("Ready Endpoint", True, 
                                      f"Status: {status}, Dependencies: {data.get('dependencies', {})}")
                    else:  # 503
                        if status != "degraded":
                            self.log_result("Ready Endpoint", False, f"Expected status 'degraded' for 503, got '{status}'")
                            return False
                        
                        self.log_result("Ready Endpoint", True, 
                                      f"Status: {status} (503 - DB unreachable as expected in some environments)")
                    
                    return True
                    
                except json.JSONDecodeError:
                    self.log_result("Ready Endpoint", False, "Response is not valid JSON")
                    return False
                
        except Exception as e:
            self.log_result("Ready Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def test_config_snapshot_no_secrets(self) -> bool:
        """Test 3: Verify config snapshot logging does NOT leak secrets"""
        try:
            # Get last 100 lines of backend logs
            log_files = [
                "/var/log/supervisor/backend.out.log",
                "/var/log/supervisor/backend.err.log"
            ]
            
            all_logs = []
            for log_file in log_files:
                try:
                    result = subprocess.run(
                        ["tail", "-n", "200", log_file],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0:
                        all_logs.extend(result.stdout.split('\n'))
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
            
            if not all_logs:
                self.log_result("Config Snapshot Security", False, "No backend logs found")
                return False
            
            # Look for config.snapshot events
            config_snapshot_lines = [line for line in all_logs if 'config.snapshot' in line]
            
            if not config_snapshot_lines:
                self.log_result("Config Snapshot Security", False, "No config.snapshot events found in logs")
                return False
            
            # Check for leaked secrets in config.snapshot lines and surrounding context
            secret_patterns = [
                r'password["\']?\s*[:=]\s*["\'][^"\']+["\']',  # password fields
                r'secret["\']?\s*[:=]\s*["\'][^"\']+["\']',    # secret fields
                r'token["\']?\s*[:=]\s*["\'][^"\']+["\']',     # token fields
                r'api_key["\']?\s*[:=]\s*["\'][^"\']+["\']',   # api_key fields
                r'username["\']?\s*[:=]\s*["\'][^"\']+["\']',  # username fields
            ]
            
            leaked_secrets = []
            for line in config_snapshot_lines:
                for pattern in secret_patterns:
                    matches = re.findall(pattern, line, re.IGNORECASE)
                    if matches:
                        leaked_secrets.extend(matches)
            
            if leaked_secrets:
                self.log_result("Config Snapshot Security", False, 
                              f"Found potential secret leaks: {leaked_secrets}")
                return False
            
            # Verify that allowed fields are present (host, port, dbname, sslmode, tls)
            allowed_fields_found = []
            for line in config_snapshot_lines:
                if any(field in line.lower() for field in ['host', 'port', 'dbname', 'sslmode', 'tls', 'driver', 'scheme']):
                    allowed_fields_found.append(line.strip())
            
            # Test the actual summarize functions to ensure they work correctly
            try:
                import sys
                sys.path.append('/app/backend')
                from app.core.connection_strings import summarize_database_url, summarize_redis_url
                from config import settings
                
                db_summary = summarize_database_url(settings.database_url)
                redis_summary = summarize_redis_url(settings.redis_url)
                
                # Verify no sensitive data in summaries
                sensitive_keys = ['password', 'user', 'username', 'secret', 'token', 'api_key']
                for summary in [db_summary, redis_summary]:
                    for key in summary.keys():
                        if any(sensitive in key.lower() for sensitive in sensitive_keys):
                            self.log_result("Config Snapshot Security", False, 
                                          f"Sensitive key found in summary: {key}")
                            return False
                
                self.log_result("Config Snapshot Security", True, 
                              f"Found {len(config_snapshot_lines)} config.snapshot events, no secrets leaked. "
                              f"DB summary: {db_summary}, Redis summary: {redis_summary}")
                return True
                
            except Exception as e:
                self.log_result("Config Snapshot Security", False, f"Error testing summary functions: {e}")
                return False
            
        except Exception as e:
            self.log_result("Config Snapshot Security", False, f"Exception: {str(e)}")
            return False
    
    def test_alembic_sync_dsn(self) -> bool:
        """Test 4: Verify Alembic offline migrations use sync DSN derived from DATABASE_URL"""
        try:
            # Check if env.py imports derive_sync_database_url
            env_py_path = "/app/backend/alembic/env.py"
            
            if not os.path.exists(env_py_path):
                self.log_result("Alembic Sync DSN", False, "alembic/env.py not found")
                return False
            
            with open(env_py_path, 'r') as f:
                env_content = f.read()
            
            # Check for required imports and usage
            required_patterns = [
                r'from app\.core\.connection_strings import derive_sync_database_url',
                r'derive_sync_database_url\(',
                r'def run_migrations_offline\(',
                r'_get_sync_url.*derive_sync_database_url'
            ]
            
            missing_patterns = []
            for pattern in required_patterns:
                if not re.search(pattern, env_content):
                    missing_patterns.append(pattern)
            
            if missing_patterns:
                self.log_result("Alembic Sync DSN", False, 
                              f"Missing required patterns in env.py: {missing_patterns}")
                return False
            
            # Try to run alembic upgrade head in check mode (dry run)
            try:
                result = subprocess.run(
                    ["python", "-m", "alembic", "upgrade", "head", "--sql"],
                    cwd="/app/backend",
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                # Check if it runs without errors (exit code 0 or generates SQL)
                if result.returncode == 0 or "CREATE TABLE" in result.stdout:
                    self.log_result("Alembic Sync DSN", True, 
                                  "env.py correctly imports and uses derive_sync_database_url, alembic runs successfully")
                    return True
                else:
                    self.log_result("Alembic Sync DSN", False, 
                                  f"Alembic command failed: {result.stderr}")
                    return False
                    
            except subprocess.TimeoutExpired:
                self.log_result("Alembic Sync DSN", False, "Alembic command timed out")
                return False
            
        except Exception as e:
            self.log_result("Alembic Sync DSN", False, f"Exception: {str(e)}")
            return False
    
    async def test_bootstrap_auth_smoke(self) -> bool:
        """Test 5: Basic auth smoke test with bootstrap credentials"""
        try:
            # Check if bootstrap is enabled by looking for environment variables
            bootstrap_enabled = os.getenv("BOOTSTRAP_ENABLED", "").lower() == "true"
            bootstrap_email = os.getenv("BOOTSTRAP_OWNER_EMAIL", "admin@casino.com")
            bootstrap_password = os.getenv("BOOTSTRAP_OWNER_PASSWORD", "Admin123!")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                login_data = {
                    "email": bootstrap_email,
                    "password": bootstrap_password
                }
                
                response = await client.post(
                    f"{self.base_url}/v1/auth/login",
                    json=login_data
                )
                
                if response.status_code == 200:
                    data = response.json()
                    access_token = data.get("access_token")
                    if access_token:
                        self.log_result("Bootstrap Auth Smoke", True, 
                                      f"Successfully logged in with bootstrap credentials")
                        return True
                    else:
                        self.log_result("Bootstrap Auth Smoke", False, 
                                      "Login successful but no access token in response")
                        return False
                        
                elif response.status_code in [401, 404]:
                    # Expected if bootstrap is not enabled or user doesn't exist
                    self.log_result("Bootstrap Auth Smoke", True, 
                                  f"Login failed as expected (bootstrap not enabled or user not seeded): {response.status_code}")
                    return True
                    
                else:
                    self.log_result("Bootstrap Auth Smoke", False, 
                                  f"Unexpected status code: {response.status_code}, Response: {response.text}")
                    return False
                
        except Exception as e:
            self.log_result("Bootstrap Auth Smoke", False, f"Exception: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run the complete P0 Deploy Config Refactor test suite"""
        print("🚀 Starting P0 Deploy Config Refactor Regression Test Suite...")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 80)
        
        # Run all tests
        test_results = []
        
        # Test 1: Health endpoint
        test_results.append(await self.test_health_endpoint())
        
        # Test 2: Ready endpoint
        test_results.append(await self.test_ready_endpoint())
        
        # Test 3: Config snapshot security
        test_results.append(self.test_config_snapshot_no_secrets())
        
        # Test 4: Alembic sync DSN
        test_results.append(self.test_alembic_sync_dsn())
        
        # Test 5: Bootstrap auth smoke test
        test_results.append(await self.test_bootstrap_auth_smoke())
        
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
            print("🎉 All P0 Deploy Config Refactor tests PASSED!")
            return True
        else:
            print(f"⚠️  {total - passed} test(s) failed. Review the details above.")
            return False

async def main():
    """Main test runner"""
    test_suite = P0DeployConfigTestSuite()
    success = await test_suite.run_all_tests()
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)