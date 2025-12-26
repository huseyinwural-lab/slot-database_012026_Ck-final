#!/usr/bin/env python3

import requests
import sys

def test_client_upload_scenarios():
    """Test Client Upload Flow - Turkish Review Request P0-E"""
    base_url = "https://smart-robot-ui.preview.emergentagent.com"
    test_game_id = "f78ddf21-c759-4b8c-a5fb-28c90b3645ab"  # Test Slot Game (QA)
    
    print("📤 CLIENT UPLOAD FLOW TESTS - P0-E")
    print(f"🎯 Test Game: Test Slot Game (QA) - ID: {test_game_id}")
    
    # Test data
    html5_content = b"hello"
    unity_content = b"unity test content"
    
    results = []
    
    # Scenario 1: HTML5 upload with launch_url + min_version
    print(f"\n🔍 Senaryo 1: launch_url + min_version ile HTML5 upload")
    
    try:
        url = f"{base_url}/api/v1/games/{test_game_id}/client-upload"
        files = {'file': ('client1.txt', html5_content, 'text/plain')}
        data = {
            'client_type': 'html5',
            'launch_url': '/static/test-overridden.html',
            'min_version': '1.2.3'
        }
        
        response = requests.post(url, files=files, data=data, timeout=30)
        
        if response.status_code == 200:
            print("✅ Senaryo 1 - Status: 200")
            response_data = response.json()
            
            # Validate key fields
            checks = [
                (response_data.get('client_type') == 'html5', "client_type == 'html5'"),
                (response_data.get('launch_url') == '/static/test-overridden.html', "launch_url correct"),
                (response_data.get('primary_client_type') == 'html5', "primary_client_type == 'html5'"),
            ]
            
            # Check game.client_variants
            game = response_data.get('game', {})
            client_variants = game.get('client_variants', {})
            html5_variant = client_variants.get('html5', {})
            html5_extra = html5_variant.get('extra', {})
            
            checks.extend([
                (html5_variant.get('launch_url') == '/static/test-overridden.html', "game.client_variants.html5.launch_url correct"),
                (html5_extra.get('min_version') == '1.2.3', "game.client_variants.html5.extra.min_version correct"),
            ])
            
            all_passed = all(check[0] for check in checks)
            for passed, desc in checks:
                print(f"   {'✅' if passed else '❌'} {desc}")
            
            results.append(("Senaryo 1", all_passed, response.status_code))
        else:
            print(f"❌ Senaryo 1 Failed - Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            results.append(("Senaryo 1", False, response.status_code))
            
    except Exception as e:
        print(f"❌ Senaryo 1 Exception: {e}")
        results.append(("Senaryo 1", False, "Exception"))
    
    # Scenario 2: Only min_version update
    print(f"\n🔍 Senaryo 2: Sadece min_version update")
    
    try:
        url = f"{base_url}/api/v1/games/{test_game_id}/client-upload"
        files = {'file': ('client1.txt', html5_content, 'text/plain')}
        data = {
            'client_type': 'html5',
            'min_version': '2.0.0'
            # launch_url intentionally omitted
        }
        
        response = requests.post(url, files=files, data=data, timeout=30)
        
        if response.status_code == 200:
            print("✅ Senaryo 2 - Status: 200")
            response_data = response.json()
            
            # Validate that launch_url is preserved
            checks = [
                (response_data.get('launch_url') == '/static/test-overridden.html', "launch_url preserved"),
            ]
            
            # Check game.client_variants
            game = response_data.get('game', {})
            client_variants = game.get('client_variants', {})
            html5_variant = client_variants.get('html5', {})
            html5_extra = html5_variant.get('extra', {})
            
            checks.extend([
                (html5_variant.get('launch_url') == '/static/test-overridden.html', "game.client_variants.html5.launch_url preserved"),
                (html5_extra.get('min_version') == '2.0.0', "game.client_variants.html5.extra.min_version updated"),
            ])
            
            all_passed = all(check[0] for check in checks)
            for passed, desc in checks:
                print(f"   {'✅' if passed else '❌'} {desc}")
            
            results.append(("Senaryo 2", all_passed, response.status_code))
        else:
            print(f"❌ Senaryo 2 Failed - Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            results.append(("Senaryo 2", False, response.status_code))
            
    except Exception as e:
        print(f"❌ Senaryo 2 Exception: {e}")
        results.append(("Senaryo 2", False, "Exception"))
    
    # Scenario 3: Unity client upload
    print(f"\n🔍 Senaryo 3: Unity client için ayrı upload")
    
    try:
        url = f"{base_url}/api/v1/games/{test_game_id}/client-upload"
        files = {'file': ('client1.txt', unity_content, 'text/plain')}
        data = {
            'client_type': 'unity',
            'launch_url': '/static/unity-build/index.html'
        }
        
        response = requests.post(url, files=files, data=data, timeout=30)
        
        if response.status_code == 200:
            print("✅ Senaryo 3 - Status: 200")
            response_data = response.json()
            
            # Validate Unity client response
            checks = [
                (response_data.get('client_type') == 'unity', "client_type == 'unity'"),
                (response_data.get('launch_url') == '/static/unity-build/index.html', "launch_url correct"),
                (response_data.get('primary_client_type') == 'html5', "primary_client_type preserved as 'html5'"),
            ]
            
            # Check game.client_variants
            game = response_data.get('game', {})
            client_variants = game.get('client_variants', {})
            unity_variant = client_variants.get('unity', {})
            
            checks.extend([
                (unity_variant.get('launch_url') == '/static/unity-build/index.html', "game.client_variants.unity.launch_url correct"),
                (unity_variant.get('runtime') == 'unity', "game.client_variants.unity.runtime correct"),
            ])
            
            all_passed = all(check[0] for check in checks)
            for passed, desc in checks:
                print(f"   {'✅' if passed else '❌'} {desc}")
            
            results.append(("Senaryo 3", all_passed, response.status_code))
        else:
            print(f"❌ Senaryo 3 Failed - Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            results.append(("Senaryo 3", False, response.status_code))
            
    except Exception as e:
        print(f"❌ Senaryo 3 Exception: {e}")
        results.append(("Senaryo 3", False, "Exception"))
    
    # Scenario 4: Invalid client_type
    print(f"\n🔍 Senaryo 4: Geçersiz client_type")
    
    try:
        url = f"{base_url}/api/v1/games/{test_game_id}/client-upload"
        files = {'file': ('client1.txt', html5_content, 'text/plain')}
        data = {
            'client_type': 'desktop'
        }
        
        response = requests.post(url, files=files, data=data, timeout=30)
        
        if response.status_code == 400:
            print("✅ Senaryo 4 - Status: 400")
            response_data = response.json()
            
            # Validate error response
            checks = [
                (response_data.get('error_code') == 'CLIENT_UPLOAD_FAILED', "error_code correct"),
                (response_data.get('details', {}).get('reason') == 'invalid_client_type', "error reason correct"),
            ]
            
            all_passed = all(check[0] for check in checks)
            for passed, desc in checks:
                print(f"   {'✅' if passed else '❌'} {desc}")
            
            results.append(("Senaryo 4", all_passed, response.status_code))
        else:
            print(f"❌ Senaryo 4 Failed - Expected 400, got {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            results.append(("Senaryo 4", False, response.status_code))
            
    except Exception as e:
        print(f"❌ Senaryo 4 Exception: {e}")
        results.append(("Senaryo 4", False, "Exception"))
    
    # Scenario 5: Missing file
    print(f"\n🔍 Senaryo 5: Eksik file")
    
    try:
        url = f"{base_url}/api/v1/games/{test_game_id}/client-upload"
        data = {
            'client_type': 'html5'
        }
        
        response = requests.post(url, data=data, timeout=30)
        
        if response.status_code == 400:
            print("✅ Senaryo 5 - Status: 400")
            response_data = response.json()
            
            # Validate error response
            checks = [
                (response_data.get('error_code') == 'CLIENT_UPLOAD_FAILED', "error_code correct"),
                (response_data.get('details', {}).get('reason') == 'missing_file', "error reason correct"),
            ]
            
            all_passed = all(check[0] for check in checks)
            for passed, desc in checks:
                print(f"   {'✅' if passed else '❌'} {desc}")
            
            results.append(("Senaryo 5", all_passed, response.status_code))
        else:
            print(f"❌ Senaryo 5 Failed - Expected 400, got {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            results.append(("Senaryo 5", False, response.status_code))
            
    except Exception as e:
        print(f"❌ Senaryo 5 Exception: {e}")
        results.append(("Senaryo 5", False, "Exception"))
    
    # Summary
    print(f"\n📊 TEST SUMMARY")
    passed_count = sum(1 for _, passed, _ in results if passed)
    total_count = len(results)
    
    for name, passed, status in results:
        print(f"{'✅' if passed else '❌'} {name}: {'PASS' if passed else 'FAIL'} (Status: {status})")
    
    print(f"\nTotal: {passed_count}/{total_count} scenarios passed")
    
    if passed_count == total_count:
        print("\n✅ ALL CLIENT UPLOAD TESTS PASSED!")
        return True
    else:
        print("\n❌ SOME CLIENT UPLOAD TESTS FAILED!")
        return False

def main():
    success = test_client_upload_scenarios()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())