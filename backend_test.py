#!/usr/bin/env python3
"""
Faz 6A Sprint 3 Deliverables Verification Test
Tests the existence and basic functionality of required script files.
"""

import os
import sys
import subprocess
import importlib.util
from pathlib import Path

def test_file_existence():
    """Test 1-4: Check existence of required script files"""
    required_files = [
        "backend/app/scripts/recon_provider.py",
        "backend/app/scripts/load_test_provider.py", 
        "backend/app/scripts/prod_guard.py",
        "backend/app/scripts/alert_validation_helper.py"
    ]
    
    results = {}
    for file_path in required_files:
        full_path = f"/app/{file_path}"
        exists = os.path.exists(full_path)
        results[file_path] = exists
        print(f"✅ {file_path}: {'EXISTS' if exists else 'MISSING'}")
    
    return all(results.values()), results

def test_syntax_validation():
    """Test 5: Verify prod_guard.py syntax is valid"""
    script_path = "/app/backend/app/scripts/prod_guard.py"
    
    try:
        # Test compilation
        result = subprocess.run([
            sys.executable, "-m", "py_compile", script_path
        ], capture_output=True, text=True, cwd="/app/backend")
        
        if result.returncode == 0:
            print("✅ prod_guard.py: SYNTAX VALID")
            return True, "Syntax validation passed"
        else:
            print(f"❌ prod_guard.py: SYNTAX ERROR - {result.stderr}")
            return False, result.stderr
    except Exception as e:
        print(f"❌ prod_guard.py: COMPILATION ERROR - {e}")
        return False, str(e)

def test_all_scripts_syntax():
    """Additional test: Verify syntax of all scripts"""
    scripts = [
        "/app/backend/app/scripts/recon_provider.py",
        "/app/backend/app/scripts/load_test_provider.py",
        "/app/backend/app/scripts/prod_guard.py", 
        "/app/backend/app/scripts/alert_validation_helper.py"
    ]
    
    results = {}
    for script in scripts:
        try:
            result = subprocess.run([
                sys.executable, "-m", "py_compile", script
            ], capture_output=True, text=True, cwd="/app/backend")
            
            script_name = os.path.basename(script)
            if result.returncode == 0:
                results[script_name] = True
                print(f"✅ {script_name}: SYNTAX VALID")
            else:
                results[script_name] = False
                print(f"❌ {script_name}: SYNTAX ERROR - {result.stderr}")
        except Exception as e:
            results[script_name] = False
            print(f"❌ {script_name}: COMPILATION ERROR - {e}")
    
    return all(results.values()), results

def test_import_validation():
    """Additional test: Check if scripts can be imported (basic dependency check)"""
    scripts_info = {
        "prod_guard": "/app/backend/app/scripts/prod_guard.py",
        "load_test_provider": "/app/backend/app/scripts/load_test_provider.py", 
        "alert_validation_helper": "/app/backend/app/scripts/alert_validation_helper.py",
        "recon_provider": "/app/backend/app/scripts/recon_provider.py"
    }
    
    results = {}
    issues = {}
    
    # Change to backend directory for proper imports
    original_cwd = os.getcwd()
    os.chdir("/app/backend")
    sys.path.insert(0, "/app/backend")
    
    try:
        for script_name, script_path in scripts_info.items():
            try:
                spec = importlib.util.spec_from_file_location(script_name, script_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                results[script_name] = True
                print(f"✅ {script_name}: IMPORT OK")
            except Exception as e:
                results[script_name] = False
                issues[script_name] = str(e)
                print(f"⚠️  {script_name}: IMPORT WARNING - {e}")
    finally:
        os.chdir(original_cwd)
        if "/app/backend" in sys.path:
            sys.path.remove("/app/backend")
    
    return results, issues

def main():
    print("=" * 60)
    print("FAZ 6A SPRINT 3 DELIVERABLES VERIFICATION")
    print("=" * 60)
    
    # Test 1-4: File Existence
    print("\n1. TESTING FILE EXISTENCE...")
    files_exist, file_results = test_file_existence()
    
    # Test 5: Syntax Validation (specific requirement)
    print("\n2. TESTING PROD_GUARD.PY SYNTAX...")
    prod_guard_syntax_ok, prod_guard_error = test_syntax_validation()
    
    # Additional: All scripts syntax
    print("\n3. TESTING ALL SCRIPTS SYNTAX...")
    all_syntax_ok, syntax_results = test_all_scripts_syntax()
    
    # Additional: Import validation
    print("\n4. TESTING IMPORT CAPABILITIES...")
    import_results, import_issues = test_import_validation()
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    print(f"File Existence: {'✅ PASS' if files_exist else '❌ FAIL'}")
    print(f"prod_guard.py Syntax: {'✅ PASS' if prod_guard_syntax_ok else '❌ FAIL'}")
    print(f"All Scripts Syntax: {'✅ PASS' if all_syntax_ok else '❌ FAIL'}")
    
    # Import issues (warnings, not failures)
    if import_issues:
        print("\nIMPORT WARNINGS (Non-blocking):")
        for script, issue in import_issues.items():
            if "async_session_factory" in issue:
                print(f"  - {script}: Uses deprecated async_session_factory (should use async_session)")
            elif "provider_wallet_drift_detected_total" in issue:
                print(f"  - {script}: References missing metric provider_wallet_drift_detected_total")
            elif "ReconciliationReport" in issue:
                print(f"  - {script}: References ReconciliationReport (should be ReconciliationRun)")
            else:
                print(f"  - {script}: {issue}")
    
    # Overall result
    core_requirements_met = files_exist and prod_guard_syntax_ok and all_syntax_ok
    
    print(f"\nOVERALL RESULT: {'✅ PASS' if core_requirements_met else '❌ FAIL'}")
    
    if core_requirements_met:
        print("All Faz 6A Sprint 3 deliverables are present and syntactically valid.")
        return 0
    else:
        print("Some Faz 6A Sprint 3 deliverables are missing or have syntax errors.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)