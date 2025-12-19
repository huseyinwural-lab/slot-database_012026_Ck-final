#!/usr/bin/env python3
"""
Docker Compose Frontend-Admin Build Test
Testing the specific failure reported: yarn install --frozen-lockfile fails because lockfile needs update.

This test simulates the Docker build process for frontend-admin service.
"""

import subprocess
import os
import shutil
import tempfile
import sys
from pathlib import Path

def run_command(cmd, cwd=None, capture_output=True):
    """Run a command and return result"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            cwd=cwd, 
            capture_output=capture_output,
            text=True,
            timeout=300
        )
        return {
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            'returncode': -1,
            'stdout': '',
            'stderr': 'Command timed out'
        }
    except Exception as e:
        return {
            'returncode': -1,
            'stdout': '',
            'stderr': str(e)
        }

def test_yarn_frozen_lockfile():
    """Test yarn install --frozen-lockfile in clean environment"""
    print("=== DOCKER COMPOSE FRONTEND-ADMIN BUILD SIMULATION ===")
    print("Testing: yarn install --frozen-lockfile --non-interactive")
    print()
    
    # Create temporary directory to simulate Docker build context
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"1. Creating clean build context in: {temp_dir}")
        
        # Copy package.json and yarn.lock (simulating COPY command in Dockerfile)
        frontend_dir = Path("/app/frontend")
        temp_frontend = Path(temp_dir)
        
        shutil.copy2(frontend_dir / "package.json", temp_frontend / "package.json")
        shutil.copy2(frontend_dir / "yarn.lock", temp_frontend / "yarn.lock")
        
        print("   ✓ Copied package.json and yarn.lock")
        
        # Verify files exist
        if not (temp_frontend / "yarn.lock").exists():
            print("   ❌ yarn.lock not found!")
            return False
            
        print("   ✓ yarn.lock exists")
        
        # Test yarn.lock file validity (skip integrity check as it requires existing node_modules)
        print("\n2. Testing yarn.lock file validity...")
        print("   ✓ Skipping integrity check (requires existing node_modules)")
        
        # Run the exact command from Dockerfile.prod line 9
        print("\n3. Running: yarn install --frozen-lockfile --non-interactive")
        result = run_command("yarn install --frozen-lockfile --non-interactive", cwd=temp_frontend)
        
        print(f"   Exit code: {result['returncode']}")
        if result['stdout']:
            print(f"   stdout: {result['stdout']}")
        if result['stderr']:
            print(f"   stderr: {result['stderr']}")
            
        if result['returncode'] != 0:
            print("\n   ❌ YARN INSTALL FAILED!")
            
            # Check for specific error messages
            error_output = result['stdout'] + result['stderr']
            if "lockfile" in error_output.lower() and "update" in error_output.lower():
                print("   🔍 Detected lockfile update requirement")
                
                # Try to identify the specific issue
                print("\n4. Analyzing lockfile issues...")
                
                # Check if running yarn install without --frozen-lockfile would work
                print("   Testing yarn install without --frozen-lockfile...")
                result2 = run_command("yarn install", cwd=temp_frontend)
                if result2['returncode'] == 0:
                    print("   ✓ yarn install (without --frozen-lockfile) works")
                    print("   → This indicates the lockfile needs regeneration")
                else:
                    print("   ❌ yarn install also fails")
                    
            return False
        else:
            print("\n   ✅ YARN INSTALL SUCCEEDED!")
            
            # Verify node_modules was created
            if (temp_frontend / "node_modules").exists():
                print("   ✓ node_modules directory created")
                
                # Check if eslint-plugin-react-hooks is installed correctly
                react_hooks_path = temp_frontend / "node_modules" / "eslint-plugin-react-hooks"
                if react_hooks_path.exists():
                    # Check version
                    package_json_path = react_hooks_path / "package.json"
                    if package_json_path.exists():
                        try:
                            import json
                            with open(package_json_path) as f:
                                pkg_data = json.load(f)
                                version = pkg_data.get('version', 'unknown')
                                print(f"   ✓ eslint-plugin-react-hooks installed: v{version}")
                        except:
                            print("   ⚠️ Could not read eslint-plugin-react-hooks version")
                else:
                    print("   ⚠️ eslint-plugin-react-hooks not found in node_modules")
            else:
                print("   ⚠️ node_modules directory not created")
                
            return True

def test_docker_compose_build_simulation():
    """Simulate the docker-compose build process"""
    print("\n=== DOCKER-COMPOSE BUILD SIMULATION ===")
    print("Simulating: docker compose -f docker-compose.prod.yml build frontend-admin")
    print()
    
    # Check if docker-compose.prod.yml exists
    compose_file = Path("/app/docker-compose.prod.yml")
    if not compose_file.exists():
        print("❌ docker-compose.prod.yml not found!")
        return False
        
    print("✓ docker-compose.prod.yml found")
    
    # Check frontend Dockerfile.prod
    dockerfile = Path("/app/frontend/Dockerfile.prod")
    if not dockerfile.exists():
        print("❌ frontend/Dockerfile.prod not found!")
        return False
        
    print("✓ frontend/Dockerfile.prod found")
    
    # Read and analyze Dockerfile
    with open(dockerfile) as f:
        dockerfile_content = f.read()
        
    print("\nAnalyzing Dockerfile.prod:")
    lines = dockerfile_content.split('\n')
    for i, line in enumerate(lines, 1):
        if 'yarn install --frozen-lockfile' in line:
            print(f"   Line {i}: {line.strip()}")
            
    return True

def main():
    """Main test function"""
    print("DOCKER-COMPOSE FRONTEND-ADMIN BUILD FAILURE VALIDATION")
    print("=" * 60)
    print()
    
    # Test 1: Docker compose build simulation
    success1 = test_docker_compose_build_simulation()
    
    # Test 2: Yarn frozen lockfile test
    success2 = test_yarn_frozen_lockfile()
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS:")
    print(f"Docker compose simulation: {'PASS' if success1 else 'FAIL'}")
    print(f"Yarn frozen-lockfile test: {'PASS' if success2 else 'FAIL'}")
    
    if success1 and success2:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ The yarn install --frozen-lockfile command works correctly")
        print("✅ No lockfile update is required")
        print("✅ Docker build should succeed")
        return True
    else:
        print("\n💥 TESTS FAILED!")
        if not success2:
            print("❌ yarn install --frozen-lockfile fails")
            print("❌ Lockfile needs update")
            print("❌ Docker build will fail")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)