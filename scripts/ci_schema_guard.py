import sys
import os
import subprocess

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

def main():
    print(f"{GREEN}=== T15-002: SCHEMA DRIFT GATE ==={RESET}")
    
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend'))
    os.chdir(backend_dir)
    
    print("-> Running 'alembic check'...")
    try:
        # Alembic 1.9+ supports 'check' command which detects if autogenerate would produce anything
        result = subprocess.run(
            ["alembic", "check"], 
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            print(f"{GREEN}[PASS] No schema drift detected.{RESET}")
            sys.exit(0)
        else:
            print(f"{RED}[FAIL] Schema drift detected! Models don't match migrations.{RESET}")
            print("Alembic Output:")
            print(result.stdout)
            print(result.stderr)
            sys.exit(1)
            
    except FileNotFoundError:
        print(f"{RED}[ERROR] Alembic command not found.{RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()
