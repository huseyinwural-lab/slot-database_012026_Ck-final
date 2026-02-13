#!/usr/bin/env python3
"""
Pre-Launch Cleanup Verification Test
Verifies that tracking code has been removed and documentation exists.
"""

import os
import re
from pathlib import Path

def test_frontend_index_html_cleanup():
    """Test that frontend/public/index.html does NOT contain posthog or emergent"""
    file_path = "/app/frontend/public/index.html"
    
    if not os.path.exists(file_path):
        return False, f"File not found: {file_path}"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read().lower()
    
    # Check for posthog references
    if 'posthog' in content:
        return False, f"Found 'posthog' reference in {file_path}"
    
    # Check for emergent references
    if 'emergent' in content:
        return False, f"Found 'emergent' reference in {file_path}"
    
    return True, f"✅ {file_path} is clean - no posthog or emergent references"

def test_frontend_player_index_html_cleanup():
    """Test that frontend-player/index.html does NOT contain posthog or emergent"""
    file_path = "/app/frontend-player/index.html"
    
    if not os.path.exists(file_path):
        return False, f"File not found: {file_path}"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read().lower()
    
    # Check for posthog references
    if 'posthog' in content:
        return False, f"Found 'posthog' reference in {file_path}"
    
    # Check for emergent references
    if 'emergent' in content:
        return False, f"Found 'emergent' reference in {file_path}"
    
    return True, f"✅ {file_path} is clean - no posthog or emergent references"

def test_feature_scope_freeze_document_exists():
    """Test that docs/release/feature_scope_freeze.md exists"""
    file_path = "/app/docs/release/feature_scope_freeze.md"
    
    if not os.path.exists(file_path):
        return False, f"Required document not found: {file_path}"
    
    # Verify it's not empty
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    
    if not content:
        return False, f"Document exists but is empty: {file_path}"
    
    # Check for expected content structure
    if "Feature Scope Freeze" not in content:
        return False, f"Document exists but doesn't appear to be a feature scope freeze document: {file_path}"
    
    return True, f"✅ {file_path} exists and contains expected content"

def run_all_tests():
    """Run all pre-launch cleanup verification tests"""
    tests = [
        ("Frontend Index HTML Cleanup", test_frontend_index_html_cleanup),
        ("Frontend Player Index HTML Cleanup", test_frontend_player_index_html_cleanup),
        ("Feature Scope Freeze Document", test_feature_scope_freeze_document_exists),
    ]
    
    results = []
    all_passed = True
    
    print("🔍 Running Pre-Launch Cleanup Verification Tests...")
    print("=" * 60)
    
    for test_name, test_func in tests:
        try:
            passed, message = test_func()
            results.append((test_name, passed, message))
            
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status}: {test_name}")
            print(f"   {message}")
            
            if not passed:
                all_passed = False
                
        except Exception as e:
            results.append((test_name, False, f"Test error: {str(e)}"))
            print(f"❌ ERROR: {test_name}")
            print(f"   Test error: {str(e)}")
            all_passed = False
    
    print("=" * 60)
    print(f"Overall Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    return all_passed, results

if __name__ == "__main__":
    success, test_results = run_all_tests()
    
    # Print summary
    print("\n📋 Test Summary:")
    for test_name, passed, message in test_results:
        status = "PASS" if passed else "FAIL"
        print(f"  {status}: {test_name}")
    
    exit(0 if success else 1)