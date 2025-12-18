#!/usr/bin/env python3
"""
STG-SecHeaders-01 Validation Test
Validates K8s security headers configuration artifacts for consistency and correctness.
"""

import yaml
import os
import re
import sys
from pathlib import Path

def test_yaml_parsing():
    """Test 1: YAML parsing for k8s/frontend-admin-security-headers-configmap.yaml and patch yaml"""
    print("=== Test 1: YAML Parsing Validation ===")
    
    configmap_path = "/app/k8s/frontend-admin-security-headers-configmap.yaml"
    patch_path = "/app/k8s/frontend-admin-security-headers.patch.yaml"
    
    results = []
    
    # Test ConfigMap YAML parsing
    try:
        with open(configmap_path, 'r') as f:
            configmap_data = yaml.safe_load(f)
        
        # Validate structure
        assert configmap_data['apiVersion'] == 'v1'
        assert configmap_data['kind'] == 'ConfigMap'
        assert configmap_data['metadata']['name'] == 'frontend-admin-security-headers'
        assert 'data' in configmap_data
        
        # Validate required data keys
        required_keys = [
            'default.conf',
            '99-security-headers.sh', 
            'security_headers_off.conf',
            'security_headers_report_only.conf',
            'security_headers_enforce.conf'
        ]
        
        for key in required_keys:
            assert key in configmap_data['data'], f"Missing required key: {key}"
        
        results.append("✅ ConfigMap YAML parsing successful - all required keys present")
        
    except Exception as e:
        results.append(f"❌ ConfigMap YAML parsing failed: {e}")
        return results
    
    # Test Patch YAML parsing
    try:
        with open(patch_path, 'r') as f:
            patch_data = yaml.safe_load(f)
        
        # Validate structure
        assert patch_data['apiVersion'] == 'apps/v1'
        assert patch_data['kind'] == 'Deployment'
        assert patch_data['metadata']['name'] == 'frontend-admin'
        
        # Validate volumes and mounts structure
        spec = patch_data['spec']['template']['spec']
        assert 'volumes' in spec
        assert 'containers' in spec
        
        results.append("✅ Patch YAML parsing successful - valid Deployment structure")
        
    except Exception as e:
        results.append(f"❌ Patch YAML parsing failed: {e}")
    
    return results

def test_selector_script_logic():
    """Test 2: Verify selector script logic for SECURITY_HEADERS_MODE"""
    print("\n=== Test 2: Selector Script Logic Validation ===")
    
    results = []
    
    try:
        configmap_path = "/app/k8s/frontend-admin-security-headers-configmap.yaml"
        with open(configmap_path, 'r') as f:
            configmap_data = yaml.safe_load(f)
        
        script_content = configmap_data['data']['99-security-headers.sh']
        
        # Test 1: Valid mode handling
        valid_modes = ['off', 'report-only', 'enforce']
        for mode in valid_modes:
            if f'case "${{MODE}}" in' in script_content and f'{mode}|' in script_content:
                results.append(f"✅ Script handles valid mode: {mode}")
            else:
                results.append(f"❌ Script missing handling for mode: {mode}")
        
        # Test 2: Invalid mode fallback
        if 'MODE="off"' in script_content and 'invalid SECURITY_HEADERS_MODE' in script_content:
            results.append("✅ Script has proper fallback for invalid modes")
        else:
            results.append("❌ Script missing invalid mode fallback")
        
        # Test 3: Source file selection logic
        if 'SRC="/etc/nginx/snippets-src/security_headers_${MODE}.conf"' in script_content:
            results.append("✅ Script correctly constructs source file path")
        else:
            results.append("❌ Script source file path construction incorrect")
        
        # Test 4: Destination file logic
        if 'DST="/etc/nginx/snippets/security_headers_active.conf"' in script_content:
            results.append("✅ Script correctly sets destination file path")
        else:
            results.append("❌ Script destination file path incorrect")
        
        # Test 5: File existence check and fallback
        if '[ ! -f "${SRC}" ]' in script_content and 'security_headers_off.conf' in script_content:
            results.append("✅ Script has proper file existence check and fallback")
        else:
            results.append("❌ Script missing file existence check or fallback")
        
        # Test 6: Copy operation
        if 'cp "${SRC}" "${DST}"' in script_content:
            results.append("✅ Script performs correct copy operation")
        else:
            results.append("❌ Script copy operation incorrect")
        
    except Exception as e:
        results.append(f"❌ Selector script validation failed: {e}")
    
    return results

