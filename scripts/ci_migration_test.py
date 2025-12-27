import sys
import os
import subprocess
import uuid

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

def main():
    print(f"{GREEN}=== T15-001: MIGRATION TEST GATE (Temp DB) ==={RESET}")
    
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend'))
    os.chdir(backend_dir)
    
    # Use a temp sqlite db
    temp_db_name = f"test_mig_{uuid.uuid4().hex}.db"
    # P1 Fix: Must be async for app.core.database to import safely, Alembic will syncify it
    temp_db_url = f"sqlite+aiosqlite:///{temp_db_name}"
    
    # Override environment
    env = os.environ.copy()
    env["DATABASE_URL"] = temp_db_url
    
    print(f"-> Testing Upgrade Head on {temp_db_name}...")
    try:
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            env=env,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"{GREEN}[PASS] Alembic Upgrade Head successful on fresh DB.{RESET}")
        else:
            print(f"{RED}[FAIL] Alembic Upgrade Head FAILED.{RESET}")
            print(result.stdout)
            print(result.stderr)
            # Cleanup
            if os.path.exists(temp_db_name):
                os.remove(temp_db_name)
            sys.exit(1)
            
    except Exception as e:
        print(f"{RED}[ERROR] Execution failed: {e}{RESET}")
        sys.exit(1)
        
    # Cleanup
    if os.path.exists(temp_db_name):
        os.remove(temp_db_name)
        print("-> Temp DB cleaned up.")
    
    sys.exit(0)

if __name__ == "__main__":
    main()
