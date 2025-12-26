import os
import sys
from pydantic import ValidationError

# Add backend to path to import config
sys.path.append("/app/backend")

def verify_prod_env():
    print("=== Go-Live Cutover: Production Environment Verification ===\n")
    
    # Force Env to Prod for the Dry Run Logic
    # Note: This affects defaults in Settings
    os.environ["ENV"] = "prod"
    
    try:
        from config import settings
        print(f"[*] ENV (Effective): {settings.env}")

        # 2. Check Database URL
        print(f"[*] Checking DATABASE_URL...")
        db_url = settings.database_url
        if "sqlite" in db_url:
            print("    [WARN] Using SQLite in PROD simulation. (Expected for this dry-run container)")
        elif not db_url:
            print("    [FAIL] DATABASE_URL is missing!")
        else:
            print(f"    [PASS] Database URL configured: {db_url}")

        # 3. Check Critical Secrets
        print("\n[*] Verifying Critical Secrets (from Loaded Settings)...")
        # In this container, we are using the .env file which might have dev keys.
        # The script should check if *any* key is present, and warn if it's a test key in prod mode.
        
        checks = [
            ("stripe_api_key", "sk_live_"),
            ("stripe_webhook_secret", "whsec_"),
            ("adyen_api_key", None),
            ("adyen_hmac_key", None)
        ]
        
        for attr, prefix in checks:
            val = getattr(settings, attr)
            if not val:
                print(f"    [FAIL] {attr.upper()} is MISSING in Settings.")
            elif prefix and not str(val).startswith(prefix):
                print(f"    [WARN] {attr.upper()} present but looks like Test Key (does not start with '{prefix}').")
                print(f"           Current Value: {str(val)[:10]}...")
            else:
                print(f"    [PASS] {attr.upper()} configured.")

        # 4. Network
        print("\n[*] Checking Network Security Config...")
        origins = settings.get_cors_origins()
        if not origins:
             print("    [WARN] CORS Origins empty (Fail-Closed in Prod).")
        elif "*" in origins:
             print(f"    [WARN] CORS is Wildcard '*' in Prod Mode: {origins}")
        else:
             print(f"    [PASS] CORS Restricted: {origins}")

    except Exception as e:
        print(f"[FAIL] Config Load Failed: {e}")

    print("\n=== Verification Complete ===")
    print(f"Responsible: {os.environ.get('USER', 'admin')}")
    from datetime import datetime
    print(f"Timestamp: {datetime.utcnow().isoformat()} UTC")

if __name__ == "__main__":
    verify_prod_env()
