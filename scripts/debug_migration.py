import sys
import os
import subprocess
import time

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

def main():
    print(f"{GREEN}=== MIGRATION DEBUGGING SCRIPT ==={RESET}")
    
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend'))
    os.chdir(backend_dir)
    
    # Check if we can import env.py logic
    try:
        sys.path.append(backend_dir)
        from alembic.env import _get_sync_url
        from config import settings
        
        print(f"Current DATABASE_URL settings: {settings.database_url}")
        computed_url = _get_sync_url(settings.database_url)
        print(f"Computed Migration URL: {computed_url}")
        
    except ImportError as e:
        print(f"{RED}[WARN] Could not import app modules: {e}{RESET}")

    # Check env vars
    print(f"ENV: DATABASE_URL={os.environ.get('DATABASE_URL')}")
    print(f"ENV: DATABASE_URL_SYNC={os.environ.get('DATABASE_URL_SYNC')}")

    # Try alembic upgrade head with verbose output
    print(f"-> Running 'alembic upgrade head'...")
    try:
        result = subprocess.run(
            ["alembic", "upgrade", "head"], 
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            print(f"{GREEN}[PASS] Upgrade Successful.{RESET}")
            print(result.stdout)
        else:
            print(f"{RED}[FAIL] Upgrade Failed.{RESET}")
            print("--- STDOUT ---")
            print(result.stdout)
            print("--- STDERR ---")
            print(result.stderr)
            
    except FileNotFoundError:
        print(f"{RED}[ERROR] Alembic command not found.{RESET}")

if __name__ == "__main__":
    main()
