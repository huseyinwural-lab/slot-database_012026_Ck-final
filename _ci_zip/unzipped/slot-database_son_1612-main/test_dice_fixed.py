#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend_test import CasinoAdminAPITester

class DiceTestRunner(CasinoAdminAPITester):
    def test_dice_advanced_limits_backend_validation_fixed(self):
        """Test Dice Advanced Limits Backend Validation - Turkish Review Request"""
        print("\n🎲 DICE ADVANCED LIMITS BACKEND VALIDATION TESTS")
        
        # Ön koşul: Find Test Dice Game (Advanced Limits QA) from /api/v1/games?category=Dice
        print(f"\n🔍 Ön koşul: Finding Test Dice Game (Advanced Limits QA)")
        success_prereq, games_response = self.run_test("Get Dice Games", "GET", "api/v1/games?category=Dice", 200)
        
        dice_game_id = None
        if success_prereq:
            # Handle both list and string responses
            if isinstance(games_response, list):
                games_list = games_response
            elif isinstance(games_response, str):
                try:
                    import json
                    games_list = json.loads(games_response)
                except:
                    games_list = []
            else:
                games_list = []
            
            for game in games_list:
                if game.get('name') == "Test Dice Game (Advanced Limits QA)":
                    dice_game_id = game.get('id')
                    print(f"   🎯 Found Test Dice Game (Advanced Limits QA): ID = {dice_game_id}")
                    break
        
        if not dice_game_id:
            print("❌ Test Dice Game (Advanced Limits QA) not found in /api/v1/games?category=Dice")
            print("   Available Dice games:")
            if success_prereq and isinstance(games_response, list):
                for game in games_response:
                    print(f"   - {game.get('name', 'Unknown')} (ID: {game.get('id', 'Unknown')})")
            else:
                print("   No Dice games found or API call failed")
            return False
        
        # Senaryo 1 – Pozitif save + GET round-trip
        print(f"\n🔍 Senaryo 1: Pozitif save + GET round-trip")
        
        positive_payload = {
            "range_min": 0.0,
            "range_max": 99.99,
            "step": 0.01,
            "house_edge_percent": 1.0,
            "min_payout_multiplier": 1.01,
            "max_payout_multiplier": 990.0,
            "allow_over": True,
            "allow_under": True,
            "min_target": 1.0,
            "max_target": 98.0,
            "round_duration_seconds": 5,
            "bet_phase_seconds": 3,
            "max_win_per_bet": 200.0,
            "max_loss_per_bet": 100.0,
            "max_session_loss": 1000.0,
            "max_session_bets": 500,
            "enforcement_mode": "hard_block",
            "country_overrides": {
                "TR": {
                    "max_session_loss": 800.0,
                    "max_win_per_bet": 150.0
                }
            },
            "provably_fair_enabled": True,
            "rng_algorithm": "sha256_chain",
            "seed_rotation_interval_rounds": 20000,
            "summary": "Dice advanced limits positive test"
        }
        
        success1, save_response = self.run_test(
            f"POST dice-math positive - {dice_game_id}", 
            "POST", 
            f"api/v1/games/{dice_game_id}/config/dice-math", 
            200,
            positive_payload
        )
        
        # Validate save response structure
        save_validation_success = True
        if success1 and isinstance(save_response, dict):
            print("   🔍 Validating POST response structure:")
            
            required_fields = [
                'id', 'game_id', 'config_version_id', 'range_min', 'range_max', 'step',
                'house_edge_percent', 'min_payout_multiplier', 'max_payout_multiplier',
                'allow_over', 'allow_under', 'min_target', 'max_target',
                'round_duration_seconds', 'bet_phase_seconds', 'max_win_per_bet',
                'max_loss_per_bet', 'max_session_loss', 'max_session_bets',
                'enforcement_mode', 'country_overrides', 'provably_fair_enabled',
                'rng_algorithm', 'seed_rotation_interval_rounds', 'created_by'
            ]
            
            missing_fields = [field for field in required_fields if field not in save_response]
            if missing_fields:
                print(f"   ❌ Missing fields in POST response: {missing_fields}")
                save_validation_success = False
            else:
                print("   ✅ All required fields present in POST response")
                
                # Validate specific values
                if save_response.get('max_session_loss') == 1000.0:
                    print(f"   ✅ max_session_loss: {save_response['max_session_loss']}")
                else:
                    print(f"   ❌ max_session_loss mismatch: expected 1000.0, got {save_response.get('max_session_loss')}")
                    save_validation_success = False
                
                if save_response.get('enforcement_mode') == 'hard_block':
                    print(f"   ✅ enforcement_mode: {save_response['enforcement_mode']}")
                else:
                    print(f"   ❌ enforcement_mode mismatch: expected 'hard_block', got {save_response.get('enforcement_mode')}")
                    save_validation_success = False
                
                # Validate TR country override
                country_overrides = save_response.get('country_overrides', {})
                if 'TR' in country_overrides:
                    tr_override = country_overrides['TR']
                    if tr_override.get('max_session_loss') == 800.0 and tr_override.get('max_win_per_bet') == 150.0:
                        print(f"   ✅ TR country override: max_session_loss={tr_override['max_session_loss']}, max_win_per_bet={tr_override['max_win_per_bet']}")
                    else:
                        print(f"   ❌ TR country override values incorrect: {tr_override}")
                        save_validation_success = False
                else:
                    print(f"   ❌ TR country override missing from response")
                    save_validation_success = False
        else:
            save_validation_success = False
            print("❌ POST dice-math failed or returned invalid response")
        
        # GET round-trip verification
        success1b, get_response = self.run_test(
            f"GET dice-math round-trip - {dice_game_id}", 
            "GET", 
            f"api/v1/games/{dice_game_id}/config/dice-math", 
            200
        )
        
        get_validation_success = True
        if success1b and isinstance(get_response, dict):
            print("   🔍 Validating GET round-trip:")
            
            # Check that advanced fields are preserved
            if get_response.get('max_session_loss') == 1000.0:
                print(f"   ✅ GET max_session_loss preserved: {get_response['max_session_loss']}")
            else:
                print(f"   ❌ GET max_session_loss not preserved: expected 1000.0, got {get_response.get('max_session_loss')}")
                get_validation_success = False
            
            if get_response.get('enforcement_mode') == 'hard_block':
                print(f"   ✅ GET enforcement_mode preserved: {get_response['enforcement_mode']}")
            else:
                print(f"   ❌ GET enforcement_mode not preserved: expected 'hard_block', got {get_response.get('enforcement_mode')}")
                get_validation_success = False
            
            # Check TR override preservation
            get_country_overrides = get_response.get('country_overrides', {})
            if 'TR' in get_country_overrides:
                tr_get_override = get_country_overrides['TR']
                if tr_get_override.get('max_session_loss') == 800.0:
                    print(f"   ✅ GET TR override preserved: max_session_loss={tr_get_override['max_session_loss']}")
                else:
                    print(f"   ❌ GET TR override not preserved: {tr_get_override}")
                    get_validation_success = False
            else:
                print(f"   ❌ GET TR override missing")
                get_validation_success = False
        else:
            get_validation_success = False
            print("❌ GET dice-math round-trip failed")
        
        # Senaryo 2 – Negatif: invalid_mode
        print(f"\n🔍 Senaryo 2: Negatif - invalid enforcement_mode")
        
        invalid_mode_payload = positive_payload.copy()
        invalid_mode_payload['enforcement_mode'] = 'invalid_mode'
        
        success2, error_response2 = self.run_test(
            f"POST dice-math invalid mode - {dice_game_id}", 
            "POST", 
            f"api/v1/games/{dice_game_id}/config/dice-math", 
            400,
            invalid_mode_payload
        )
        
        validation2_success = True
        if success2 and isinstance(error_response2, dict):
            print("   🔍 Validating invalid enforcement_mode error:")
            
            error_code = error_response2.get('error_code')
            details = error_response2.get('details', {})
            field = details.get('field')
            reason = details.get('reason')
            
            if error_code == 'DICE_MATH_VALIDATION_FAILED':
                print(f"   ✅ error_code: {error_code}")
            else:
                print(f"   ❌ error_code mismatch: expected 'DICE_MATH_VALIDATION_FAILED', got '{error_code}'")
                validation2_success = False
            
            if field == 'enforcement_mode':
                print(f"   ✅ details.field: {field}")
            else:
                print(f"   ❌ details.field mismatch: expected 'enforcement_mode', got '{field}'")
                validation2_success = False
            
            if reason == 'unsupported_enforcement_mode':
                print(f"   ✅ details.reason: {reason}")
            else:
                print(f"   ❌ details.reason mismatch: expected 'unsupported_enforcement_mode', got '{reason}'")
                validation2_success = False
        else:
            validation2_success = False
            print("❌ Invalid enforcement_mode test failed to return proper 400 error")
        
        # Senaryo 3 – Negatif: max_session_loss = 0
        print(f"\n🔍 Senaryo 3: Negatif - max_session_loss = 0")
        
        zero_session_loss_payload = positive_payload.copy()
        zero_session_loss_payload['max_session_loss'] = 0
        
        success3, error_response3 = self.run_test(
            f"POST dice-math zero session loss - {dice_game_id}", 
            "POST", 
            f"api/v1/games/{dice_game_id}/config/dice-math", 
            400,
            zero_session_loss_payload
        )
        
        validation3_success = True
        if success3 and isinstance(error_response3, dict):
            print("   🔍 Validating max_session_loss = 0 error:")
            
            error_code = error_response3.get('error_code')
            details = error_response3.get('details', {})
            field = details.get('field')
            reason = details.get('reason')
            
            if error_code == 'DICE_MATH_VALIDATION_FAILED':
                print(f"   ✅ error_code: {error_code}")
            else:
                print(f"   ❌ error_code mismatch: expected 'DICE_MATH_VALIDATION_FAILED', got '{error_code}'")
                validation3_success = False
            
            if field == 'max_session_loss':
                print(f"   ✅ details.field: {field}")
            else:
                print(f"   ❌ details.field mismatch: expected 'max_session_loss', got '{field}'")
                validation3_success = False
            
            if reason == 'must_be_positive':
                print(f"   ✅ details.reason: {reason}")
            else:
                print(f"   ❌ details.reason mismatch: expected 'must_be_positive', got '{reason}'")
                validation3_success = False
        else:
            validation3_success = False
            print("❌ max_session_loss = 0 test failed to return proper 400 error")
        
        # Senaryo 4 – Negatif: invalid country code
        print(f"\n🔍 Senaryo 4: Negatif - invalid country code")
        
        invalid_country_payload = positive_payload.copy()
        invalid_country_payload['country_overrides'] = {
            "TUR": {  # Invalid 3-letter code instead of TR
                "max_session_loss": 800.0
            }
        }
        
        success4, error_response4 = self.run_test(
            f"POST dice-math invalid country - {dice_game_id}", 
            "POST", 
            f"api/v1/games/{dice_game_id}/config/dice-math", 
            400,
            invalid_country_payload
        )
        
        validation4_success = True
        if success4 and isinstance(error_response4, dict):
            print("   🔍 Validating invalid country code error:")
            
            error_code = error_response4.get('error_code')
            details = error_response4.get('details', {})
            field = details.get('field')
            reason = details.get('reason')
            
            if error_code == 'DICE_MATH_VALIDATION_FAILED':
                print(f"   ✅ error_code: {error_code}")
            else:
                print(f"   ❌ error_code mismatch: expected 'DICE_MATH_VALIDATION_FAILED', got '{error_code}'")
                validation4_success = False
            
            if field == 'country_overrides':
                print(f"   ✅ details.field: {field}")
            else:
                print(f"   ❌ details.field mismatch: expected 'country_overrides', got '{field}'")
                validation4_success = False
            
            if reason == 'invalid_country_code':
                print(f"   ✅ details.reason: {reason}")
            else:
                print(f"   ❌ details.reason mismatch: expected 'invalid_country_code', got '{reason}'")
                validation4_success = False
        else:
            validation4_success = False
            print("❌ Invalid country code test failed to return proper 400 error")
        
        # Senaryo 5 – Negatif: negatif override değeri
        print(f"\n🔍 Senaryo 5: Negatif - negative override value")
        
        negative_override_payload = positive_payload.copy()
        negative_override_payload['country_overrides'] = {
            "TR": {
                "max_session_loss": -10  # Negative value
            }
        }
        
        success5, error_response5 = self.run_test(
            f"POST dice-math negative override - {dice_game_id}", 
            "POST", 
            f"api/v1/games/{dice_game_id}/config/dice-math", 
            400,
            negative_override_payload
        )
        
        validation5_success = True
        if success5 and isinstance(error_response5, dict):
            print("   🔍 Validating negative override value error:")
            
            error_code = error_response5.get('error_code')
            details = error_response5.get('details', {})
            field = details.get('field')
            reason = details.get('reason')
            
            if error_code == 'DICE_MATH_VALIDATION_FAILED':
                print(f"   ✅ error_code: {error_code}")
            else:
                print(f"   ❌ error_code mismatch: expected 'DICE_MATH_VALIDATION_FAILED', got '{error_code}'")
                validation5_success = False
            
            if field == 'country_overrides.TR.max_session_loss':
                print(f"   ✅ details.field: {field}")
            else:
                print(f"   ❌ details.field mismatch: expected 'country_overrides.TR.max_session_loss', got '{field}'")
                validation5_success = False
            
            if reason == 'must_be_positive':
                print(f"   ✅ details.reason: {reason}")
            else:
                print(f"   ❌ details.reason mismatch: expected 'must_be_positive', got '{reason}'")
                validation5_success = False
        else:
            validation5_success = False
            print("❌ Negative override value test failed to return proper 400 error")
        
        # Overall test result
        overall_success = (success_prereq and success1 and save_validation_success and 
                          success1b and get_validation_success and success2 and validation2_success and 
                          success3 and validation3_success and success4 and validation4_success and 
                          success5 and validation5_success)
        
        if overall_success:
            print("\n✅ DICE ADVANCED LIMITS BACKEND VALIDATION - ALL TESTS PASSED")
            print("   ✅ Ön koşul: Test Dice Game (Advanced Limits QA) found")
            print("   ✅ Senaryo 1: Positive save + GET round-trip working")
            print("   ✅ Senaryo 2: Invalid enforcement_mode validation working")
            print("   ✅ Senaryo 3: max_session_loss = 0 validation working")
            print("   ✅ Senaryo 4: Invalid country code validation working")
            print("   ✅ Senaryo 5: Negative override value validation working")
        else:
            print("\n❌ DICE ADVANCED LIMITS BACKEND VALIDATION - SOME TESTS FAILED")
            if not success_prereq:
                print("   ❌ Prerequisite: Test Dice Game not found")
            if not (success1 and save_validation_success):
                print("   ❌ Senaryo 1: Positive save failed or response invalid")
            if not (success1b and get_validation_success):
                print("   ❌ Senaryo 1: GET round-trip failed")
            if not (success2 and validation2_success):
                print("   ❌ Senaryo 2: Invalid enforcement_mode validation failed")
            if not (success3 and validation3_success):
                print("   ❌ Senaryo 3: max_session_loss = 0 validation failed")
            if not (success4 and validation4_success):
                print("   ❌ Senaryo 4: Invalid country code validation failed")
            if not (success5 and validation5_success):
                print("   ❌ Senaryo 5: Negative override value validation failed")
        
        return overall_success

def main():
    print("🎲 DICE ADVANCED LIMITS BACKEND VALIDATION TEST")
    print("=" * 60)
    
    tester = DiceTestRunner()
    
    # Run the fixed dice advanced limits test
    result = tester.test_dice_advanced_limits_backend_validation_fixed()
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    status = "✅ PASS" if result else "❌ FAIL"
    print(f"Dice Advanced Limits Backend Validation: {status}")
    
    print(f"\nTotal API Calls: {tester.tests_run}")
    print(f"Passed: {tester.tests_passed}")
    print(f"Failed: {tester.tests_run - tester.tests_passed}")
    
    if tester.failed_tests:
        print("\n❌ FAILED API CALLS:")
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