def test_mount_path_conflicts():
    """Test 3: Identify mount/path conflicts (read-only vs writable)"""
    print("\n=== Test 3: Mount/Path Conflicts Analysis ===")
    
    results = []
    
    try:
        patch_path = "/app/k8s/frontend-admin-security-headers.patch.yaml"
        with open(patch_path, 'r') as f:
            patch_data = yaml.safe_load(f)
        
        container = patch_data['spec']['template']['spec']['containers'][0]
        volume_mounts = container['volumeMounts']
        
        # Analyze each mount
        mount_analysis = {}
        for mount in volume_mounts:
            path = mount['mountPath']
            readonly = mount.get('readOnly', False)
            name = mount['name']
            subpath = mount.get('subPath', 'N/A')
            
            mount_analysis[path] = {
                'readonly': readonly,
                'name': name,
                'subpath': subpath
            }
        
        # Check for conflicts
        readonly_paths = []
        writable_paths = []
        
        for path, info in mount_analysis.items():
            if info['readonly']:
                readonly_paths.append(path)
                results.append(f"✅ Read-only mount: {path} (volume: {info['name']}, subpath: {info['subpath']})")
            else:
                writable_paths.append(path)
                results.append(f"✅ Writable mount: {path} (volume: {info['name']})")
        
        # Validate expected mount structure
        expected_readonly = [
            '/etc/nginx/conf.d/default.conf',
            '/etc/nginx/snippets-src', 
            '/docker-entrypoint.d/99-security-headers.sh'
        ]
        
        expected_writable = [
            '/etc/nginx/snippets'
        ]
        
        # Check all expected readonly mounts are present and readonly
        for expected_path in expected_readonly:
            if expected_path in readonly_paths:
                results.append(f"✅ Correctly configured as read-only: {expected_path}")
            else:
                results.append(f"❌ Missing or not read-only: {expected_path}")
        
        # Check all expected writable mounts are present and writable
        for expected_path in expected_writable:
            if expected_path in writable_paths:
                results.append(f"✅ Correctly configured as writable: {expected_path}")
            else:
                results.append(f"❌ Missing or not writable: {expected_path}")
        
        # Check for path conflicts (same base path with different permissions)
        base_paths = {}
        for path in mount_analysis:
            base = os.path.dirname(path)
            if base not in base_paths:
                base_paths[base] = []
            base_paths[base].append((path, mount_analysis[path]['readonly']))
        
        conflicts_found = False
        for base, paths in base_paths.items():
            if len(paths) > 1:
                readonly_states = [readonly for _, readonly in paths]
                if len(set(readonly_states)) > 1:  # Mixed readonly states
                    results.append(f"⚠️  Potential conflict in {base}: mixed readonly states")
                    conflicts_found = True
        
        if not conflicts_found:
            results.append("✅ No mount path conflicts detected")
        
    except Exception as e:
        results.append(f"❌ Mount path analysis failed: {e}")
    
    return results

def test_hsts_csp_configuration():
    """Test 4: Confirm HSTS max-age=300 and CSP report-only header in report-only mode"""
    print("\n=== Test 4: HSTS and CSP Configuration Validation ===")
    
    results = []
    
    try:
        configmap_path = "/app/k8s/frontend-admin-security-headers-configmap.yaml"
        with open(configmap_path, 'r') as f:
            configmap_data = yaml.safe_load(f)
        
        report_only_config = configmap_data['data']['security_headers_report_only.conf']
        
        # Test HSTS max-age=300
        hsts_pattern = r'add_header\s+Strict-Transport-Security\s+"max-age=300"'
        if re.search(hsts_pattern, report_only_config):
            results.append("✅ HSTS max-age=300 correctly configured in report-only mode")
        else:
            results.append("❌ HSTS max-age=300 not found or incorrect in report-only mode")
        
        # Test CSP report-only header
        csp_report_only_pattern = r'add_header\s+Content-Security-Policy-Report-Only'
        if re.search(csp_report_only_pattern, report_only_config):
            results.append("✅ CSP report-only header correctly configured")
        else:
            results.append("❌ CSP report-only header not found")
        
        # Validate CSP policy content
        expected_csp_directives = [
            "default-src 'self'",
            "base-uri 'self'", 
            "object-src 'none'",
            "frame-ancestors 'none'",
            "script-src 'self' 'report-sample'",
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: blob:",
            "font-src 'self' data:",
            "connect-src 'self' https: wss:"
        ]
        
        csp_policy_found = False
        for line in report_only_config.split('\n'):
            if 'Content-Security-Policy-Report-Only' in line:
                csp_policy_found = True
                for directive in expected_csp_directives:
                    if directive in line:
                        results.append(f"✅ CSP directive present: {directive}")
                    else:
                        results.append(f"❌ CSP directive missing: {directive}")
                break
        
        if not csp_policy_found:
            results.append("❌ CSP policy line not found in report-only config")
        
        # Validate baseline security headers are present
        baseline_headers = [
            'X-Content-Type-Options "nosniff"',
            'Referrer-Policy "strict-origin-when-cross-origin"',
            'Permissions-Policy "geolocation=(), microphone=(), camera=()"',
            'X-Frame-Options "DENY"'
        ]
        
        for header in baseline_headers:
            if header in report_only_config:
                results.append(f"✅ Baseline header present: {header}")
            else:
                results.append(f"❌ Baseline header missing: {header}")
        
        # Test enforce mode doesn't have report-only
        enforce_config = configmap_data['data']['security_headers_enforce.conf']
        if 'Content-Security-Policy-Report-Only' not in enforce_config:
            results.append("✅ Enforce mode correctly uses Content-Security-Policy (not report-only)")
        else:
            results.append("❌ Enforce mode incorrectly uses report-only CSP header")
        
        # Test off mode doesn't have CSP or HSTS
        off_config = configmap_data['data']['security_headers_off.conf']
        if 'Content-Security-Policy' not in off_config and 'Strict-Transport-Security' not in off_config:
            results.append("✅ Off mode correctly excludes CSP and HSTS headers")
        else:
            results.append("❌ Off mode incorrectly includes CSP or HSTS headers")
        
    except Exception as e:
        results.append(f"❌ HSTS/CSP configuration validation failed: {e}")
    
    return results

