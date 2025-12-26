#!/usr/bin/env python3
"""
Focused Backend Regression Test for Review Request
Tests specific requirements from the review request:
1. Alembic baseline migration validation
2. Password policy validation  
3. P0 regression pytest execution
4. Health endpoints validation
"""

import requests
import subprocess
import os
import sys

BASE_URL = "https://smart-robot-ui.preview.emergentagent.com"

def test_alembic_baseline_migration():
    """Test 1: Validate Alembic baseline migration contains op.create_table(...) calls"""
    print("🔍 Test 1: Alembic Baseline Migration Validation")
    
    try:
        migration_file = "/app/backend/alembic/versions/24e894ecb377_baseline.py"
        if not os.path.exists(migration_file):
            print(f"❌ Migration file not found: {migration_file}")
            return False
        
        with open(migration_file, 'r') as f:
            content = f.read()
        
        # Check for op.create_table calls for core tables
        core_tables = [
            "tenant", "adminuser", "player", "transaction", 
            "chargebackcase", "reconciliationreport", "financesettings",
            "game", "gameasset", "gameconfigversion", "apikey",
            "featureflag", "auditlog", "approvalrequest", "supportticket",
            "riskrule", "contentpage", "bonus", "affiliate"
        ]
        
        found_tables = []
        for table in core_tables:
            if f'op.create_table(\n        "{table}"' in content or f"op.create_table('{table}'" in content:
                found_tables.append(table)
        
        if len(found_tables) >= 15:  # Should have most core tables
            print(f"✅ Migration contains op.create_table(...) calls for {len(found_tables)} core tables")
            print(f"   Found tables: {', '.join(found_tables[:10])}{'...' if len(found_tables) > 10 else ''}")
            return True
        else:
            print(f"❌ Migration missing too many core tables. Found: {len(found_tables)}")
            return False
            
    except Exception as e:
        print(f"❌ Alembic migration validation error: {str(e)}")
        return False

def test_password_policy_validation():
    """Test 2: Password policy validation"""
    print("🔍 Test 2: Password Policy Validation")
    
    try:
        # Test 2a: POST /api/v1/admin/create-tenant-admin without password should return 400 PASSWORD_REQUIRED
        print("   Testing create-tenant-admin without password")
        
        # First try to get a token (may fail, but we'll test the endpoint anyway)
        try:
            seed_response = requests.post(f"{BASE_URL}/api/v1/admin/seed", timeout=30)
            login_response = requests.post(f"{BASE_URL}/api/v1/auth/login", 
                json={"email": "admin@casino.com", "password": "Admin123!"}, timeout=30)
            
            if login_response.status_code == 200:
                token = login_response.json().get('access_token')
                headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
            else:
                headers = {'Content-Type': 'application/json'}
        except:
            headers = {'Content-Type': 'application/json'}
        
        payload_no_password = {
            "email": "test.tenant.admin@example.com",
            "tenant_id": "demo_renter",
            "full_name": "Test Tenant Admin"
            # No password field
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/admin/create-tenant-admin", 
                               json=payload_no_password, headers=headers, timeout=30)
        
        if response.status_code == 400:
            try:
                response_data = response.json()
                error_code = response_data.get('error_code')
                if error_code == 'PASSWORD_REQUIRED':
                    print("   ✅ create-tenant-admin without password: 400 PASSWORD_REQUIRED")
                    success_admin_password = True
                else:
                    print(f"   ❌ create-tenant-admin: Expected PASSWORD_REQUIRED, got {error_code}")
                    success_admin_password = False
            except Exception as e:
                print(f"   ❌ create-tenant-admin: Failed to parse 400 response - {str(e)}")
                success_admin_password = False
        else:
            print(f"   ❌ create-tenant-admin: Expected 400, got {response.status_code}")
            success_admin_password = False
        
        # Test 2b: POST /api/v1/auth/player/register with short password should return 400
        print("   Testing player register with short password")
        
        payload_short_password = {
            "email": "test.player@example.com",
            "username": "testplayer",
            "tenant_id": "default_casino",
            "password": "123"  # Less than 8 characters
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/auth/player/register", 
                               json=payload_short_password, timeout=30)
        
        if response.status_code == 400:
            try:
                response_data = response.json()
                detail = response_data.get('detail', '')
                if 'Password must be at least 8 characters' in detail or 'password' in detail.lower():
                    print("   ✅ player register with short password: 400 with password validation")
                    success_player_password = True
                else:
                    print(f"   ❌ player register: Expected password validation, got {detail}")
                    success_player_password = False
            except Exception as e:
                print(f"   ❌ player register: Failed to parse 400 response - {str(e)}")
                success_player_password = False
        else:
            print(f"   ❌ player register: Expected 400, got {response.status_code}")
            success_player_password = False
        
        return success_admin_password and success_player_password
        
    except Exception as e:
        print(f"❌ Password policy validation error: {str(e)}")
        return False

