import pytest
from unittest.mock import patch
from config import Settings

def test_prod_config_validation_success():
    """Test that validation passes when all secrets are present."""
    with patch.dict("os.environ", {
        "ENV": "prod",
        "STRIPE_API_KEY": "sk_live_123",  # must contain 'live'
        "STRIPE_WEBHOOK_SECRET": "whsec_123",
        "ADYEN_API_KEY": "adyen_key",
        "ADYEN_MERCHANT_ACCOUNT": "merchant",
        "ADYEN_HMAC_KEY": "hmac",
        "KYC_MOCK_ENABLED": "false",
        "AUDIT_EXPORT_SECRET": "strong_secret_not_default",
    }):
        s = Settings()
        s.validate_prod_secrets()  # Should not raise

def test_prod_config_validation_fail_stripe():
    """Test failure when Stripe keys are missing in prod."""
    with patch.dict("os.environ", {
        "ENV": "prod",
        "ADYEN_API_KEY": "adyen_key",
        "ADYEN_MERCHANT_ACCOUNT": "merchant",
        "ADYEN_HMAC_KEY": "hmac",
        "KYC_MOCK_ENABLED": "false",
        "AUDIT_EXPORT_SECRET": "strong_secret_not_default",
        # Missing Stripe
    }):
        s = Settings()
        with pytest.raises(ValueError) as exc:
            s.validate_prod_secrets()
        # STRIPE_API_KEY is None, STRIPE_WEBHOOK_SECRET is None
        # Our config check accumulates errors.
        # Check that AT LEAST one of them is mentioned.
        err = str(exc.value)
        assert "STRIPE_API_KEY" in err or "STRIPE_WEBHOOK_SECRET" in err

def test_prod_config_validation_fail_adyen():
    """Test failure when Adyen keys are missing in prod."""
    with patch.dict("os.environ", {
        "ENV": "prod",
        "STRIPE_API_KEY": "sk_live_test",
        "STRIPE_WEBHOOK_SECRET": "whsec_test",
        "KYC_MOCK_ENABLED": "false",
        "AUDIT_EXPORT_SECRET": "strong_secret_not_default",
    }):
        s = Settings()
        with pytest.raises(ValueError) as exc:
            s.validate_prod_secrets()
        assert "ADYEN_API_KEY" in str(exc.value)

def test_dev_config_validation_skip():
    """Test that dev environment skips strict validation."""
    with patch.dict("os.environ", {"ENV": "dev"}):
        s = Settings()
        s.validate_prod_secrets() # Should pass even with empty keys
