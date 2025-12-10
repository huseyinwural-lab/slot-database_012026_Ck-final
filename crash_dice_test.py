    def test_crash_dice_math_endpoints(self):
        """Test new Crash & Dice Math backend endpoints as per Turkish review request"""
        print("\n🎯 CRASH & DICE MATH ENDPOINTS TESTS")
        
        # First get games to test with
        success_games, games_response = self.run_test("Get Games for Crash/Dice Test", "GET", "api/v1/games", 200)
        
        if not success_games or not isinstance(games_response, list) or len(games_response) == 0:
            print("❌ No games found to test crash/dice endpoints")
            return False
        
        # Find or create CRASH and DICE games for testing
        crash_game_id = None
        dice_game_id = None
        non_compatible_game_id = None
        
        for game in games_response:
            core_type = game.get('core_type') or game.get('coreType')
            if core_type == 'CRASH' and not crash_game_id:
                crash_game_id = game.get('id')
            elif core_type == 'DICE' and not dice_game_id:
                dice_game_id = game.get('id')
            elif core_type not in ['CRASH', 'DICE'] and not non_compatible_game_id:
                non_compatible_game_id = game.get('id')
        
        # Create CRASH game if not exists
        if not crash_game_id:
            print("📝 Creating CRASH game for testing...")
            new_crash_game = {
                "name": "Test Crash Game",
                "provider": "Test Provider",
                "category": "Crash Games",
                "core_type": "CRASH",
                "rtp": 96.0
            }
            success_create, create_response = self.run_test("Create CRASH Game", "POST", "api/v1/games", 200, new_crash_game)
            if success_create and isinstance(create_response, dict):
                crash_game_id = create_response.get('id')
                print(f"✅ Created CRASH game: {crash_game_id}")
            else:
                print("❌ Failed to create CRASH game for testing")
                return False
        
        # Create DICE game if not exists
        if not dice_game_id:
            print("📝 Creating DICE game for testing...")
            new_dice_game = {
                "name": "Test Dice Game",
                "provider": "Test Provider", 
                "category": "Dice Games",
                "core_type": "DICE",
                "rtp": 99.0
            }
            success_create, create_response = self.run_test("Create DICE Game", "POST", "api/v1/games", 200, new_dice_game)
            if success_create and isinstance(create_response, dict):
                dice_game_id = create_response.get('id')
                print(f"✅ Created DICE game: {dice_game_id}")
            else:
                print("❌ Failed to create DICE game for testing")
                return False
        
        print(f"✅ Using CRASH game: {crash_game_id}")
        print(f"✅ Using DICE game: {dice_game_id}")
        if non_compatible_game_id:
            print(f"✅ Using non-compatible game for negative tests: {non_compatible_game_id}")
        
        # =============================================================================
        # CRASH MATH TESTS
        # =============================================================================
        print(f"\n🚀 CRASH MATH CONFIGURATION TESTS")
        
        # 1) Default GET (CRASH game) - should return default template
        print(f"\n📊 Test 1: Default GET for CRASH game")
        success1, crash_default_response = self.run_test(f"Get Crash Math Default - {crash_game_id}", "GET", f"api/v1/games/{crash_game_id}/config/crash-math", 200)
        
        crash_default_validation = True
        if success1 and isinstance(crash_default_response, dict):
            print("✅ Crash math GET endpoint working")
            
            # Validate default template values
            expected_defaults = {
                'base_rtp': 96.0,
                'volatility_profile': 'medium',
                'min_multiplier': 1.0,
                'max_multiplier': 500.0,
                'max_auto_cashout': 100.0,
                'round_duration_seconds': 12,
                'bet_phase_seconds': 6,
                'grace_period_seconds': 2,
                'provably_fair_enabled': True,
                'rng_algorithm': 'sha256_chain',
                'seed_rotation_interval_rounds': 10000,
                'config_version_id': None
            }
            
            for field, expected_value in expected_defaults.items():
                actual_value = crash_default_response.get(field)
                if actual_value == expected_value:
                    print(f"   ✅ {field}: {actual_value}")
                else:
                    print(f"   ❌ {field}: expected {expected_value}, got {actual_value}")
                    crash_default_validation = False
        else:
            print("❌ Failed to get crash math default template")
            crash_default_validation = False
        
        # 2) Non-CRASH game GET (should return 404)
        success2 = True
        if non_compatible_game_id:
            print(f"\n📊 Test 2: Non-CRASH game GET")
            success2, non_crash_response = self.run_test(f"Get Crash Math Non-CRASH Game - {non_compatible_game_id}", "GET", f"api/v1/games/{non_compatible_game_id}/config/crash-math", 404)
            
            if success2 and isinstance(non_crash_response, dict):
                error_code = non_crash_response.get('error_code')
                if error_code == 'CRASH_MATH_NOT_AVAILABLE_FOR_GAME':
                    print("✅ Non-crash game correctly returns 404 with proper error code")
                else:
                    print(f"❌ Expected error_code 'CRASH_MATH_NOT_AVAILABLE_FOR_GAME', got '{error_code}'")
                    success2 = False
        else:
            print("⚠️  No non-compatible game available for negative test")
        
        # 3) Valid POST (CRASH)
        print(f"\n📊 Test 3: Valid POST for CRASH game")
        
        valid_crash_config = {
            "base_rtp": 96.5,
            "volatility_profile": "high",
            "min_multiplier": 1.0,
            "max_multiplier": 1000.0,
            "max_auto_cashout": 50.0,
            "round_duration_seconds": 15,
            "bet_phase_seconds": 8,
            "grace_period_seconds": 3,
            "min_bet_per_round": 0.10,
            "max_bet_per_round": 100.0,
            "provably_fair_enabled": True,
            "rng_algorithm": "sha256_chain",
            "seed_rotation_interval_rounds": 5000,
            "summary": "Test crash math config via backend tests"
        }
        
        success3, crash_post_response = self.run_test(f"Create Crash Math Config - {crash_game_id}", "POST", f"api/v1/games/{crash_game_id}/config/crash-math", 200, valid_crash_config)
        
        crash_post_validation = True
        if success3 and isinstance(crash_post_response, dict):
            print("✅ Crash math config creation successful")
            
            # Validate POST response structure
            required_fields = ['id', 'game_id', 'config_version_id', 'base_rtp', 'volatility_profile', 'schema_version', 'created_by']
            missing_fields = [field for field in required_fields if field not in crash_post_response]
            
            if not missing_fields:
                print("✅ POST response structure complete")
                print(f"   📝 ID: {crash_post_response['id']}")
                print(f"   🎮 Game ID: {crash_post_response['game_id']}")
                print(f"   📊 Base RTP: {crash_post_response['base_rtp']}")
                print(f"   📋 Schema Version: {crash_post_response['schema_version']}")
                print(f"   👤 Created by: {crash_post_response['created_by']}")
                
                if crash_post_response.get('created_by') == 'current_admin':
                    print("✅ Created by correctly set to 'current_admin'")
                else:
                    print(f"❌ Expected created_by='current_admin', got '{crash_post_response.get('created_by')}'")
                    crash_post_validation = False
            else:
                print(f"❌ POST response missing fields: {missing_fields}")
                crash_post_validation = False
        else:
            print("❌ Failed to create crash math config")
            crash_post_validation = False
        
        # Verify GET after POST shows updated config
        print(f"\n🔍 Verifying GET after POST for CRASH")
        success3b, updated_crash_response = self.run_test(f"Get Updated Crash Math Config - {crash_game_id}", "GET", f"api/v1/games/{crash_game_id}/config/crash-math", 200)
        
        if success3b and isinstance(updated_crash_response, dict):
            if (updated_crash_response.get('base_rtp') == 96.5 and 
                updated_crash_response.get('volatility_profile') == 'high' and
                updated_crash_response.get('config_version_id') is not None):
                print("✅ GET after POST shows updated crash config")
            else:
                print("❌ GET after POST does not show updated crash config")
                crash_post_validation = False
        
        # 4) Validation Errors (CRASH) - Test key validation scenarios
        print(f"\n❌ Test 4: Crash Math Validation Errors")
        
        crash_validation_tests = []
        
        # 4a: base_rtp=80 (< 90)
        invalid_rtp = valid_crash_config.copy()
        invalid_rtp['base_rtp'] = 80.0
        success4a, rtp_response = self.run_test(f"Invalid RTP (80)", "POST", f"api/v1/games/{crash_game_id}/config/crash-math", 400, invalid_rtp)
        if success4a and isinstance(rtp_response, dict):
            if rtp_response.get('error_code') == 'CRASH_MATH_VALIDATION_FAILED' and rtp_response.get('details', {}).get('field') == 'base_rtp':
                print("✅ Invalid RTP validation working")
            else:
                print(f"❌ Invalid RTP validation failed: {rtp_response}")
        crash_validation_tests.append(success4a)
        
        # 4b: volatility_profile='ultra' (invalid)
        invalid_volatility = valid_crash_config.copy()
        invalid_volatility['volatility_profile'] = 'ultra'
        success4b, _ = self.run_test(f"Invalid Volatility Profile", "POST", f"api/v1/games/{crash_game_id}/config/crash-math", 400, invalid_volatility)
        crash_validation_tests.append(success4b)
        
        # 4c: min_multiplier=2.0, max_multiplier=1.5 (min >= max)
        invalid_multiplier = valid_crash_config.copy()
        invalid_multiplier['min_multiplier'] = 2.0
        invalid_multiplier['max_multiplier'] = 1.5
        success4c, _ = self.run_test(f"Invalid Multiplier Range", "POST", f"api/v1/games/{crash_game_id}/config/crash-math", 400, invalid_multiplier)
        crash_validation_tests.append(success4c)
        
        # 4d: max_multiplier=20000 (> 10000)
        invalid_max_mult = valid_crash_config.copy()
        invalid_max_mult['max_multiplier'] = 20000.0
        success4d, _ = self.run_test(f"Invalid Max Multiplier (>10000)", "POST", f"api/v1/games/{crash_game_id}/config/crash-math", 400, invalid_max_mult)
        crash_validation_tests.append(success4d)
        
        crash_validation_passed = all(crash_validation_tests)
        if crash_validation_passed:
            print("✅ Key crash validation negative cases passed (returned 400 as expected)")
        else:
            print(f"❌ Some crash validation tests failed: {sum(crash_validation_tests)}/{len(crash_validation_tests)} passed")
        
        # 5) Log Control (CRASH)
        print(f"\n📊 Test 5: Crash Math Log Verification")
        success5, crash_logs_response = self.run_test(f"Get Config Logs - {crash_game_id}", "GET", f"api/v1/games/{crash_game_id}/config/logs?limit=20", 200)
        
        crash_log_validation = True
        if success5 and isinstance(crash_logs_response, dict):
            logs = crash_logs_response.get('logs', [])
            if isinstance(logs, list):
                print(f"✅ Found {len(logs)} log entries")
                
                # Look for crash_math_saved actions
                crash_logs = [log for log in logs if log.get('action') == 'crash_math_saved']
                if crash_logs:
                    print(f"✅ Found {len(crash_logs)} crash_math_saved log entries")
                    
                    # Validate log structure
                    latest_log = crash_logs[0]
                    details = latest_log.get('details', {})
                    
                    # Check for required details fields
                    if 'old_value' in details and 'new_value' in details:
                        print("✅ Log details contain old_value and new_value")
                    else:
                        print("❌ Log details missing required fields")
                        crash_log_validation = False
                else:
                    print("❌ No crash_math_saved log entries found")
                    crash_log_validation = False
            else:
                print("❌ Logs response does not contain logs array")
                crash_log_validation = False
        else:
            print("❌ Failed to get config logs")
            crash_log_validation = False
        
        # =============================================================================
        # DICE MATH TESTS
        # =============================================================================
        print(f"\n🎲 DICE MATH CONFIGURATION TESTS")
        
        # 6) Default GET (DICE game) - should return default template
        print(f"\n📊 Test 6: Default GET for DICE game")
        success6, dice_default_response = self.run_test(f"Get Dice Math Default - {dice_game_id}", "GET", f"api/v1/games/{dice_game_id}/config/dice-math", 200)
        
        dice_default_validation = True
        if success6 and isinstance(dice_default_response, dict):
            print("✅ Dice math GET endpoint working")
            
            # Validate default template values
            expected_defaults = {
                'range_min': 0.0,
                'range_max': 99.99,
                'step': 0.01,
                'house_edge_percent': 1.0,
                'min_payout_multiplier': 1.01,
                'max_payout_multiplier': 990.0,
                'allow_over': True,
                'allow_under': True,
                'min_target': 1.0,
                'max_target': 98.0,
                'round_duration_seconds': 5,
                'bet_phase_seconds': 3,
                'provably_fair_enabled': True,
                'rng_algorithm': 'sha256_chain',
                'seed_rotation_interval_rounds': 20000,
                'config_version_id': None
            }
            
            for field, expected_value in expected_defaults.items():
                actual_value = dice_default_response.get(field)
                if actual_value == expected_value:
                    print(f"   ✅ {field}: {actual_value}")
                else:
                    print(f"   ❌ {field}: expected {expected_value}, got {actual_value}")
                    dice_default_validation = False
        else:
            print("❌ Failed to get dice math default template")
            dice_default_validation = False
        
        # 7) Non-DICE game GET (should return 404)
        success7 = True
        if non_compatible_game_id:
            print(f"\n📊 Test 7: Non-DICE game GET")
            success7, non_dice_response = self.run_test(f"Get Dice Math Non-DICE Game - {non_compatible_game_id}", "GET", f"api/v1/games/{non_compatible_game_id}/config/dice-math", 404)
            
            if success7 and isinstance(non_dice_response, dict):
                error_code = non_dice_response.get('error_code')
                if error_code == 'DICE_MATH_NOT_AVAILABLE_FOR_GAME':
                    print("✅ Non-dice game correctly returns 404 with proper error code")
                else:
                    print(f"❌ Expected error_code 'DICE_MATH_NOT_AVAILABLE_FOR_GAME', got '{error_code}'")
                    success7 = False
        else:
            print("⚠️  No non-compatible game available for negative test")
        
        # 8) Valid POST (DICE)
        print(f"\n📊 Test 8: Valid POST for DICE game")
        
        valid_dice_config = {
            "range_min": 0.0,
            "range_max": 100.0,
            "step": 0.1,
            "house_edge_percent": 2.0,
            "min_payout_multiplier": 1.1,
            "max_payout_multiplier": 500.0,
            "allow_over": True,
            "allow_under": True,
            "min_target": 5.0,
            "max_target": 95.0,
            "round_duration_seconds": 8,
            "bet_phase_seconds": 5,
            "provably_fair_enabled": True,
            "rng_algorithm": "sha256_chain",
            "seed_rotation_interval_rounds": 15000,
            "summary": "Test dice math config via backend tests"
        }
        
        success8, dice_post_response = self.run_test(f"Create Dice Math Config - {dice_game_id}", "POST", f"api/v1/games/{dice_game_id}/config/dice-math", 200, valid_dice_config)
        
        dice_post_validation = True
        if success8 and isinstance(dice_post_response, dict):
            print("✅ Dice math config creation successful")
            
            # Validate POST response structure
            required_fields = ['id', 'game_id', 'config_version_id', 'range_min', 'range_max', 'schema_version', 'created_by']
            missing_fields = [field for field in required_fields if field not in dice_post_response]
            
            if not missing_fields:
                print("✅ POST response structure complete")
                print(f"   📝 ID: {dice_post_response['id']}")
                print(f"   🎮 Game ID: {dice_post_response['game_id']}")
                print(f"   📊 Range: {dice_post_response['range_min']}-{dice_post_response['range_max']}")
                print(f"   📋 Schema Version: {dice_post_response['schema_version']}")
                print(f"   👤 Created by: {dice_post_response['created_by']}")
                
                if dice_post_response.get('created_by') == 'current_admin':
                    print("✅ Created by correctly set to 'current_admin'")
                else:
                    print(f"❌ Expected created_by='current_admin', got '{dice_post_response.get('created_by')}'")
                    dice_post_validation = False
            else:
                print(f"❌ POST response missing fields: {missing_fields}")
                dice_post_validation = False
        else:
            print("❌ Failed to create dice math config")
            dice_post_validation = False
        
        # Verify GET after POST shows updated config
        print(f"\n🔍 Verifying GET after POST for DICE")
        success8b, updated_dice_response = self.run_test(f"Get Updated Dice Math Config - {dice_game_id}", "GET", f"api/v1/games/{dice_game_id}/config/dice-math", 200)
        
        if success8b and isinstance(updated_dice_response, dict):
            if (updated_dice_response.get('house_edge_percent') == 2.0 and 
                updated_dice_response.get('step') == 0.1 and
                updated_dice_response.get('config_version_id') is not None):
                print("✅ GET after POST shows updated dice config")
            else:
                print("❌ GET after POST does not show updated dice config")
                dice_post_validation = False
        
        # 9) Validation Errors (DICE) - Test key validation scenarios
        print(f"\n❌ Test 9: Dice Math Validation Errors")
        
        dice_validation_tests = []
        
        # 9a: range_min >= range_max
        invalid_range = valid_dice_config.copy()
        invalid_range['range_min'] = 50.0
        invalid_range['range_max'] = 40.0
        success9a, _ = self.run_test(f"Invalid Range (min>=max)", "POST", f"api/v1/games/{dice_game_id}/config/dice-math", 400, invalid_range)
        dice_validation_tests.append(success9a)
        
        # 9b: step <= 0
        invalid_step = valid_dice_config.copy()
        invalid_step['step'] = 0.0
        success9b, _ = self.run_test(f"Invalid Step (<=0)", "POST", f"api/v1/games/{dice_game_id}/config/dice-math", 400, invalid_step)
        dice_validation_tests.append(success9b)
        
        # 9c: house_edge_percent > 5.0
        invalid_house_edge = valid_dice_config.copy()
        invalid_house_edge['house_edge_percent'] = 6.0
        success9c, _ = self.run_test(f"Invalid House Edge (>5)", "POST", f"api/v1/games/{dice_game_id}/config/dice-math", 400, invalid_house_edge)
        dice_validation_tests.append(success9c)
        
        # 9d: allow_over=false and allow_under=false
        invalid_allow = valid_dice_config.copy()
        invalid_allow['allow_over'] = False
        invalid_allow['allow_under'] = False
        success9d, _ = self.run_test(f"Invalid Allow Over/Under (both false)", "POST", f"api/v1/games/{dice_game_id}/config/dice-math", 400, invalid_allow)
        dice_validation_tests.append(success9d)
        
        dice_validation_passed = all(dice_validation_tests)
        if dice_validation_passed:
            print("✅ Key dice validation negative cases passed (returned 400 as expected)")
        else:
            print(f"❌ Some dice validation tests failed: {sum(dice_validation_tests)}/{len(dice_validation_tests)} passed")
        
        # 10) Log Control (DICE)
        print(f"\n📊 Test 10: Dice Math Log Verification")
        success10, dice_logs_response = self.run_test(f"Get Config Logs - {dice_game_id}", "GET", f"api/v1/games/{dice_game_id}/config/logs?limit=20", 200)
        
        dice_log_validation = True
        if success10 and isinstance(dice_logs_response, dict):
            logs = dice_logs_response.get('logs', [])
            if isinstance(logs, list):
                print(f"✅ Found {len(logs)} log entries")
                
                # Look for dice_math_saved actions
                dice_logs = [log for log in logs if log.get('action') == 'dice_math_saved']
                if dice_logs:
                    print(f"✅ Found {len(dice_logs)} dice_math_saved log entries")
                    
                    # Validate log structure
                    latest_log = dice_logs[0]
                    details = latest_log.get('details', {})
                    
                    # Check for required details fields
                    if 'old_value' in details and 'new_value' in details:
                        print("✅ Log details contain old_value and new_value")
                    else:
                        print("❌ Log details missing required fields")
                        dice_log_validation = False
                else:
                    print("❌ No dice_math_saved log entries found")
                    dice_log_validation = False
            else:
                print("❌ Logs response does not contain logs array")
                dice_log_validation = False
        else:
            print("❌ Failed to get config logs")
            dice_log_validation = False
        
        # SUMMARY
        print(f"\n📊 CRASH & DICE MATH ENDPOINTS SUMMARY:")
        print(f"   🚀 Crash Default GET: {'✅ PASS' if success1 and crash_default_validation else '❌ FAIL'}")
        print(f"   🚫 Crash Non-Compatible GET: {'✅ PASS' if success2 else '❌ FAIL'}")
        print(f"   ✅ Crash Valid POST: {'✅ PASS' if success3 and crash_post_validation else '❌ FAIL'}")
        print(f"   ❌ Crash Validation Errors: {'✅ PASS' if crash_validation_passed else '❌ FAIL'}")
        print(f"   📋 Crash Log Verification: {'✅ PASS' if success5 and crash_log_validation else '❌ FAIL'}")
        print(f"   🎲 Dice Default GET: {'✅ PASS' if success6 and dice_default_validation else '❌ FAIL'}")
        print(f"   🚫 Dice Non-Compatible GET: {'✅ PASS' if success7 else '❌ FAIL'}")
        print(f"   ✅ Dice Valid POST: {'✅ PASS' if success8 and dice_post_validation else '❌ FAIL'}")
        print(f"   ❌ Dice Validation Errors: {'✅ PASS' if dice_validation_passed else '❌ FAIL'}")
        print(f"   📋 Dice Log Verification: {'✅ PASS' if success10 and dice_log_validation else '❌ FAIL'}")
        
        return all([
            success1 and crash_default_validation,
            success2,
            success3 and crash_post_validation,
            crash_validation_passed,
            success5 and crash_log_validation,
            success6 and dice_default_validation,
            success7,
            success8 and dice_post_validation,
            dice_validation_passed,
            success10 and dice_log_validation
        ])