def test_patch_environment_configuration():
    """Test 5: Validate patch sets SECURITY_HEADERS_MODE=report-only"""
    print("\n=== Test 5: Patch Environment Configuration ===")
    
    results = []
    
    try:
        patch_path = "/app/k8s/frontend-admin-security-headers.patch.yaml"
        with open(patch_path, 'r') as f:
            patch_data = yaml.safe_load(f)
        
        container = patch_data['spec']['template']['spec']['containers'][0]
        env_vars = container.get('env', [])
        
        # Find SECURITY_HEADERS_MODE env var
        security_mode_found = False
        for env_var in env_vars:
            if env_var['name'] == 'SECURITY_HEADERS_MODE':
                security_mode_found = True
                if env_var['value'] == 'report-only':
                    results.append("✅ SECURITY_HEADERS_MODE correctly set to 'report-only' in patch")
                else:
                    results.append(f"❌ SECURITY_HEADERS_MODE set to '{env_var['value']}', expected 'report-only'")
                break
        
        if not security_mode_found:
            results.append("❌ SECURITY_HEADERS_MODE environment variable not found in patch")
        
    except Exception as e:
        results.append(f"❌ Patch environment configuration validation failed: {e}")
    
    return results

def test_documentation_consistency():
    """Test 6: Validate documentation consistency"""
    print("\n=== Test 6: Documentation Consistency ===")
    
    results = []
    
    try:
        doc_path = "/app/docs/ops/csp_hsts_checklist.md"
        with open(doc_path, 'r') as f:
            doc_content = f.read()
        
        # Check STG-SecHeaders-01 section exists
        if 'STG-SecHeaders-01' in doc_content:
            results.append("✅ STG-SecHeaders-01 section found in documentation")
        else:
            results.append("❌ STG-SecHeaders-01 section missing from documentation")
        
        # Check mode options documented
        if 'SECURITY_HEADERS_MODE=off|report-only|enforce' in doc_content:
            results.append("✅ Security headers mode options documented")
        else:
            results.append("❌ Security headers mode options not properly documented")
        
        # Check rollback instructions
        if 'SECURITY_HEADERS_MODE=off' in doc_content and 'rollback' in doc_content.lower():
            results.append("✅ Rollback instructions present")
        else:
            results.append("❌ Rollback instructions missing or incomplete")
        
        # Check validation commands
        if 'curl -I' in doc_content and 'content-security-policy' in doc_content.lower():
            results.append("✅ Validation commands documented")
        else:
            results.append("❌ Validation commands missing")
        
    except Exception as e:
        results.append(f"❌ Documentation consistency check failed: {e}")
    
    return results

def main():
    """Run all STG-SecHeaders-01 validation tests"""
    print("STG-SecHeaders-01: K8s UI-nginx Security Headers Validation")
    print("=" * 60)
    
    all_results = []
    
    # Run all tests
    test_functions = [
        test_yaml_parsing,
        test_selector_script_logic,
        test_mount_path_conflicts,
        test_hsts_csp_configuration,
        test_patch_environment_configuration,
        test_documentation_consistency
    ]
    
    for test_func in test_functions:
        try:
            results = test_func()
            all_results.extend(results)
        except Exception as e:
            all_results.append(f"❌ Test {test_func.__name__} failed with exception: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in all_results if result.startswith("✅"))
    failed = sum(1 for result in all_results if result.startswith("❌"))
    warnings = sum(1 for result in all_results if result.startswith("⚠️"))
    
    for result in all_results:
        print(result)
    
    print(f"\nResults: {passed} passed, {failed} failed, {warnings} warnings")
    
    # Determine ready-to-apply status
    critical_failures = [r for r in all_results if r.startswith("❌") and any(keyword in r.lower() for keyword in ['yaml', 'mode', 'hsts', 'csp', 'max-age=300'])]
    
    if not critical_failures:
        print("\n🟢 STATUS: READY-TO-APPLY")
        print("All critical validations passed. K8s manifests are consistent and ready for deployment.")
    else:
        print("\n🔴 STATUS: CORRECTIONS NEEDED")
        print("Critical issues found that must be addressed before deployment:")
        for failure in critical_failures:
            print(f"  - {failure}")
    
    return 0 if not critical_failures else 1

if __name__ == "__main__":
    sys.exit(main())