def test_p0_regression_pytest():
    """Test 3: Run P0 regression pytest files"""
    print("🔍 Test 3: P0 Regression Pytest Execution")
    
    try:
        # Set environment variables for tests
        env = os.environ.copy()
        env['REACT_APP_BACKEND_URL'] = BASE_URL
        env['TEST_OWNER_EMAIL'] = 'admin@casino.com'
        env['TEST_OWNER_PASSWORD'] = 'Admin123!'
        
        # Test 3a: Run test_response_dto_leaks.py
        print("   Running pytest test_response_dto_leaks.py")
        
        result_dto = subprocess.run(
            ['python', '-m', 'pytest', '/app/backend/tests/test_response_dto_leaks.py', '-v'],
            cwd='/app/backend',
            env=env,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result_dto.returncode == 0:
            print("   ✅ test_response_dto_leaks.py: PASSED")
            success_dto = True
        else:
            print("   ❌ test_response_dto_leaks.py: FAILED")
            print(f"      STDERR: {result_dto.stderr[-200:]}")
            success_dto = False
        
        # Test 3b: Run test_tenant_isolation.py
        print("   Running pytest test_tenant_isolation.py")
        
        result_isolation = subprocess.run(
            ['python', '-m', 'pytest', '/app/backend/tests/test_tenant_isolation.py', '-v'],
            cwd='/app/backend',
            env=env,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result_isolation.returncode == 0:
            print("   ✅ test_tenant_isolation.py: PASSED")
            success_isolation = True
        else:
            print("   ❌ test_tenant_isolation.py: FAILED")
            print(f"      STDERR: {result_isolation.stderr[-200:]}")
            success_isolation = False
        
        return success_dto and success_isolation
        
    except subprocess.TimeoutExpired:
        print("   ❌ Pytest execution timed out")
        return False
    except Exception as e:
        print(f"   ❌ Pytest execution error: {str(e)}")
        return False

def test_health_endpoints():
    """Test 4: Health endpoints validation"""
    print("🔍 Test 4: Health Endpoints Validation")
    
    try:
        # Test 4a: GET /api/health should return 200
        print("   Testing GET /api/health")
        
        response = requests.get(f"{BASE_URL}/api/health", timeout=30)
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                status = response_data.get('status')
                if status == 'healthy':
                    print("   ✅ /api/health: 200 OK with status='healthy'")
                    success_health = True
                else:
                    print(f"   ❌ /api/health: Expected status='healthy', got {status}")
                    success_health = False
            except Exception as e:
                print(f"   ❌ /api/health: Failed to parse response - {str(e)}")
                success_health = False
        else:
            print(f"   ❌ /api/health: Expected 200, got {response.status_code}")
            success_health = False
        
        # Test 4b: GET /api/ready should return 200
        print("   Testing GET /api/ready")
        
        response = requests.get(f"{BASE_URL}/api/ready", timeout=30)
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                status = response_data.get('status')
                if status == 'ready':
                    print("   ✅ /api/ready: 200 OK with status='ready'")
                    success_ready = True
                else:
                    print(f"   ❌ /api/ready: Expected status='ready', got {status}")
                    success_ready = False
            except Exception as e:
                print(f"   ❌ /api/ready: Failed to parse response - {str(e)}")
                success_ready = False
        else:
            print(f"   ❌ /api/ready: Expected 200, got {response.status_code}")
            success_ready = False
        
        return success_health and success_ready
        
    except Exception as e:
        print(f"❌ Health endpoints validation error: {str(e)}")
        return False

def main():
    """Main test runner for focused regression tests"""
    print("🔧 FOCUSED BACKEND REGRESSION TESTS - RELEASE HARDENING")
    print("=" * 60)
    
    results = []
    
    # Test 1: Alembic baseline migration validation
    results.append(("Alembic Baseline Migration", test_alembic_baseline_migration()))
    
    # Test 2: Password policy validation
    results.append(("Password Policy Validation", test_password_policy_validation()))
    
    # Test 3: P0 regression pytest execution
    results.append(("P0 Regression Pytest", test_p0_regression_pytest()))
    
    # Test 4: Health endpoints validation
    results.append(("Health Endpoints", test_health_endpoints()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 FINAL RESULTS:")
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} - {test_name}")
        if success:
            passed += 1
    
    print(f"\n📊 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Release hardening validation successful!")
        return 0
    else:
        print("⚠️  SOME TESTS FAILED - Review required before release")
        return 1

if __name__ == "__main__":
    sys.exit(main())