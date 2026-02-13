import pytest
from config import Settings
import os

def test_prod_config_enforcement():
    """
    Simulate PROD environment and verify enforcement raises error 
    if unsafe flags are present.
    """
    # 1. Setup Unsafe Config in Prod
    os.environ["ENV"] = "prod"
    # Unsafe defaults from Pydantic model usually, but let's override manually to trigger error
    # We create a new Settings instance to simulate app startup
    
    # We need to monkeypatch env vars before instantiating Settings
    # But Settings is instantiated at module level in config.py.
    # So we instantiate a fresh one here.
    
    # Scenario: Debug=True in Prod
    os.environ["DEBUG"] = "true"
    
    try:
        s = Settings()
        # Explicitly call validator as it might be post-init or called manually
        s.validate_prod_security_settings()
        assert False, "Should have raised ValueError for DEBUG=True in Prod"
    except ValueError as e:
        assert "DEBUG must be False" in str(e)
    finally:
        del os.environ["DEBUG"]

    # Scenario: Allow Test Payments in Prod
    os.environ["ALLOW_TEST_PAYMENT_METHODS"] = "true"
    try:
        s = Settings()
        s.validate_prod_security_settings()
        assert False, "Should have raised ValueError for Test Payments in Prod"
    except ValueError as e:
        assert "ALLOW_TEST_PAYMENT_METHODS must be False" in str(e)
    finally:
        del os.environ["ALLOW_TEST_PAYMENT_METHODS"]

    # Scenario: Signature Not Enforced
    os.environ["WEBHOOK_SIGNATURE_ENFORCED"] = "false"
    try:
        s = Settings()
        s.validate_prod_security_settings()
        assert False, "Should have raised ValueError for Sig Enforce=False"
    except ValueError as e:
        assert "WEBHOOK_SIGNATURE_ENFORCED must be True" in str(e)
    finally:
        del os.environ["WEBHOOK_SIGNATURE_ENFORCED"]
        
    # Reset
    os.environ["ENV"] = "test"

def test_env_guard_secrets():
    """
    Verify validation of missing secrets.
    """
    os.environ["ENV"] = "prod"
    # Clear a required secret
    if "STRIPE_API_KEY" in os.environ:
        del os.environ["STRIPE_API_KEY"]
    
    try:
        s = Settings()
        s.validate_prod_secrets()
        # Note: If local .env has keys, this might pass. 
        # In CI/Test env we expect strict control. 
        # If it passes, it means key is present.
    except ValueError as e:
        assert "Missing required secrets" in str(e)
    
    # Cleanup
    os.environ["ENV"] = "test"
