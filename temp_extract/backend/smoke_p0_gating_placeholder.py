from unittest.mock import patch
from httpx import AsyncClient, ASGITransport
from server import app

# Helper to run async test
async def run_gating_check():
    # P0-1: Mock Payout Gating Check in PROD
    # Should return 403
    
    print("=== P0-1: Prod Gating Smoke Check ===")
    
    # We simulate a "mock payout retry" call in PROD env
    # Note: We patch settings to force PROD behavior for this script run
    
    with patch("config.settings.env", "prod"):
        with patch("config.settings.allow_test_payment_methods", False):
            # Patch secrets so app doesn't crash on validation during this synthetic test
            with patch("config.settings.stripe_api_key", "sk_test_fake"), \
                 patch("config.settings.stripe_webhook_secret", "whsec_fake"), \
                 patch("config.settings.adyen_api_key", "fake"), \
                 patch("config.settings.adyen_merchant_account", "fake"), \
                 patch("config.settings.adyen_hmac_key", "fake"):
                 
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    # 1. Test Mock Payout Retry -> 403
                    # We need a fake token (admin)
                    # We assume middleware lets us pass with a fake token if we mock auth, 
                    # but simpler is to expect 401 if we don't mock auth, 
                    # OR we mock the endpoint logic itself.
                    # Actually, the GATING logic is inside the route.
                    # Let's try to hit it. We need a token.
                    
                    # Create a dummy token? Or mock the dep.
                    # Hard to mock dep in script without overriding app.dependency_overrides
                    
                    # Let's verify via unittest instead? 
                    # The user asked for "smoke output". 
                    # Use existing `verify_prod_gating.py` approach.
                    pass

if __name__ == "__main__":
    print("Use 'verify_prod_gating.py' for the smoke check.")
