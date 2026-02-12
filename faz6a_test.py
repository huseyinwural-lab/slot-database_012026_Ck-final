#!/usr/bin/env python3
"""
Faz 6A Sprint 1 (Provider Integration) Test Suite

This test suite validates:
1. PragmaticAdapter implementation in backend/app/services/providers/adapters.py
2. GamesCallbackRouter updated in backend/app/routes/games_callback.py  
3. Metrics added in backend/app/core/metrics.py
4. pytest backend/tests/providers/test_pragmatic_adapter.py passes

Tests are designed to run against the backend service components.
"""

import sys
import os
import subprocess
import asyncio

# Add backend to path for imports
sys.path.append('/app/backend')

class Faz6ASprintTestSuite:
    def __init__(self):
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
    
    def test_pragmatic_adapter_implementation(self) -> bool:
        """Test 1: Verify PragmaticAdapter implementation exists and works"""
        try:
            from app.services.providers.adapters import PragmaticAdapter
            from app.services.providers.registry import ProviderRegistry
            
            # Test adapter instantiation
            adapter = PragmaticAdapter()
            
            # Test signature validation (should return True in dev mode)
            sig_result = adapter.validate_signature({"hash": "test"}, {})
            if sig_result is not True:
                self.log_result("PragmaticAdapter Implementation", False, 
                              f"Signature validation failed: expected True, got {sig_result}")
                return False
            
            # Test request mapping
            test_payload = {
                "action": "bet",
                "userId": "test_user",
                "gameId": "test_game",
                "roundId": "test_round",
                "reference": "test_tx",
                "amount": 10.0,
                "currency": "USD"
            }
            
            mapped = adapter.map_request(test_payload)
            expected_fields = ["action", "player_id", "game_id", "round_id", "tx_id", "amount", "currency"]
            
            for field in expected_fields:
                if field not in mapped:
                    self.log_result("PragmaticAdapter Implementation", False, 
                                  f"Missing field in mapped request: {field}")
                    return False
            
            # Verify correct mapping
            if mapped["action"] != "bet" or mapped["player_id"] != "test_user" or mapped["amount"] != 10.0:
                self.log_result("PragmaticAdapter Implementation", False, 
                              f"Incorrect mapping: {mapped}")
                return False
            
            # Test response mapping
            engine_response = {"tx_id": "test_tx", "balance": 100.0, "currency": "USD"}
            response = adapter.map_response(engine_response)
            
            if response.get("error") != 0 or response.get("transactionId") != "test_tx":
                self.log_result("PragmaticAdapter Implementation", False, 
                              f"Response mapping failed: {response}")
                return False
            
            # Test error mapping
            error_response = adapter.map_error("INSUFFICIENT_FUNDS", "No money")
            if error_response.get("error") != 1 or error_response.get("description") != "No money":
                self.log_result("PragmaticAdapter Implementation", False, 
                              f"Error mapping failed: {error_response}")
                return False
            
            # Test registry integration
            registry_adapter = ProviderRegistry.get_adapter("pragmatic")
            if not isinstance(registry_adapter, PragmaticAdapter):
                self.log_result("PragmaticAdapter Implementation", False, 
                              f"Registry integration failed: expected PragmaticAdapter, got {type(registry_adapter)}")
                return False
            
            self.log_result("PragmaticAdapter Implementation", True, 
                          "All adapter methods working correctly and registered in provider registry")
            return True
            
        except Exception as e:
            self.log_result("PragmaticAdapter Implementation", False, f"Exception: {str(e)}")
            return False
    
    def test_games_callback_router_updated(self) -> bool:
        """Test 2: Verify GamesCallbackRouter has been updated with metrics and proper imports"""
        try:
            # Check that the router file exists and has the required imports
            router_file = "/app/backend/app/routes/games_callback.py"
            if not os.path.exists(router_file):
                self.log_result("GamesCallbackRouter Updated", False, "games_callback.py file not found")
                return False
            
            with open(router_file, 'r') as f:
                content = f.read()
            
            # Check for required imports
            required_imports = [
                "from app.core.metrics import metrics",
                "from app.services.providers.registry import ProviderRegistry"
            ]
            
            for import_line in required_imports:
                if import_line not in content:
                    self.log_result("GamesCallbackRouter Updated", False, 
                                  f"Missing required import: {import_line}")
                    return False
            
            # Check for metrics usage
            metrics_usage = [
                "metrics.provider_requests_total",
                "metrics.provider_signature_failures"
            ]
            
            for metric in metrics_usage:
                if metric not in content:
                    self.log_result("GamesCallbackRouter Updated", False, 
                                  f"Missing metrics usage: {metric}")
                    return False
            
            # Check for provider callback endpoint
            if "@router.post(\"/{provider}\")" not in content:
                self.log_result("GamesCallbackRouter Updated", False, 
                              "Missing provider callback endpoint")
                return False
            
            # Check for adapter usage
            if "ProviderRegistry.get_adapter(provider)" not in content:
                self.log_result("GamesCallbackRouter Updated", False, 
                              "Missing ProviderRegistry.get_adapter usage")
                return False
            
            self.log_result("GamesCallbackRouter Updated", True, 
                          "Games callback router has all required imports, metrics, and provider integration")
            return True
            
        except Exception as e:
            self.log_result("GamesCallbackRouter Updated", False, f"Exception: {str(e)}")
            return False
    
    def test_metrics_implementation(self) -> bool:
        """Test 3: Verify Metrics have been added to core/metrics.py"""
        try:
            from app.core.metrics import metrics
            
            # Check that provider-specific metrics exist
            required_metrics = [
                "provider_requests_total",
                "provider_signature_failures"
            ]
            
            for metric_name in required_metrics:
                if not hasattr(metrics, metric_name):
                    self.log_result("Metrics Implementation", False, 
                                  f"Missing required metric: {metric_name}")
                    return False
            
            # Test that metrics can be incremented (basic functionality test)
            try:
                metrics.provider_requests_total.labels(provider="test", method="test", status="test").inc()
                metrics.provider_signature_failures.labels(provider="test").inc()
            except Exception as e:
                self.log_result("Metrics Implementation", False, 
                              f"Failed to increment metrics: {str(e)}")
                return False
            
            # Check that game-related metrics also exist
            game_metrics = [
                "bets_total",
                "wins_total", 
                "rollbacks_total",
                "bet_amount",
                "win_amount"
            ]
            
            for metric_name in game_metrics:
                if not hasattr(metrics, metric_name):
                    self.log_result("Metrics Implementation", False, 
                                  f"Missing game metric: {metric_name}")
                    return False
            
            self.log_result("Metrics Implementation", True, 
                          "All required provider and game metrics are implemented and functional")
            return True
            
        except Exception as e:
            self.log_result("Metrics Implementation", False, f"Exception: {str(e)}")
            return False
    
    def test_pytest_pragmatic_adapter(self) -> bool:
        """Test 4: Run pytest on pragmatic adapter tests"""
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "tests/providers/test_pragmatic_adapter.py", "-v"],
                cwd="/app/backend",
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                self.log_result("Pytest Pragmatic Adapter", False, 
                              f"Pytest failed with return code {result.returncode}. STDOUT: {result.stdout}, STDERR: {result.stderr}")
                return False
            
            # Check that all tests passed
            if "FAILED" in result.stdout:
                self.log_result("Pytest Pragmatic Adapter", False, 
                              f"Some tests failed: {result.stdout}")
                return False
            
            # Count passed tests
            import re
            passed_match = re.search(r'(\d+) passed', result.stdout)
            if passed_match:
                passed_count = int(passed_match.group(1))
                if passed_count < 4:  # We expect at least 4 tests
                    self.log_result("Pytest Pragmatic Adapter", False, 
                                  f"Expected at least 4 tests to pass, got {passed_count}")
                    return False
            
            self.log_result("Pytest Pragmatic Adapter", True, 
                          f"All pragmatic adapter tests passed successfully. {passed_count} tests passed.")
            return True
            
        except Exception as e:
            self.log_result("Pytest Pragmatic Adapter", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run the complete Faz 6A Sprint 1 test suite"""
        print("🚀 Starting Faz 6A Sprint 1 (Provider Integration) Test Suite...")
        print("=" * 80)
        
        # Run all tests
        test_results = []
        
        # Test 1: PragmaticAdapter implementation
        test_results.append(self.test_pragmatic_adapter_implementation())
        
        # Test 2: GamesCallbackRouter updated
        test_results.append(self.test_games_callback_router_updated())
        
        # Test 3: Metrics implementation
        test_results.append(self.test_metrics_implementation())
        
        # Test 4: Pytest pragmatic adapter
        test_results.append(self.test_pytest_pragmatic_adapter())
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 FAZ 6A SPRINT 1 TEST SUMMARY")
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
            print("🎉 All Faz 6A Sprint 1 tests PASSED!")
            return True
        else:
            print(f"⚠️  {total - passed} test(s) failed. Review the details above.")
            return False

def main():
    """Main test runner"""
    suite = Faz6ASprintTestSuite()
    success = suite.run_all_tests()
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)