#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class GameAssetsAPITester:
    def __init__(self, base_url="https://finance-hub-348.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            response = None
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Non-dict response'}")
                    return True, response_data
                except:
                    return True, response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                self.failed_tests.append({
                    "name": name,
                    "endpoint": endpoint,
                    "expected": expected_status,
                    "actual": response.status_code,
                    "response": response.text[:200]
                })
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append({
                "name": name,
                "endpoint": endpoint,
                "error": str(e)
            })
            return False, {}

    def test_game_assets_endpoints(self):
        """Test Game Assets backend endpoints as per review request"""
        print("\n🖼️ GAME ASSETS ENDPOINTS TESTS")
        
        # 1. Choose a valid game_id from GET /api/v1/games
        success_games, games_response = self.run_test("Get Games for Assets Test", "GET", "api/v1/games", 200)
        
        if not success_games or not isinstance(games_response, list) or len(games_response) == 0:
            print("❌ No games found to test assets endpoints")
            return False
        
        game_id = games_response[0].get('id')
        game_name = games_response[0].get('name', 'Unknown Game')
        print(f"✅ Using game: {game_name} (ID: {game_id})")
        
        # 2. GET /api/v1/games/{game_id}/config/assets - Expect 200 OK, assets array may be empty
        print(f"\n📊 Testing GET Assets for game {game_id}")
        success1, assets_response = self.run_test(f"Get Assets - {game_id}", "GET", f"api/v1/games/{game_id}/config/assets", 200)
        
        initial_validation = True
        if success1 and isinstance(assets_response, dict):
            print("✅ Assets GET endpoint working")
            
            # Validate response structure
            if 'assets' in assets_response:
                assets = assets_response['assets']
                print(f"✅ Assets array found with {len(assets)} items")
                if len(assets) == 0:
                    print("ℹ️  Assets array is empty (expected on first run)")
                else:
                    print(f"ℹ️  Found {len(assets)} existing assets")
            else:
                print("❌ Assets response missing 'assets' field")
                initial_validation = False
        else:
            print("❌ Failed to get assets")
            initial_validation = False
        
        # 3. POST /api/v1/games/{game_id}/config/assets/upload with multipart/form-data
        print(f"\n📤 Testing POST Asset Upload for game {game_id}")
        
        # Create a small PNG image data (1x1 pixel PNG)
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xdd\xcc\xdb\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        
        # Prepare multipart form data
        files = {
            'file': ('test_logo.png', png_data, 'image/png')
        }
        data = {
            'asset_type': 'logo',
            'language': 'tr',
            'tags': 'desktop,lobby'
        }
        
        # Test asset upload
        url = f"{self.base_url}/api/v1/games/{game_id}/config/assets/upload"
        
        self.tests_run += 1
        print(f"\n🔍 Testing Asset Upload...")
        print(f"   URL: {url}")
        
        try:
            response = requests.post(url, files=files, data=data, timeout=30)
            
            success2 = response.status_code == 200
            upload_response = None
            asset_id = None
            
            if success2:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    upload_response = response.json()
                    print(f"   Response keys: {list(upload_response.keys()) if isinstance(upload_response, dict) else 'Non-dict response'}")
                    
                    # Validate upload response structure
                    if isinstance(upload_response, dict):
                        required_fields = ['id', 'game_id', 'config_version_id', 'asset_type', 'url', 'filename', 'mime_type', 'size_bytes', 'language', 'tags', 'created_by', 'is_deleted']
                        missing_fields = [field for field in required_fields if field not in upload_response]
                        
                        if not missing_fields:
                            print("✅ Upload response structure is complete")
                            asset_id = upload_response['id']
                            print(f"   📝 Asset ID: {asset_id}")
                            print(f"   🎮 Game ID: {upload_response['game_id']}")
                            print(f"   📋 Asset Type: {upload_response['asset_type']}")
                            print(f"   🌐 Language: {upload_response['language']}")
                            print(f"   🏷️ Tags: {upload_response['tags']}")
                            print(f"   👤 Created by: {upload_response['created_by']}")
                            print(f"   🗑️ Is Deleted: {upload_response['is_deleted']}")
                            
                            # Validate specific field values
                            if upload_response.get('asset_type') == 'logo':
                                print("✅ Asset type correctly set to 'logo'")
                            else:
                                print(f"❌ Expected asset_type='logo', got '{upload_response.get('asset_type')}'")
                            
                            if upload_response.get('language') == 'tr':
                                print("✅ Language correctly set to 'tr'")
                            else:
                                print(f"❌ Expected language='tr', got '{upload_response.get('language')}'")
                            
                            if upload_response.get('is_deleted') == False:
                                print("✅ is_deleted correctly set to false")
                            else:
                                print(f"❌ Expected is_deleted=false, got '{upload_response.get('is_deleted')}'")
                        else:
                            print(f"❌ Upload response missing fields: {missing_fields}")
                except Exception as e:
                    print(f"⚠️ Error parsing upload response: {e}")
            else:
                print(f"❌ Failed - Expected 200, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                self.failed_tests.append({
                    "name": "Asset Upload",
                    "endpoint": f"api/v1/games/{game_id}/config/assets/upload",
                    "expected": 200,
                    "actual": response.status_code,
                    "response": response.text[:200]
                })
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append({
                "name": "Asset Upload",
                "endpoint": f"api/v1/games/{game_id}/config/assets/upload",
                "error": str(e)
            })
            success2 = False
        
        # 4. GET /api/v1/games/{game_id}/config/assets again - should contain the uploaded asset
        print(f"\n🔍 Testing GET Assets after upload for game {game_id}")
        success3, updated_assets_response = self.run_test(f"Get Updated Assets - {game_id}", "GET", f"api/v1/games/{game_id}/config/assets", 200)
        
        updated_validation = True
        if success3 and isinstance(updated_assets_response, dict):
            assets = updated_assets_response.get('assets', [])
            print(f"✅ Found {len(assets)} assets after upload")
            
            if len(assets) > 0:
                # Look for our uploaded asset
                uploaded_asset_found = False
                for asset in assets:
                    if asset.get('asset_type') == 'logo' and asset.get('language') == 'tr':
                        uploaded_asset_found = True
                        print("✅ Uploaded logo asset found in assets list")
                        print(f"   📝 Asset ID: {asset.get('id')}")
                        print(f"   📋 Asset Type: {asset.get('asset_type')}")
                        print(f"   🌐 Language: {asset.get('language')}")
                        break
                
                if not uploaded_asset_found:
                    print("❌ Uploaded asset not found in assets list")
                    updated_validation = False
            else:
                print("❌ No assets found after upload")
                updated_validation = False
        else:
            print("❌ Failed to get updated assets")
            updated_validation = False
        
        # 5. Validation negative cases for upload
        print(f"\n❌ Testing Asset Upload Validation (Negative Cases)")
        
        # Missing file
        print("Testing missing file...")
        url_missing_file = f"{self.base_url}/api/v1/games/{game_id}/config/assets/upload"
        try:
            response_missing = requests.post(url_missing_file, data={'asset_type': 'logo'}, timeout=30)
            success4 = response_missing.status_code == 400
            if success4:
                try:
                    error_response = response_missing.json()
                    if error_response.get('error_code') == 'ASSET_UPLOAD_FAILED' and 'missing_file' in error_response.get('details', {}).get('reason', ''):
                        print("✅ Missing file validation working correctly")
                    else:
                        print(f"❌ Unexpected error response for missing file: {error_response}")
                        success4 = False
                except:
                    print(f"❌ Invalid JSON response for missing file: {response_missing.text}")
                    success4 = False
            else:
                print(f"❌ Expected 400 for missing file, got {response_missing.status_code}")
        except Exception as e:
            print(f"❌ Error testing missing file: {e}")
            success4 = False
        
        # Invalid asset_type
        print("Testing invalid asset_type...")
        files_invalid_type = {'file': ('test.png', png_data, 'image/png')}
        data_invalid_type = {'asset_type': 'unknown'}
        try:
            response_invalid_type = requests.post(url, files=files_invalid_type, data=data_invalid_type, timeout=30)
            success5 = response_invalid_type.status_code == 400
            if success5:
                try:
                    error_response = response_invalid_type.json()
                    if error_response.get('error_code') == 'ASSET_UPLOAD_FAILED' and 'invalid_type' in error_response.get('details', {}).get('reason', ''):
                        print("✅ Invalid asset_type validation working correctly")
                    else:
                        print(f"❌ Unexpected error response for invalid type: {error_response}")
                        success5 = False
                except:
                    print(f"❌ Invalid JSON response for invalid type: {response_invalid_type.text}")
                    success5 = False
            else:
                print(f"❌ Expected 400 for invalid asset_type, got {response_invalid_type.status_code}")
        except Exception as e:
            print(f"❌ Error testing invalid asset_type: {e}")
            success5 = False
        
        # Unsupported mime type
        print("Testing unsupported mime type...")
        files_invalid_mime = {'file': ('test.pdf', b'%PDF-1.4', 'application/pdf')}
        data_invalid_mime = {'asset_type': 'logo'}
        try:
            response_invalid_mime = requests.post(url, files=files_invalid_mime, data=data_invalid_mime, timeout=30)
            success6 = response_invalid_mime.status_code == 400
            if success6:
                try:
                    error_response = response_invalid_mime.json()
                    if (error_response.get('error_code') == 'ASSET_UPLOAD_FAILED' and 
                        'unsupported_mime_type' in error_response.get('details', {}).get('reason', '') and
                        'application/pdf' in str(error_response.get('details', {}))):
                        print("✅ Unsupported mime type validation working correctly")
                    else:
                        print(f"❌ Unexpected error response for invalid mime: {error_response}")
                        success6 = False
                except:
                    print(f"❌ Invalid JSON response for invalid mime: {response_invalid_mime.text}")
                    success6 = False
            else:
                print(f"❌ Expected 400 for unsupported mime type, got {response_invalid_mime.status_code}")
        except Exception as e:
            print(f"❌ Error testing unsupported mime type: {e}")
            success6 = False
        
        validation_tests_passed = success4 and success5 and success6
        if validation_tests_passed:
            print("✅ All validation negative cases passed")
        else:
            print("❌ Some validation tests failed")
        
        # 6. DELETE /api/v1/games/{game_id}/config/assets/{asset_id}
        delete_success = True
        if asset_id:
            print(f"\n🗑️ Testing DELETE Asset for game {game_id}, asset {asset_id}")
            success7, delete_response = self.run_test(f"Delete Asset - {asset_id}", "DELETE", f"api/v1/games/{game_id}/config/assets/{asset_id}", 200)
            
            if success7 and isinstance(delete_response, dict):
                if delete_response.get('message') == 'Asset deleted':
                    print("✅ Asset deletion successful")
                else:
                    print(f"❌ Unexpected delete response: {delete_response}")
                    delete_success = False
            else:
                print("❌ Failed to delete asset")
                delete_success = False
        else:
            print("⚠️ No asset ID available for deletion test")
            success7 = True  # Skip if no asset was created
        
        # 7. GET assets again to verify deletion (asset should not be in list due to is_deleted flag)
        if asset_id:
            print(f"\n🔍 Testing GET Assets after deletion for game {game_id}")
            success8, final_assets_response = self.run_test(f"Get Assets After Deletion - {game_id}", "GET", f"api/v1/games/{game_id}/config/assets", 200)
            
            deletion_verification = True
            if success8 and isinstance(final_assets_response, dict):
                assets = final_assets_response.get('assets', [])
                
                # Check that our deleted asset is not in the list
                deleted_asset_found = False
                for asset in assets:
                    if asset.get('id') == asset_id:
                        deleted_asset_found = True
                        break
                
                if not deleted_asset_found:
                    print("✅ Deleted asset not found in assets list (is_deleted flag honored)")
                else:
                    print("❌ Deleted asset still appears in assets list")
                    deletion_verification = False
            else:
                print("❌ Failed to get assets after deletion")
                deletion_verification = False
        else:
            success8 = True
            deletion_verification = True
        
        # 8. GET /api/v1/games/{game_id}/config/logs to verify asset actions
        print(f"\n📋 Testing Game Logs for Asset Actions")
        success9, logs_response = self.run_test(f"Get Game Logs for Assets - {game_id}", "GET", f"api/v1/games/{game_id}/config/logs?limit=20", 200)
        
        logs_validation = True
        if success9 and isinstance(logs_response, dict):
            items = logs_response.get('items', [])
            print(f"✅ Found {len(items)} log entries")
            
            # Look for asset actions
            asset_uploaded_found = False
            asset_deleted_found = False
            
            for log in items:
                action = log.get('action', '')
                details = log.get('details', {})
                
                if action == 'asset_uploaded':
                    asset_uploaded_found = True
                    print(f"   ✅ Found asset_uploaded action")
                    print(f"      - Asset ID: {details.get('asset_id', 'N/A')}")
                    print(f"      - Asset Type: {details.get('asset_type', 'N/A')}")
                    print(f"      - Config Version ID: {details.get('config_version_id', 'N/A')}")
                    print(f"      - Game ID: {details.get('game_id', 'N/A')}")
                    print(f"      - Admin ID: {details.get('admin_id', 'N/A')}")
                    print(f"      - Request ID: {details.get('request_id', 'N/A')}")
                    print(f"      - Action Type: {details.get('action_type', 'N/A')}")
                
                elif action == 'asset_deleted':
                    asset_deleted_found = True
                    print(f"   ✅ Found asset_deleted action")
                    print(f"      - Asset ID: {details.get('asset_id', 'N/A')}")
                    print(f"      - Asset Type: {details.get('asset_type', 'N/A')}")
                    print(f"      - Config Version ID: {details.get('config_version_id', 'N/A')}")
                    print(f"      - Game ID: {details.get('game_id', 'N/A')}")
                    print(f"      - Admin ID: {details.get('admin_id', 'N/A')}")
                    print(f"      - Request ID: {details.get('request_id', 'N/A')}")
                    print(f"      - Action Type: {details.get('action_type', 'N/A')}")
            
            if asset_uploaded_found:
                print("✅ Asset uploaded action found in logs")
            else:
                print("❌ Asset uploaded action not found in logs")
                logs_validation = False
            
            if asset_id and not asset_deleted_found:
                print("❌ Asset deleted action not found in logs")
                logs_validation = False
            elif asset_id:
                print("✅ Asset deleted action found in logs")
        else:
            print("❌ Failed to get game logs")
            logs_validation = False
        
        print(f"\n📊 GAME ASSETS ENDPOINTS SUMMARY:")
        print(f"   📊 GET Assets Initial: {'✅ PASS' if success1 and initial_validation else '❌ FAIL'}")
        print(f"   📤 POST Asset Upload: {'✅ PASS' if success2 else '❌ FAIL'}")
        print(f"   🔍 GET Updated Assets: {'✅ PASS' if success3 and updated_validation else '❌ FAIL'}")
        print(f"   ❌ Validation Tests: {'✅ PASS' if validation_tests_passed else '❌ FAIL'}")
        print(f"   🗑️ DELETE Asset: {'✅ PASS' if success7 and delete_success else '❌ FAIL'}")
        print(f"   🔍 Deletion Verification: {'✅ PASS' if success8 and deletion_verification else '❌ FAIL'}")
        print(f"   📋 Logs Verification: {'✅ PASS' if success9 and logs_validation else '❌ FAIL'}")
        
        return all([
            success1 and initial_validation,
            success2,
            success3 and updated_validation,
            validation_tests_passed,
            success7 and delete_success,
            success8 and deletion_verification,
            success9 and logs_validation
        ])

def main():
    print("🖼️ Game Assets API Testing")
    print("=" * 50)
    
    tester = GameAssetsAPITester()
    
    # Run the Game Assets test
    result = tester.test_game_assets_endpoints()
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    status = "✅ PASS" if result else "❌ FAIL"
    print(f"Game Assets Endpoints: {status}")
    
    print(f"\nTotal Tests: {tester.tests_run}")
    print(f"Passed: {tester.tests_passed}")
    print(f"Failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if tester.failed_tests:
        print("\n❌ FAILED TESTS DETAILS:")
        for i, failed in enumerate(tester.failed_tests, 1):
            print(f"\n{i}. {failed['name']}")
            print(f"   Endpoint: {failed['endpoint']}")
            if 'error' in failed:
                print(f"   Error: {failed['error']}")
            else:
                print(f"   Expected: {failed['expected']}, Got: {failed['actual']}")
                print(f"   Response: {failed['response']}")
    
    return 0 if result else 1

if __name__ == "__main__":
    sys.exit(main())